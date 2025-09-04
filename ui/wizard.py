# ui/wizard.py - Enhanced version with better UX and state management
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List

# Import our enhanced components
from ui.components import LabeledEntry, FilePicker
from services.llm_providers import DeepSeekClient, SonnetClient, create_test_clients
from services.document_processor import DocumentProcessor
from services.token_manager import TokenManager, ChainedPromptGenerator
from validation.schemas import BudgetResult  # kept for compatibility, no longer used directly


class StateManager:
    """Centralized state management with validation and persistence"""
    def __init__(self):
        self._state = {
            "project": {},
            "tor_path": None,
            "tor_content": None,
            "tor_chunks": {},
            "models": {
                "narrative": "DeepSeek",
                "budget": "Sonnet",
                "temperature": 0.2,
                "max_tokens": 4000,
                "language": "es"
            },
            "templates": {"docx": None, "xlsx": None},
            "results": {"narrative": None, "budget": None, "output_paths": {}},
            "api_status": {"deepseek": False, "sonnet": False},
            "processing": {"active": False, "current_step": None, "progress": 0}
        }
        self._load_state()

    def get(self, key: str, default=None):
        """Get state value with dot notation support"""
        keys = key.split('.')
        value = self._state
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set state value with dot notation support"""
        keys = key.split('.')
        target = self._state
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        self._save_state()

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple state values"""
        for key, value in updates.items():
            self.set(key, value)

    def validate_project(self) -> tuple[bool, List[str]]:
        """Validate project data"""
        errors = []
        project = self.get("project", {})

        required_fields = [
            ("title", "Título del proyecto"),
            ("country", "País"),
            ("donor", "Donante/Financiador"),
            ("duration_months", "Duración")
        ]

        for field, label in required_fields:
            if not project.get(field, "").strip():
                errors.append(f"• {label} es requerido")

        # Validate duration is numeric
        duration = project.get("duration_months", "")
        if duration and not str(duration).strip().isdigit():
            errors.append("• Duración debe ser un número de meses")

        return len(errors) == 0, errors

    def validate_tor(self) -> tuple[bool, List[str]]:
        """Validate ToR data"""
        errors = []

        if not self.get("tor_path"):
            errors.append("• Falta seleccionar archivo de ToR")

        if not self.get("tor_content"):
            errors.append("• Falta procesar el contenido del ToR")

        if not self.get("tor_chunks"):
            errors.append("• Falta análisis del documento ToR")

        return len(errors) == 0, errors

    def validate_apis(self) -> tuple[bool, List[str]]:
        """Validate API configuration"""
        errors = []

        if not self.get("api_status.deepseek"):
            errors.append("• API de DeepSeek no configurada correctamente")

        if not self.get("api_status.sonnet"):
            errors.append("• API de Sonnet no configurada correctamente")

        return len(errors) == 0, errors

    def _save_state(self) -> None:
        """Save state to file"""
        try:
            state_dir = Path("runs/state")
            state_dir.mkdir(parents=True, exist_ok=True)

            # Don't save sensitive/huge data
            safe_state = dict(self._state)
            safe_state.pop("tor_content", None)

            with open(state_dir / "wizard_state.json", 'w', encoding='utf-8') as f:
                json.dump(safe_state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Fail silently for state saving

    def _load_state(self) -> None:
        """Load state from file"""
        try:
            state_file = Path("runs/state/wizard_state.json")
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    saved_state = json.load(f)

                # Merge with current state
                for key, value in saved_state.items():
                    if key in self._state and isinstance(self._state[key], dict) and isinstance(value, dict):
                        self._state[key].update(value)
                    else:
                        self._state[key] = value
        except Exception:
            pass  # Fail silently for state loading


class ProgressManager:
    """Manages progress tracking and UI updates"""
    def __init__(self, progress_callback: Callable[[int, str], None]):
        self.progress_callback = progress_callback
        self.steps = []
        self.current_step = 0

    def set_steps(self, steps: List[str]) -> None:
        self.steps = steps
        self.current_step = 0

    def update(self, step_text: str, progress: int = None) -> None:
        if progress is None:
            progress = int((self.current_step / len(self.steps)) * 100) if self.steps else 0
        self.progress_callback(progress, step_text)

    def next_step(self, step_text: str = None) -> None:
        self.current_step += 1
        if step_text is None and self.current_step <= len(self.steps):
            step_text = self.steps[self.current_step - 1]
        progress = int((self.current_step / len(self.steps)) * 100) if self.steps else 0
        self.progress_callback(progress, step_text or f"Paso {self.current_step}")


class ProposalWizard(ttk.Frame):
    """Enhanced wizard with better state management and error handling"""
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)

        # Initialize managers
        self.state = StateManager()
        self.progress_manager = ProgressManager(self._update_progress_ui)

        # UI components
        self._processing = False
        self._current_thread = None

        self._setup_ui()
        self._setup_event_handlers()

        # Initial API status check
        self.master.after(1000, self._check_api_status_async)

    def _setup_ui(self):
        """Setup the UI components"""
        style = ttk.Style()
        style.configure('Enhanced.TNotebook', tabposition='n')

        self.notebook = ttk.Notebook(self, style='Enhanced.TNotebook')
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self.tabs = {}
        tab_configs = [
            ("project", "🏗️ Proyecto", self._build_project_tab),
            ("tor", "📋 Términos de Referencia", self._build_tor_tab),
            ("config", "⚙️ Configuración", self._build_config_tab),
            ("generate", "🚀 Generación", self._build_generate_tab),
            ("results", "📊 Resultados", self._build_results_tab)
        ]

        for tab_id, tab_name, build_func in tab_configs:
            frame = ttk.Frame(self.notebook, padding=15)
            self.tabs[tab_id] = frame
            self.notebook.add(frame, text=tab_name)
            build_func(frame)

    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.master.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _build_project_tab(self, parent):
        """Build enhanced project information tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Status indicator
        status_frame = ttk.Frame(scrollable_frame)
        status_frame.pack(fill="x", pady=(0, 10))

        self.project_status_label = ttk.Label(
            status_frame,
            text="📝 Complete la información del proyecto",
            font=('TkDefaultFont', 10, 'bold')
        )
        self.project_status_label.pack(anchor="w")

        # Basic project information
        basic_frame = ttk.LabelFrame(scrollable_frame, text="Información General", padding=10)
        basic_frame.pack(fill="x", pady=5)

        # Initialize variables
        self.project_vars = {
            'title': tk.StringVar(),
            'country': tk.StringVar(value="Guatemala"),
            'language': tk.StringVar(value="es"),
            'donor': tk.StringVar(),
            'duration_months': tk.StringVar(),
            'budget_cap': tk.StringVar()
        }

        # Load saved values
        project_data = self.state.get("project", {})
        for key, var in self.project_vars.items():
            if key in project_data:
                var.set(project_data[key])

        # Create form fields with validation
        LabeledEntry(basic_frame, "Título del proyecto *", self.project_vars['title']).pack(fill="x", pady=3)

        # Country and language row
        country_row = ttk.Frame(basic_frame)
        country_row.pack(fill="x", pady=3)

        country_frame = ttk.Frame(country_row)
        country_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Label(country_frame, text="País *").pack(anchor="w")
        country_combo = ttk.Combobox(
            country_frame,
            textvariable=self.project_vars['country'],
            values=["Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panamá"]
        )
        country_combo.pack(fill="x")

        lang_frame = ttk.Frame(country_row)
        lang_frame.pack(side="right")
        ttk.Label(lang_frame, text="Idioma").pack(anchor="w")
        ttk.Combobox(
            lang_frame,
            textvariable=self.project_vars['language'],
            values=["es", "en"],
            state="readonly",
            width=8
        ).pack()

        LabeledEntry(basic_frame, "Donante/Financiador *", self.project_vars['donor']).pack(fill="x", pady=3)

        # Duration and budget row
        duration_row = ttk.Frame(basic_frame)
        duration_row.pack(fill="x", pady=3)

        duration_frame = ttk.Frame(duration_row)
        duration_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Label(duration_frame, text="Duración (meses) *").pack(anchor="w")
        duration_entry = ttk.Entry(duration_frame, textvariable=self.project_vars['duration_months'])
        duration_entry.pack(fill="x")

        budget_frame = ttk.Frame(duration_row)
        budget_frame.pack(side="right", fill="x", expand=True)
        ttk.Label(budget_frame, text="Presupuesto máximo").pack(anchor="w")
        budget_entry = ttk.Entry(budget_frame, textvariable=self.project_vars['budget_cap'])
        budget_entry.pack(fill="x")

        # Location information
        location_frame = ttk.LabelFrame(scrollable_frame, text="Ubicación", padding=10)
        location_frame.pack(fill="x", pady=5)

        # Additional location variables
        self.location_vars = {
            'department': tk.StringVar(),
            'municipality': tk.StringVar(),
            'community': tk.StringVar(),
            'coverage_type': tk.StringVar(value="Local")
        }

        # Load location data
        for key, var in self.location_vars.items():
            if key in project_data:
                var.set(project_data[key])

        # Coverage type
        ttk.Label(location_frame, text="Cobertura").pack(anchor="w")
        ttk.Combobox(
            location_frame,
            textvariable=self.location_vars['coverage_type'],
            values=["Local", "Municipal", "Departamental", "Regional", "Nacional"],
            state="readonly"
        ).pack(fill="x", pady=(0, 5))

        # Department and municipality
        dept_muni_row = ttk.Frame(location_frame)
        dept_muni_row.pack(fill="x", pady=3)

        dept_frame = ttk.Frame(dept_muni_row)
        dept_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Label(dept_frame, text="Departamento").pack(anchor="w")
        ttk.Combobox(
            dept_frame,
            textvariable=self.location_vars['department'],
            values=[
                "Alta Verapaz", "Baja Verapaz", "Chimaltenango", "Chiquimula",
                "El Progreso", "Escuintla", "Guatemala", "Huehuetenango",
                "Izabal", "Jalapa", "Jutiapa", "Petén", "Quetzaltenango",
                "Quiché", "Retalhuleu", "Sacatepéquez", "San Marcos",
                "Santa Rosa", "Sololá", "Suchitepéquez", "Totonicapán", "Zacapa"
            ]
        ).pack(fill="x")

        muni_frame = ttk.Frame(dept_muni_row)
        muni_frame.pack(side="right", fill="x", expand=True)
        LabeledEntry(muni_frame, "Municipio", self.location_vars['municipality']).pack(fill="x")

        LabeledEntry(location_frame, "Comunidad (opcional)", self.location_vars['community']).pack(fill="x", pady=3)

        # Target population
        population_frame = ttk.LabelFrame(scrollable_frame, text="Población Objetivo", padding=10)
        population_frame.pack(fill="x", pady=5)

        self.population_vars = {
            'beneficiaries_direct': tk.StringVar(),
            'beneficiaries_indirect': tk.StringVar(),
            'demographic_focus': tk.StringVar()
        }

        # Load population data
        for key, var in self.population_vars.items():
            if key in project_data:
                var.set(project_data[key])

        # Target population description
        ttk.Label(population_frame, text="Descripción de población objetivo").pack(anchor="w")
        self.target_population_text = tk.Text(population_frame, height=3, wrap="word")
        self.target_population_text.pack(fill="x", pady=(2, 5))

        # Load target population text
        if 'target_population' in project_data:
            self.target_population_text.insert("1.0", project_data['target_population'])

        # Beneficiaries
        beneficiaries_row = ttk.Frame(population_frame)
        beneficiaries_row.pack(fill="x", pady=3)

        LabeledEntry(
            beneficiaries_row,
            "Beneficiarios directos",
            self.population_vars['beneficiaries_direct']
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        LabeledEntry(
            beneficiaries_row,
            "Beneficiarios indirectos",
            self.population_vars['beneficiaries_indirect']
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Demographic focus
        ttk.Label(population_frame, text="Enfoque demográfico").pack(anchor="w", pady=(5, 0))
        ttk.Combobox(
            population_frame,
            textvariable=self.population_vars['demographic_focus'],
            values=[
                "Población general", "Mujeres", "Jóvenes", "Pueblos indígenas",
                "Personas con discapacidad", "Adultos mayores",
                "Familias rurales", "Microempresarios", "Líderes comunitarios"
            ]
        ).pack(fill="x", pady=(2, 5))

        # IEPADES profile
        org_frame = ttk.LabelFrame(scrollable_frame, text="Perfil Organizacional - IEPADES", padding=10)
        org_frame.pack(fill="both", expand=True, pady=5)

        # Pre-filled IEPADES profile
        iepades_profile = """El Instituto de Enseñanza para el Desarrollo Sostenible (IEPADES) es una organización no gubernamental fundada hace más de 30 años en Guatemala. Su misión principal ha sido promover la paz, la democracia y el desarrollo sostenible, especialmente en comunidades rurales y vulnerables.

Desde sus inicios, IEPADES ha trabajado para fortalecer el poder local, fomentar la justicia social y apoyar la autogestión comunitaria. A lo largo de su trayectoria, ha desarrollado proyectos enfocados en la construcción de paz, la prevención de la violencia y el fortalecimiento de capacidades locales.

IEPADES ha establecido alianzas estratégicas en Guatemala y otros países de Centroamérica, consolidándose como un referente en temas de desarrollo sostenible y derechos humanos.

Áreas de experticia:
• Construcción de paz y prevención de violencia
• Fortalecimiento de capacidades locales
• Autogestión comunitaria
• Desarrollo sostenible
• Derechos humanos
• Participación ciudadana
• Desarrollo económico local"""

        self.org_profile_text = tk.Text(org_frame, height=10, wrap="word")
        org_scrollbar = ttk.Scrollbar(org_frame, orient="vertical", command=self.org_profile_text.yview)
        self.org_profile_text.configure(yscrollcommand=org_scrollbar.set)

        self.org_profile_text.pack(side="left", fill="both", expand=True)
        org_scrollbar.pack(side="right", fill="y")

        # Load saved profile or use default
        saved_profile = project_data.get('org_profile', iepades_profile)
        self.org_profile_text.insert("1.0", saved_profile)

        # Action buttons
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            buttons_frame,
            text="Validar y Guardar",
            command=self._validate_and_save_project
        ).pack(side="right", padx=(5, 0))

        ttk.Button(
            buttons_frame,
            text="Limpiar formulario",
            command=self._clear_project_form
        ).pack(side="right")

        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _build_tor_tab(self, parent):
        """Build enhanced ToR processing tab"""
        # Status
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(0, 10))

        self.tor_status_label = ttk.Label(
            status_frame,
            text="📄 Seleccione y procese el archivo de Términos de Referencia",
            font=('TkDefaultFont', 10, 'bold')
        )
        self.tor_status_label.pack(anchor="w")

        # File selection
        file_frame = ttk.LabelFrame(parent, text="Selección de Archivo", padding=10)
        file_frame.pack(fill="x", pady=5)

        self.tor_picker = FilePicker(
            file_frame,
            "Archivo de ToR (PDF/DOCX)",
            [("PDF", "*.pdf"), ("Word", "*.docx"), ("Todos los archivos", "*.*")],
            self._on_tor_file_selected
        )
        self.tor_picker.pack(fill="x", pady=5)

        # Processing progress
        progress_frame = ttk.LabelFrame(parent, text="Procesamiento", padding=10)
        progress_frame.pack(fill="x", pady=5)

        self.tor_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.tor_progress_label = ttk.Label(progress_frame, text="Esperando archivo...")
        self.tor_progress_label.pack(pady=(0, 5))

        # Document analysis
        analysis_frame = ttk.LabelFrame(parent, text="Análisis del Documento", padding=10)
        analysis_frame.pack(fill="x", pady=5)

        self.doc_analysis_text = tk.Text(analysis_frame, height=6, wrap="word", state="disabled")
        analysis_scrollbar = ttk.Scrollbar(analysis_frame, orient="vertical", command=self.doc_analysis_text.yview)
        self.doc_analysis_text.configure(yscrollcommand=analysis_scrollbar.set)

        self.doc_analysis_text.pack(side="left", fill="both", expand=True)
        analysis_scrollbar.pack(side="right", fill="y")

        # Document preview
        preview_frame = ttk.LabelFrame(parent, text="Vista Previa del Contenido", padding=10)
        preview_frame.pack(fill="both", expand=True, pady=5)

        self.tor_preview_text = tk.Text(preview_frame, wrap="word", state="disabled")
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tor_preview_text.yview)
        self.tor_preview_text.configure(yscrollcommand=preview_scrollbar.set)

        self.tor_preview_text.pack(side="left", fill="both", expand=True)
        preview_scrollbar.pack(side="right", fill="y")

        # Action buttons
        tor_buttons_frame = ttk.Frame(parent)
        tor_buttons_frame.pack(fill="x", pady=5)

        ttk.Button(
            tor_buttons_frame,
            text="Reprocesar documento",
            command=self._reprocess_tor
        ).pack(side="left")

        ttk.Button(
            tor_buttons_frame,
            text="Limpiar",
            command=self._clear_tor_data
        ).pack(side="right")

    def _build_config_tab(self, parent):
        """Build enhanced configuration tab"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(0, 10))

        self.config_status_label = ttk.Label(
            status_frame,
            text="⚙️ Configure las APIs y parámetros de generación",
            font=('TkDefaultFont', 10, 'bold')
        )
        self.config_status_label.pack(anchor="w")

        # API Status
        api_frame = ttk.LabelFrame(parent, text="Estado de las APIs", padding=10)
        api_frame.pack(fill="x", pady=5)

        self.api_status_labels = {}
        api_info = [
            ("deepseek", "DeepSeek (Narrativa)", "🔮"),
            ("sonnet", "Claude Sonnet (Presupuesto)", "🧠")
        ]

        for api_key, api_name, icon in api_info:
            row = ttk.Frame(api_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=f"{icon} {api_name}:").pack(side="left")

            status_label = ttk.Label(row, text="❓ Verificando...")
            status_label.pack(side="left", padx=(10, 0))
            self.api_status_labels[api_key] = status_label

        ttk.Button(
            api_frame,
            text="🔄 Verificar APIs",
            command=self._check_api_status_async
        ).pack(pady=(10, 0))

        # Model configuration
        model_frame = ttk.LabelFrame(parent, text="Configuración de Modelos", padding=10)
        model_frame.pack(fill="x", pady=5)

        # Model selection variables
        self.model_vars = {
            'narrative_model': tk.StringVar(value="DeepSeek"),
            'budget_model': tk.StringVar(value="Sonnet"),
            'temperature': tk.DoubleVar(value=0.2),
            'max_tokens': tk.IntVar(value=4000)
        }

        # Load saved model config
        model_config = self.state.get("models", {})
        for key, var in self.model_vars.items():
            if key.replace('_', '') in model_config:
                var.set(model_config[key.replace('_', '')])

        # Model selection
        model_row1 = ttk.Frame(model_frame)
        model_row1.pack(fill="x", pady=3)
        ttk.Label(model_row1, text="Modelo para narrativa:").pack(side="left")
        ttk.Combobox(
            model_row1,
            textvariable=self.model_vars['narrative_model'],
            values=["DeepSeek"],
            state="readonly",
            width=15
        ).pack(side="left", padx=(10, 0))

        model_row2 = ttk.Frame(model_frame)
        model_row2.pack(fill="x", pady=3)
        ttk.Label(model_row2, text="Modelo para presupuesto:").pack(side="left")
        ttk.Combobox(
            model_row2,
            textvariable=self.model_vars['budget_model'],
            values=["Sonnet"],
            state="readonly",
            width=15
        ).pack(side="left", padx=(10, 0))

        # Parameters
        param_frame = ttk.Frame(model_frame)
        param_frame.pack(fill="x", pady=(10, 0))

        # Temperature
        temp_row = ttk.Frame(param_frame)
        temp_row.pack(fill="x", pady=3)
        ttk.Label(temp_row, text="Temperature (creatividad):").pack(side="left")
        temp_scale = ttk.Scale(
            temp_row,
            variable=self.model_vars['temperature'],
            from_=0.0,
            to=1.0,
            orient="horizontal",
            length=200
        )
        temp_scale.pack(side="left", padx=(10, 5))

        self.temp_display = ttk.Label(temp_row, text="0.2")
        self.temp_display.pack(side="left")
        temp_scale.configure(command=self._update_temp_display)

        # Max tokens
        tokens_row = ttk.Frame(param_frame)
        tokens_row.pack(fill="x", pady=3)
        ttk.Label(tokens_row, text="Máximo de tokens:").pack(side="left")
        ttk.Entry(
            tokens_row,
            textvariable=self.model_vars['max_tokens'],
            width=10
        ).pack(side="left", padx=(10, 0))

        # Template configuration
        template_frame = ttk.LabelFrame(parent, text="Plantillas de Documentos", padding=10)
        template_frame.pack(fill="x", pady=5)

        self.template_pickers = {}

        # DOCX template
        self.template_pickers['docx'] = FilePicker(
            template_frame,
            "Plantilla DOCX (opcional)",
            [("Word", "*.docx")],
            lambda path: self._on_template_selected('docx', path)
        )
        self.template_pickers['docx'].pack(fill="x", pady=3)

        # XLSX template
        self.template_pickers['xlsx'] = FilePicker(
            template_frame,
            "Plantilla Excel (opcional)",
            [("Excel", "*.xlsx")],
            lambda path: self._on_template_selected('xlsx', path)
        )
        self.template_pickers['xlsx'].pack(fill="x", pady=3)

        # Save button
        ttk.Button(
            parent,
            text="💾 Guardar Configuración",
            command=self._save_configuration
        ).pack(pady=10)

    def _build_generate_tab(self, parent):
        """Build enhanced generation tab"""
        # Status
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(0, 10))

        self.generate_status_label = ttk.Label(
            status_frame,
            text="🚀 Listo para generar la propuesta",
            font=('TkDefaultFont', 10, 'bold')
        )
        self.generate_status_label.pack(anchor="w")

        # Pre-generation validation
        validation_frame = ttk.LabelFrame(parent, text="Validación Pre-Generación", padding=10)
        validation_frame.pack(fill="x", pady=5)

        self.validation_items = {}
        validation_checks = [
            ("project", "📝 Datos del proyecto completos"),
            ("tor", "📄 Documento ToR procesado"),
            ("apis", "🔌 APIs configuradas correctamente")
        ]

        for check_id, check_text in validation_checks:
            row = ttk.Frame(validation_frame)
            row.pack(fill="x", pady=2)

            status_icon = ttk.Label(row, text="❓")
            status_icon.pack(side="left")

            ttk.Label(row, text=check_text).pack(side="left", padx=(5, 0))

            self.validation_items[check_id] = status_icon

        ttk.Button(
            validation_frame,
            text="🔍 Verificar Todo",
            command=self._run_pre_generation_validation
        ).pack(pady=(10, 0))

        # Progress tracking
        progress_frame = ttk.LabelFrame(parent, text="Progreso de Generación", padding=10)
        progress_frame.pack(fill="x", pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="Esperando...")
        self.progress_label.pack()

        # Generation log
        log_frame = ttk.LabelFrame(parent, text="Registro de Generación", padding=10)
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(log_frame, wrap="word", state="disabled")
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")

        # Generation controls
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", pady=5)

        self.generate_button = ttk.Button(
            controls_frame,
            text="🚀 Generar Propuesta Completa",
            command=self._start_generation
        )
        self.generate_button.pack(side="left")

        self.abort_button = ttk.Button(
            controls_frame,
            text="🛑 Abortar",
            command=self._abort_generation,
            state="disabled"
        )
        self.abort_button.pack(side="left", padx=(10, 0))

        ttk.Button(
            controls_frame,
            text="🧹 Limpiar Log",
            command=self._clear_generation_log
        ).pack(side="right")

    def _build_results_tab(self, parent):
        """Build enhanced results tab"""
        # Status
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=(0, 10))

        self.results_status_label = ttk.Label(
            status_frame,
            text="📊 Visualice y acceda a los resultados generados",
            font=('TkDefaultFont', 10, 'bold')
        )
        self.results_status_label.pack(anchor="w")

        # Results summary
        summary_frame = ttk.LabelFrame(parent, text="Resumen de Resultados", padding=10)
        summary_frame.pack(fill="x", pady=5)

        self.results_summary_text = tk.Text(summary_frame, height=4, wrap="word", state="disabled")
        self.results_summary_text.pack(fill="x")

        # Generated files
        files_frame = ttk.LabelFrame(parent, text="Archivos Generados", padding=10)
        files_frame.pack(fill="x", pady=5)

        # Files list with actions
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.pack(fill="x")

        self.files_listbox = tk.Listbox(files_list_frame, height=4)
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient="vertical", command=self.files_listbox.yview)
        self.files_listbox.configure(yscrollcommand=files_scrollbar.set)

        self.files_listbox.pack(side="left", fill="both", expand=True)
        files_scrollbar.pack(side="right", fill="y")

        # Continue to completion
        files_buttons_frame = ttk.Frame(files_frame)
        files_buttons_frame.pack(fill="x", pady=(5, 0))

        ttk.Button(
            files_buttons_frame,
            text="📁 Abrir Carpeta de Resultados",
            command=self._open_results_folder
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            files_buttons_frame,
            text="📝 Abrir Documento de Narrativa",
            command=lambda: self._open_result_file('narrative')
        ).pack(side="left", padx=(5, 0))

        ttk.Button(
            files_buttons_frame,
            text="💰 Abrir Documento de Presupuesto",
            command=lambda: self._open_result_file('budget')
        ).pack(side="left", padx=(5, 0))

    def _on_tab_changed(self, event):
        """Handle tab change events"""
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        if current_tab == "🚀 Generación":
            self._run_pre_generation_validation()

    def _update_progress_ui(self, progress: int, step_text: str):
        """Update progress bar and label safely from any thread"""
        self.master.after(0, self._set_progress_state, progress, step_text)

    def _set_progress_state(self, progress: int, step_text: str):
        """Set progress state in the UI thread"""
        self.progress_bar['value'] = progress
        self.progress_label['text'] = step_text
        self.state.set("processing.current_step", step_text)
        self.state.set("processing.progress", progress)

    def _validate_and_save_project(self):
        """Validate project data and save to state"""
        self._update_state_from_project_ui()
        is_valid, errors = self.state.validate_project()
        if is_valid:
            messagebox.showinfo("Éxito", "Datos del proyecto guardados y validados correctamente.")
            self._update_project_status_ui(True)
        else:
            messagebox.showerror("Error de Validación", "\n".join(errors))
            self._update_project_status_ui(False)

    def _update_state_from_project_ui(self):
        """Update state manager with data from project UI fields"""
        project_data = {}
        for key, var in self.project_vars.items():
            project_data[key] = var.get()
        for key, var in self.location_vars.items():
            project_data[key] = var.get()
        for key, var in self.population_vars.items():
            project_data[key] = var.get()
        project_data['target_population'] = self.target_population_text.get("1.0", tk.END).strip()
        project_data['org_profile'] = self.org_profile_text.get("1.0", tk.END).strip()
        self.state.set("project", project_data)

    def _update_project_status_ui(self, is_valid: bool):
        """Update the status label for the project tab"""
        if is_valid:
            self.project_status_label['text'] = "✅ Datos del proyecto validados y listos"
            self.project_status_label['foreground'] = "green"
        else:
            self.project_status_label['text'] = "❌ Hay errores en los datos del proyecto"
            self.project_status_label['foreground'] = "red"

    def _clear_project_form(self):
        """Clear the project form fields"""
        for var in self.project_vars.values():
            var.set("")
        for var in self.location_vars.values():
            var.set("")
        for var in self.population_vars.values():
            var.set("")
        self.target_population_text.delete("1.0", tk.END)
        # Restore default values
        self.project_vars['country'].set("Guatemala")
        self.project_vars['language'].set("es")
        self.location_vars['coverage_type'].set("Local")
        self.org_profile_text.delete("1.0", tk.END)
        self.org_profile_text.insert("1.0", """El Instituto de Enseñanza para el Desarrollo Sostenible (IEPADES) es una organización no gubernamental fundada hace más de 30 años en Guatemala...""")
        self._update_project_status_ui(False)

    def _on_tor_file_selected(self, file_path):
        """Handle selection of a new ToR file"""
        self.state.set("tor_path", file_path)
        self._start_tor_processing(file_path)

    def _reprocess_tor(self):
        """Reprocess the currently selected ToR file"""
        tor_path = self.state.get("tor_path")
        if tor_path:
            self._start_tor_processing(tor_path)
        else:
            messagebox.showerror("Error", "No hay un archivo de ToR seleccionado para reprocesar.")

    def _start_tor_processing(self, file_path):
        """Start document processing in a separate thread"""
        self._toggle_processing_state(True, "tor")
        self._current_thread = threading.Thread(target=self._process_tor_task, args=(file_path,))
        self._current_thread.start()

    def _process_tor_task(self, file_path):
        """Task to process the ToR document"""
        try:
            self.progress_manager.update("Procesando documento...", 10)
            processor = DocumentProcessor()
            tor_content = processor.extract_text_from_file(file_path)
            self.state.set("tor_content", tor_content)
            self.progress_manager.update("Analizando contenido...", 50)
            tor_chunks = processor.chunk_document(tor_content)
            self.state.set("tor_chunks", tor_chunks)

            # Simulated analysis
            analysis_text = (
                f"Análisis de Documento:\n\n"
                f"Ruta: {file_path}\n"
                f"Tamaño: {len(tor_content) / 1024:.2f} KB\n"
                f"Secciones identificadas: {len(tor_chunks['sections'])}\n"
                f"Párrafos totales: {len(tor_chunks['paragraphs'])}"
            )

            self.master.after(0, self._update_tor_ui, tor_content, analysis_text, True)

        except Exception as e:
            traceback.print_exc()
            self.master.after(0, lambda: messagebox.showerror("Error de Procesamiento", f"Ocurrió un error al procesar el documento: {e}"))
            self.master.after(0, self._toggle_processing_state, False, "tor")

    def _update_tor_ui(self, content, analysis, success):
        """Update ToR tab UI after processing"""
        self.tor_preview_text.config(state="normal")
        self.tor_preview_text.delete("1.0", tk.END)
        self.tor_preview_text.insert("1.0", content[:5000] + "...")  # Show a truncated preview
        self.tor_preview_text.config(state="disabled")

        self.doc_analysis_text.config(state="normal")
        self.doc_analysis_text.delete("1.0", tk.END)
        self.doc_analysis_text.insert("1.0", analysis)
        self.doc_analysis_text.config(state="disabled")

        if success:
            self.tor_status_label['text'] = "✅ Documento ToR procesado correctamente"
            self.tor_status_label['foreground'] = "green"
        else:
            self.tor_status_label['text'] = "❌ Error al procesar el documento ToR"
            self.tor_status_label['foreground'] = "red"

        self._toggle_processing_state(False, "tor")
        self._run_pre_generation_validation()

    def _clear_tor_data(self):
        """Clear all data related to the ToR document"""
        self.state.update({
            "tor_path": None,
            "tor_content": None,
            "tor_chunks": {}
        })
        self.tor_picker.clear()
        self.tor_preview_text.config(state="normal")
        self.tor_preview_text.delete("1.0", tk.END)
        self.tor_preview_text.config(state="disabled")
        self.doc_analysis_text.config(state="normal")
        self.doc_analysis_text.delete("1.0", tk.END)
        self.doc_analysis_text.config(state="disabled")
        self.tor_status_label['text'] = "📄 Seleccione y procese el archivo de Términos de Referencia"
        self.tor_status_label['foreground'] = "black"

    def _on_template_selected(self, template_type, file_path):
        """Handle template file selection"""
        self.state.set(f"templates.{template_type}", file_path)

    def _check_api_status_async(self):
        """Check API status in a separate thread"""
        self.api_status_labels['deepseek']['text'] = "❓ Verificando..."
        self.api_status_labels['deepseek']['foreground'] = "black"
        self.api_status_labels['sonnet']['text'] = "❓ Verificando..."
        self.api_status_labels['sonnet']['foreground'] = "black"

        threading.Thread(target=self._check_api_status_task).start()

    def _check_api_status_task(self):
        """Task to check API status"""
        try:
            print("DEBUG: Checking API status...")
            deepseek_client, sonnet_client = create_test_clients()
            print(f"DEBUG: DeepSeek API key exists: {bool(deepseek_client.api_key)}")
            print(f"DEBUG: Sonnet API key exists: {bool(sonnet_client.api_key)}")
            print(f"DEBUG: Sonnet model: {sonnet_client.model}")

            print("DEBUG: Testing DeepSeek connection...")
            deepseek_status = deepseek_client.test_connection()
            print(f"DEBUG: DeepSeek status: {deepseek_status}")

            print("DEBUG: Testing Sonnet connection...")
            sonnet_status = sonnet_client.test_connection()
            print(f"DEBUG: Sonnet status: {sonnet_status}")

            self.master.after(0, self._update_api_status_ui, deepseek_status, sonnet_status)
        except Exception as e:
            print(f"DEBUG: Exception in API check: {e}")
            traceback.print_exc()
            self.master.after(0, lambda: messagebox.showerror("Error de Conexión", f"Ocurrió un error al verificar las APIs: {e}"))
            self.master.after(0, self._update_api_status_ui, False, False)

    def _update_api_status_ui(self, deepseek_ok: bool, sonnet_ok: bool):
        """Update API status labels in the UI thread"""
        self.state.set("api_status.deepseek", deepseek_ok)
        self.state.set("api_status.sonnet", sonnet_ok)

        self.api_status_labels['deepseek']['text'] = "✅ Conectado" if deepseek_ok else "❌ Desconectado"
        self.api_status_labels['deepseek']['foreground'] = "green" if deepseek_ok else "red"

        self.api_status_labels['sonnet']['text'] = "✅ Conectado" if sonnet_ok else "❌ Desconectado"
        self.api_status_labels['sonnet']['foreground'] = "green" if sonnet_ok else "red"

        self._run_pre_generation_validation()

    def _update_temp_display(self, *args):
        """Update the temperature value display"""
        temp = self.model_vars['temperature'].get()
        self.temp_display['text'] = f"{temp:.1f}"

    def _save_configuration(self):
        """Save the model and template configuration"""
        models_config = {
            'narrative': self.model_vars['narrative_model'].get(),
            'budget': self.model_vars['budget_model'].get(),
            'temperature': self.model_vars['temperature'].get(),
            'max_tokens': self.model_vars['max_tokens'].get()
        }
        self.state.set("models", models_config)
        messagebox.showinfo("Éxito", "Configuración guardada correctamente.")

    def _run_pre_generation_validation(self):
        """Run all pre-generation validation checks"""
        project_ok, _ = self.state.validate_project()
        tor_ok, _ = self.state.validate_tor()
        apis_ok, _ = self.state.validate_apis()

        self._update_validation_ui("project", project_ok)
        self._update_validation_ui("tor", tor_ok)
        self._update_validation_ui("apis", apis_ok)

        can_generate = project_ok and tor_ok and apis_ok
        if can_generate:
            self.generate_button.config(state="normal")
            self.generate_status_label['text'] = "🚀 Listo para generar la propuesta"
            self.generate_status_label['foreground'] = "green"
        else:
            self.generate_button.config(state="disabled")
            self.generate_status_label['text'] = "❌ Faltan requisitos para la generación"
            self.generate_status_label['foreground'] = "red"

        return can_generate  # Return boolean so callers can decide

    def _update_validation_ui(self, item_id, is_ok):
        """Update validation icon and color"""
        label = self.validation_items.get(item_id)
        if label:
            label['text'] = "✅" if is_ok else "❌"
            label['foreground'] = "green" if is_ok else "red"

    def _start_generation(self):
        """Start the full generation process in a separate thread"""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

        can_generate = self._run_pre_generation_validation()  # Use the returned value
        if not can_generate:
            messagebox.showerror("Error", "No se puede iniciar la generación. Verifique los requisitos.")
            return

        self._toggle_processing_state(True, "generation")
        self.progress_manager.set_steps([
            "Generando propuesta narrativa (borrador)...",
            "Generando presupuesto...",
            "Integrando resultados y guardando archivos..."
        ])

        self._current_thread = threading.Thread(target=self._generation_task)
        self._current_thread.start()

    def _generation_task(self):
        """The main generation task to be run in a separate thread"""
        try:
            print("DEBUG: Starting generation task...")

            # Step 1: Generate narrative
            self.progress_manager.next_step()
            self._log_message("Iniciando generación de narrativa...")
            # Placeholder for actual LLM call
            narrative_result = "Contenido de narrativa generado por IA."
            self.state.set("results.narrative", narrative_result)
            self._log_message("Narrativa generada con éxito.")

            # Step 2: Generate budget (use simple dict + JSON to avoid pydantic serialization issues)
            self.progress_manager.next_step()
            self._log_message("Iniciando generación de presupuesto...")

            budget_result_json = {
                "items": [
                    {"item": "Salario personal técnico", "cost": 50000},
                    {"item": "Materiales de oficina", "cost": 2000},
                ]
            }
            # Store JSON string in state (what UI expects)
            self.state.set("results.budget", json.dumps(budget_result_json))
            self._log_message("Presupuesto generado con éxito.")

            # Step 3: Save results to files
            self.progress_manager.next_step()
            self._log_message("Guardando resultados en archivos...")
            output_folder = self._save_results_to_files(narrative_result, budget_result_json)
            self.state.set("results.output_paths", {
                "folder": str(output_folder),
                "narrative_docx": str(output_folder / "propuesta.docx"),
                "budget_xlsx": str(output_folder / "presupuesto.xlsx")
            })
            self._log_message("Archivos guardados con éxito.")

            self.progress_manager.update("Generación completa", 100)
            self.master.after(0, self._finish_generation_ui_update, True)

        except Exception as e:
            traceback.print_exc()
            self.master.after(0, lambda: messagebox.showerror("Error de Generación", f"Ocurrió un error crítico: {e}"))
            self.master.after(0, self._finish_generation_ui_update, False)

    def _save_results_to_files(self, narrative_content, budget_data):
        """Save narrative and budget to files (placeholder)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = Path("runs") / f"proposal_{timestamp}"
        output_folder.mkdir(parents=True, exist_ok=True)

        # Placeholder for DOCX (writes plain text)
        with open(output_folder / "propuesta.docx", "w", encoding="utf-8") as f:
            f.write(narrative_content)

        # Placeholder for XLSX (writes serialized dict as string)
        # NOTE: intentionally removed `.model_dump()` to avoid freeze
        with open(output_folder / "presupuesto.xlsx", "w", encoding="utf-8") as f:
            f.write(str(budget_data))

        return output_folder

    def _clear_generation_log(self):
        """Clear the generation log text widget"""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def _finish_generation_ui_update(self, success):
        """Update UI after generation task is complete"""
        self._toggle_processing_state(False, "generation")
        if success:
            messagebox.showinfo("Generación Completa", "La propuesta ha sido generada con éxito. Revise la pestaña 'Resultados'.")
        self._update_results_tab_ui()

    def _abort_generation(self):
        """Aborts the currently running thread"""
        if self._current_thread and self._current_thread.is_alive():
            messagebox.showwarning("Abortar", "La generación se detendrá al finalizar el paso actual.")
            # Would need a cooperative cancel flag for true abort
            self._toggle_processing_state(False, "generation")
        else:
            messagebox.showinfo("Abortar", "No hay ninguna tarea de generación en curso.")

    def _log_message(self, message: str):
        """Log a message to the generation log text widget"""
        self.master.after(0, self._add_log_entry, message)

    def _add_log_entry(self, message: str):
        """Adds a log entry in the UI thread"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _toggle_processing_state(self, is_processing, tab):
        """Disable/enable UI elements based on processing state"""
        self._processing = is_processing
        state = "disabled" if is_processing else "normal"

        if tab == "tor":
            self.tor_picker.button.config(state=state)
        elif tab == "generation":
            self.generate_button.config(state="disabled" if is_processing else "normal")
            self.abort_button.config(state="normal" if is_processing else "disabled")
            self.notebook.tab("project", state=state)
            self.notebook.tab("tor", state=state)
            self.notebook.tab("config", state=state)

    def _update_results_tab_ui(self):
        """Update the results tab with the latest information"""
        narrative_path = self.state.get("results.output_paths.narrative_docx")
        budget_path = self.state.get("results.output_paths.budget_xlsx")

        summary_text = ""
        files_list = []

        if narrative_path:
            summary_text += "Documento de Narrativa: ✅ Generado\n"
            files_list.append(f"Narrativa: {Path(narrative_path).name}")

        if budget_path:
            summary_text += "Documento de Presupuesto: ✅ Generado\n"
            files_list.append(f"Presupuesto: {Path(budget_path).name}")

        self.results_summary_text.config(state="normal")
        self.results_summary_text.delete("1.0", tk.END)
        self.results_summary_text.insert("1.0", summary_text or "No hay resultados generados.")
        self.results_summary_text.config(state="disabled")

        self.files_listbox.delete(0, tk.END)
        for item in files_list:
            self.files_listbox.insert(tk.END, item)

    def _open_results_folder(self):
        """Open the generated results folder in the file explorer"""
        folder_path = self.state.get("results.output_paths.folder")
        if folder_path and os.path.exists(folder_path):
            try:
                os.startfile(folder_path)  # Windows
            except AttributeError:
                try:
                    import subprocess
                    subprocess.Popen(['xdg-open', folder_path])  # Linux
                except FileNotFoundError:
                    subprocess.Popen(['open', folder_path])  # macOS
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
        else:
            messagebox.showerror("Error", "La carpeta de resultados no existe.")

    def _open_result_file(self, file_type):
        """Open a specific generated file"""
        path = self.state.get(
            f"results.output_paths.{file_type}_docx" if file_type == 'narrative'
            else f"results.output_paths.{file_type}_xlsx"
        )
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except AttributeError:
                try:
                    import subprocess
                    subprocess.Popen(['xdg-open', path])
                except FileNotFoundError:
                    subprocess.Popen(['open', path])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
        else:
            messagebox.showerror("Error", "El archivo no existe. Por favor, genere la propuesta primero.")

    def _on_window_close(self):
        """Handle window close event"""
        if self._processing:
            if messagebox.askyesno("Confirmar Salida", "Hay un proceso en curso. ¿Desea salir de todas formas?"):
                self.master.destroy()
        else:
            self.master.destroy()


def main():
    """Main function to run the application"""
    root = tk.Tk()
    root.title("Asistente para Propuestas de Proyectos - IEPADES")
    root.geometry("800x650")

    # Apply a nice theme
    style = ttk.Style(root)
    style.theme_use('vista')  # or 'clam', 'alt', 'default', 'classic'

    app = ProposalWizard(root)
    root.mainloop()


if __name__ == '__main__':
    main()
