import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ui.components import LabeledEntry, FilePicker
from services.llm_providers import DeepSeekClient, SonnetClient
from services.document_processor import DocumentProcessor
from services.token_manager import TokenManager, ChainedPromptGenerator
from validation.schemas import BudgetResult
from pathlib import Path
import json
import threading
from datetime import datetime

class ProposalWizard(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self._state = {
            "project": {},
            "tor_path": None,
            "tor_content": None,
            "tor_chunks": [],
            "models": {"narrative": "DeepSeek", "budget": "Sonnet", "temperature": 0.2, "max_tokens": 4000, "language": "es"},
            "templates": {"docx": None, "xlsx": None},
            "results": {"narrative": None, "budget": None, "output_paths": {}}
        }
        self._processing = False
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.tab1 = ttk.Frame(nb, padding=12)
        self.tab2 = ttk.Frame(nb, padding=12)
        self.tab3 = ttk.Frame(nb, padding=12)
        self.tab4 = ttk.Frame(nb, padding=12)
        self.tab5 = ttk.Frame(nb, padding=12)

        nb.add(self.tab1, text="Proyecto")
        nb.add(self.tab2, text="Términos de Referencia")
        nb.add(self.tab3, text="LLM & Plantillas")
        nb.add(self.tab4, text="Generación")
        nb.add(self.tab5, text="Resultados")

        self._build_tab1()
        self._build_tab2()
        self._build_tab3()
        self._build_tab4()
        self._build_tab5()

    def _build_tab1(self):
        frm = ttk.Frame(self.tab1)
        frm.pack(fill="x", expand=False)

        self.title_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.lang_var = tk.StringVar(value="es")
        self.donor_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.cap_var = tk.StringVar()
        self.org_var = tk.Text(self.tab1, height=6, wrap="word")

        LabeledEntry(frm, "Título del proyecto", self.title_var).pack(fill="x", pady=6)
        LabeledEntry(frm, "País", self.country_var).pack(fill="x", pady=6)

        lang_row = ttk.Frame(frm); lang_row.pack(fill="x", pady=6)
        ttk.Label(lang_row, text="Idioma").pack(side="left")
        ttk.Combobox(lang_row, textvariable=self.lang_var, values=["es","en"], state="readonly", width=8).pack(side="left", padx=8)

        LabeledEntry(frm, "Donante", self.donor_var).pack(fill="x", pady=6)
        LabeledEntry(frm, "Duración (meses)", self.duration_var).pack(fill="x", pady=6)
        LabeledEntry(frm, "Tope de presupuesto", self.cap_var).pack(fill="x", pady=6)

        org_box = ttk.Frame(self.tab1); org_box.pack(fill="both", expand=True, pady=10)
        ttk.Label(org_box, text="Perfil de la organización").pack(anchor="w")
        self.org_var.pack(fill="both", expand=True)

        save_btn = ttk.Button(self.tab1, text="Guardar datos", command=self._save_project_inputs)
        save_btn.pack(anchor="e", pady=8)

    def _save_project_inputs(self):
        self._state["project"] = {
            "title": self.title_var.get().strip(),
            "country": self.country_var.get().strip(),
            "language": self.lang_var.get(),
            "donor": self.donor_var.get().strip(),
            "duration_months": self.duration_var.get().strip(),
            "budget_cap": self.cap_var.get().strip(),
            "org_profile": self.org_var.get("1.0","end").strip()
        }
        messagebox.showinfo("OK", "Datos del proyecto guardados correctamente.")

    def _build_tab2(self):
        top = ttk.Frame(self.tab2); top.pack(fill="x")
        self.tor_picker = FilePicker(top, "Seleccionar ToR (PDF/DOCX)", [("PDF","*.pdf"),("Word","*.docx")], self._on_pick_tor)
        self.tor_picker.pack(fill="x", pady=6)
        self.tor_info = ttk.Label(self.tab2, text="Sin archivo seleccionado.")
        self.tor_info.pack(anchor="w", pady=8)
        
        # Add progress bar for document processing
        self.tor_progress = ttk.Progressbar(self.tab2, mode='indeterminate')
        self.tor_progress.pack(fill="x", pady=8)
        self.tor_progress.pack_forget()  # Hide initially
        
        # Document analysis info
        analysis_frame = ttk.LabelFrame(self.tab2, text="Análisis del Documento")
        analysis_frame.pack(fill="x", pady=10)
        
        self.doc_analysis = ttk.Label(analysis_frame, text="Ningún documento analizado aún", wraplength=600, justify="left")
        self.doc_analysis.pack(padx=10, pady=10, anchor="w")
        
        # Preview area
        preview_frame = ttk.LabelFrame(self.tab2, text="Vista previa del contenido")
        preview_frame.pack(fill="both", expand=True, pady=10)
        
        self.tor_preview = tk.Text(preview_frame, height=10, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tor_preview.yview)
        self.tor_preview.configure(yscrollcommand=scrollbar.set)
        
        self.tor_preview.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _on_pick_tor(self, path):
        self._state["tor_path"] = path
        self.tor_info.config(text=f"Procesando: {Path(path).name}...")
        self.tor_progress.pack(fill="x", pady=8)
        self.tor_progress.start()
        
        # Process document in separate thread
        def process_document():
            content = DocumentProcessor.extract_text_from_file(path)
            self.master.after(0, self._tor_processing_complete, content, Path(path).name)
        
        threading.Thread(target=process_document, daemon=True).start()

    def _tor_processing_complete(self, content, filename):
        self.tor_progress.stop()
        self.tor_progress.pack_forget()
        
        if content and not content.startswith("Error"):
            self._state["tor_content"] = content
            
            # Analyze document and create chunks
            estimated_tokens = TokenManager.estimate_tokens(content)
            max_tokens_deepseek = TokenManager.get_max_content_tokens("deepseek")
            max_tokens_sonnet = TokenManager.get_max_content_tokens("sonnet")
            
            # Create chunks for different providers
            deepseek_chunks = TokenManager.intelligent_chunk_tor(content, max_tokens_deepseek)
            sonnet_chunks = TokenManager.intelligent_chunk_tor(content, max_tokens_sonnet)
            
            self._state["tor_chunks"] = {
                "deepseek": deepseek_chunks,
                "sonnet": sonnet_chunks
            }
            
            # Update UI with analysis
            analysis_text = f"""
📄 Documento: {filename}
📊 Tamaño: {len(content):,} caracteres (~{estimated_tokens:,} tokens)
🔗 Chunks para DeepSeek: {len(deepseek_chunks)} (máx {max_tokens_deepseek:,} tokens c/u)
🔗 Chunks para Sonnet: {len(sonnet_chunks)} (máx {max_tokens_sonnet:,} tokens c/u)
📋 Estrategia: {'Prompt único' if len(deepseek_chunks) <= 1 else 'Prompts encadenados'}
            """.strip()
            
            self.doc_analysis.config(text=analysis_text)
            self.tor_info.config(text=f"✅ ToR procesado correctamente: {filename}")
            
            # Show preview
            self.tor_preview.config(state="normal")
            self.tor_preview.delete("1.0", "end")
            preview_text = content[:2000] + "\n\n... (documento continúa)" if len(content) > 2000 else content
            self.tor_preview.insert("1.0", preview_text)
            self.tor_preview.config(state="disabled")
            
            # Show chunk info if multiple chunks
            if len(deepseek_chunks) > 1:
                chunk_info = "\n\n=== SECCIONES IDENTIFICADAS ===\n"
                for i, chunk in enumerate(deepseek_chunks):
                    chunk_info += f"{i+1}. {chunk['section']} (~{TokenManager.estimate_tokens(chunk['content'])} tokens)\n"
                
                self.tor_preview.config(state="normal")
                self.tor_preview.insert("end", chunk_info)
                self.tor_preview.config(state="disabled")
        else:
            self.tor_info.config(text=f"❌ Error procesando {filename}")
            self.doc_analysis.config(text=f"Error: {content}")
            messagebox.showerror("Error", f"No se pudo procesar el archivo:\n{content}")

    def _build_tab3(self):
        frm = ttk.Frame(self.tab3); frm.pack(fill="x")
        
        # API Status indicators
        status_frame = ttk.LabelFrame(frm, text="Estado de las APIs")
        status_frame.pack(fill="x", pady=10)
        
        self.deepseek_status = ttk.Label(status_frame, text="DeepSeek: No configurado")
        self.deepseek_status.pack(anchor="w", padx=10, pady=2)
        
        self.sonnet_status = ttk.Label(status_frame, text="Sonnet: No configurado")
        self.sonnet_status.pack(anchor="w", padx=10, pady=2)
        
        ttk.Button(status_frame, text="Verificar APIs", command=self._check_api_status).pack(anchor="e", padx=10, pady=5)
        
        # Token limits info
        limits_frame = ttk.LabelFrame(frm, text="Límites de Tokens")
        limits_frame.pack(fill="x", pady=10)
        
        limits_text = f"""
DeepSeek: ~{TokenManager.get_max_content_tokens('deepseek'):,} tokens máx por prompt
Sonnet: ~{TokenManager.get_max_content_tokens('sonnet'):,} tokens máx por prompt
Estrategia: Chunking inteligente + prompts encadenados para documentos grandes
        """.strip()
        
        ttk.Label(limits_frame, text=limits_text, justify="left").pack(padx=10, pady=10, anchor="w")
        
        # Model selection
        model_frame = ttk.LabelFrame(frm, text="Selección de Modelos")
        model_frame.pack(fill="x", pady=10)
        
        model_row1 = ttk.Frame(model_frame); model_row1.pack(fill="x", pady=6, padx=10)
        ttk.Label(model_row1, text="Modelo narrativo").pack(side="left")
        self.narrative_var = tk.StringVar(value="DeepSeek")
        ttk.Combobox(model_row1, textvariable=self.narrative_var, values=["DeepSeek"], state="readonly", width=20).pack(side="left", padx=8)

        model_row2 = ttk.Frame(model_frame); model_row2.pack(fill="x", pady=6, padx=10)
        ttk.Label(model_row2, text="Modelo presupuesto").pack(side="left")
        self.budget_var = tk.StringVar(value="Sonnet")
        ttk.Combobox(model_row2, textvariable=self.budget_var, values=["Sonnet"], state="readonly", width=20).pack(side="left", padx=8)

        # Parameters
        param_frame = ttk.LabelFrame(frm, text="Parámetros")
        param_frame.pack(fill="x", pady=10)
        
        tun_row = ttk.Frame(param_frame); tun_row.pack(fill="x", pady=6, padx=10)
        ttk.Label(tun_row, text="Temperature").pack(side="left")
        self.temp_var = tk.DoubleVar(value=0.2)
        temp_scale = ttk.Scale(tun_row, variable=self.temp_var, from_=0.0, to=1.0, orient="horizontal")
        temp_scale.pack(side="left", padx=8, fill="x", expand=True)
        self.temp_label = ttk.Label(tun_row, text="0.2")
        self.temp_label.pack(side="left", padx=8)
        temp_scale.configure(command=self._update_temp_label)
        
        tokens_row = ttk.Frame(param_frame); tokens_row.pack(fill="x", pady=6, padx=10)
        ttk.Label(tokens_row, text="Max tokens").pack(side="left")
        self.max_tokens_var = tk.IntVar(value=4000)
        ttk.Entry(tokens_row, textvariable=self.max_tokens_var, width=10).pack(side="left", padx=8)

        # Templates
        tpl_frame = ttk.LabelFrame(self.tab3, text="Plantillas")
        tpl_frame.pack(fill="x", pady=10)
        
        self.docx_picker = FilePicker(tpl_frame, "Plantilla DOCX (opcional)", [("DOCX","*.docx")], self._on_pick_docx)
        self.xlsx_picker = FilePicker(tpl_frame, "Plantilla XLSX (opcional)", [("Excel","*.xlsx")], self._on_pick_xlsx)
        self.docx_picker.pack(fill="x", pady=6, padx=10)
        self.xlsx_picker.pack(fill="x", pady=6, padx=10)

        save_btn = ttk.Button(self.tab3, text="Guardar configuración", command=self._save_models_templates)
        save_btn.pack(anchor="e", pady=8)
        
        # Check API status on startup
        self.master.after(100, self._check_api_status)

    def _update_temp_label(self, value):
        self.temp_label.config(text=f"{float(value):.1f}")

    def _check_api_status(self):
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        sonnet_key = os.getenv("SONNET_API_KEY")
        
        deepseek_status = "✅ Configurado" if deepseek_key else "❌ No configurado"
        sonnet_status = "✅ Configurado" if sonnet_key else "❌ No configurado"
        
        self.deepseek_status.config(text=f"DeepSeek: {deepseek_status}")
        self.sonnet_status.config(text=f"Sonnet: {sonnet_status}")

    def _on_pick_docx(self, path):
        self._state["templates"]["docx"] = path

    def _on_pick_xlsx(self, path):
        self._state["templates"]["xlsx"] = path

    def _save_models_templates(self):
        self._state["models"]["narrative"] = self.narrative_var.get()
        self._state["models"]["budget"] = self.budget_var.get()
        self._state["models"]["temperature"] = float(self.temp_var.get())
        self._state["models"]["max_tokens"] = int(self.max_tokens_var.get())
        messagebox.showinfo("OK", "Configuración guardada correctamente.")

    def _build_tab4(self):
        frm = ttk.Frame(self.tab4); frm.pack(fill="both", expand=True)
        
        # Progress section
        progress_frame = ttk.LabelFrame(frm, text="Progreso")
        progress_frame.pack(fill="x", pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Listo para generar")
        self.progress_label.pack(padx=10, pady=2)
        
        # Chunk processing info
        chunk_frame = ttk.LabelFrame(frm, text="Estado del Procesamiento")
        chunk_frame.pack(fill="x", pady=10)
        
        self.chunk_status = ttk.Label(chunk_frame, text="Esperando documento...")
        self.chunk_status.pack(padx=10, pady=5)
        
        # Log section
        log_frame = ttk.LabelFrame(frm, text="Registro de Ejecución")
        log_frame.pack(fill="both", expand=True, pady=10)
        
        self.log = tk.Text(log_frame, height=12, wrap="word")
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_scrollbar.set)
        
        self.log.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        log_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Buttons
        btns = ttk.Frame(frm); btns.pack(fill="x", pady=5)
        self.generate_btn = ttk.Button(btns, text="Generar Propuesta", command=self._on_generate)
        self.generate_btn.pack(side="left")
        self.abort_btn = ttk.Button(btns, text="Abortar", command=self._on_abort, state="disabled")
        self.abort_btn.pack(side="left", padx=8)

    def _on_generate(self):
        if self._processing:
            return
            
        # Validation
        if not self._validate_inputs():
            return
            
        self._processing = True
        self.generate_btn.config(state="disabled")
        self.abort_btn.config(state="normal")
        
        # Update chunk status
        chunks = self._state.get("tor_chunks", {})
        if chunks:
            deepseek_chunks = len(chunks.get("deepseek", []))
            sonnet_chunks = len(chunks.get("sonnet", []))
            self.chunk_status.config(text=f"DeepSeek: {deepseek_chunks} chunks | Sonnet: {sonnet_chunks} chunks")
        
        # Start generation in separate thread
        def generate():
            try:
                self._generate_proposal()
            except Exception as e:
                self.master.after(0, self._append_log, f"❌ Error inesperado: {str(e)}")
            finally:
                self.master.after(0, self._generation_complete)
        
        threading.Thread(target=generate, daemon=True).start()

    def _validate_inputs(self):
        self._append_log("🔍 Validando entradas...")
        
        if not self._state.get("project") or not self._state["project"].get("title"):
            self._append_log("❌ Error: faltan datos del proyecto. Ve a la pestaña 'Proyecto'.")
            messagebox.showerror("Error", "Faltan datos del proyecto")
            return False
            
        if not self._state.get("tor_path") or not self._state.get("tor_content"):
            self._append_log("❌ Error: falta procesar ToR. Ve a la pestaña 'Términos de Referencia'.")
            messagebox.showerror("Error", "Falta procesar los Términos de Referencia")
            return False
            
        if not os.getenv("DEEPSEEK_API_KEY") and not os.getenv("SONNET_API_KEY"):
            self._append_log("❌ Error: no hay APIs configuradas. Revisa tu archivo .env")
            messagebox.showerror("Error", "No hay APIs configuradas")
            return False
            
        self._append_log("✅ Validación exitosa")
        return True

    def _generate_proposal(self):
        self.master.after(0, self._update_progress, 0, "🚀 Iniciando generación...")
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path("runs") / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        
        self.master.after(0, self._append_log, f"📁 Directorio de salida: {run_dir}")
        
        # Step 1: Generate narrative using DeepSeek with token management
        self.master.after(0, self._update_progress, 20, "📝 Generando narrativa...")
        narrative = self._generate_narrative_with_chunking()
        
        if narrative and not narrative.startswith("Error"):
            self._state["results"]["narrative"] = narrative
            self.master.after(0, self._append_log, "✅ Narrativa generada exitosamente")
        else:
            self.master.after(0, self._append_log, f"❌ Error en narrativa: {narrative}")
        
        # Step 2: Generate budget using Sonnet with token management
        self.master.after(0, self._update_progress, 50, "💰 Generando presupuesto...")
        budget = self._generate_budget_with_chunking()
        
        if budget and not budget.get("error"):
            self._state["results"]["budget"] = budget
            total = budget.get("total", 0)
            self.master.after(0, self._append_log, f"✅ Presupuesto generado exitosamente (Total: ${total:,.2f})")
        else:
            error_msg = budget.get("error", "Error desconocido") if budget else "No se generó presupuesto"
            self.master.after(0, self._append_log, f"❌ Error en presupuesto: {error_msg}")
        
        # Step 3: Generate documents
        self.master.after(0, self._update_progress, 80, "📄 Generando documentos...")
        
        # Generate DOCX
        docx_path = run_dir / "propuesta.docx"
        context = {
            **self._state["project"],
            "project_title": self._state["project"].get("title", "Propuesta"),
            "narrative": narrative if narrative and not narrative.startswith("Error") else "No se pudo generar la narrativa"
        }
        
        if DocumentProcessor.generate_docx_from_template(
            self._state["templates"].get("docx"), 
            str(docx_path), 
            context
        ):
            self._state["results"]["output_paths"]["docx"] = str(docx_path)
            self.master.after(0, self._append_log, f"✅ Documento DOCX generado: {docx_path.name}")
        else:
            self.master.after(0, self._append_log, "❌ Error generando documento DOCX")
        
        # Generate Excel budget
        if budget and not budget.get("error"):
            excel_path = run_dir / "presupuesto.xlsx"
            if DocumentProcessor.generate_excel_budget(str(excel_path), budget):
                self._state["results"]["output_paths"]["xlsx"] = str(excel_path)
                self.master.after(0, self._append_log, f"✅ Presupuesto Excel generado: {excel_path.name}")
            else:
                self.master.after(0, self._append_log, "❌ Error generando presupuesto Excel")
        
        # Save raw results
        results_path = run_dir / "results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self._state["results"], f, ensure_ascii=False, indent=2)
        
        # Save processing metadata
        metadata = {
            "timestamp": timestamp,
            "project_info": self._state["project"],
            "tor_analysis": {
                "original_size": len(self._state.get("tor_content", "")),
                "estimated_tokens": TokenManager.estimate_tokens(self._state.get("tor_content", "")),
                "chunks_used": {
                    "deepseek": len(self._state.get("tor_chunks", {}).get("deepseek", [])),
                    "sonnet": len(self._state.get("tor_chunks", {}).get("sonnet", []))
                }
            },
            "models_used": self._state["models"]
        }
        
        metadata_path = run_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.master.after(0, self._update_progress, 100, "🎉 ¡Generación completada!")
        self.master.after(0, self._append_log, "🎉 ¡Propuesta generada exitosamente!")

    def _generate_narrative_with_chunking(self):
        """Generate narrative using intelligent chunking and chained prompts"""
        try:
            chunks = self._state.get("tor_chunks", {}).get("deepseek", [])
            if not chunks:
                return "Error: No hay chunks de DeepSeek disponibles"
            
            self.master.after(0, self._append_log, f"📝 Procesando narrativa con {len(chunks)} chunk(s)")
            
            # Create DeepSeek client
            client = DeepSeekClient(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                temperature=self._state["models"]["temperature"],
                max_tokens=self._state["models"]["max_tokens"]
            )
            
            # Get max tokens for chunking
            max_tokens = TokenManager.get_max_content_tokens("deepseek")
            
            # Use ChainedPromptGenerator
            generator = ChainedPromptGenerator(client, max_tokens)
            result = generator.process_tor_chunks(chunks, self._state["project"], "narrative")
            
            return result
            
        except Exception as e:
            return f"Error generando narrativa: {str(e)}"

    def _generate_budget_with_chunking(self):
        """Generate budget using intelligent chunking and chained prompts"""
        try:
            chunks = self._state.get("tor_chunks", {}).get("sonnet", [])
            if not chunks:
                return {"error": "No hay chunks de Sonnet disponibles"}
            
            self.master.after(0, self._append_log, f"💰 Procesando presupuesto con {len(chunks)} chunk(s)")
            
            # Create Sonnet client
            client = SonnetClient(
                api_key=os.getenv("SONNET_API_KEY"),
                temperature=self._state["models"]["temperature"],
                max_tokens=self._state["models"]["max_tokens"]
            )
            
            # Get max tokens for chunking
            max_tokens = TokenManager.get_max_content_tokens("sonnet")
            
            # Use ChainedPromptGenerator
            generator = ChainedPromptGenerator(client, max_tokens)
            result = generator.process_tor_chunks(chunks, self._state["project"], "budget")
            
            return result
            
        except Exception as e:
            return {"error": f"Error generando presupuesto: {str(e)}"}

    def _update_progress(self, value, text):
        self.progress_bar['value'] = value
        self.progress_label.config(text=text)

    def _generation_complete(self):
        self._processing = False
        self.generate_btn.config(state="normal")
        self.abort_btn.config(state="disabled")
        self._update_progress(0, "Generación completada")

    def _on_abort(self):
        if self._processing:
            self._processing = False
            self.generate_btn.config(state="normal")
            self.abort_btn.config(state="disabled")
            self._append_log("🛑 Generación abortada por el usuario")

    def _append_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{timestamp}] {msg}\n")
        self.log.see("end")

    def _build_tab5(self):
        frm = ttk.Frame(self.tab5); frm.pack(fill="both", expand=True)
        
        # Results summary
        summary_frame = ttk.LabelFrame(frm, text="Resumen de Resultados")
        summary_frame.pack(fill="x", pady=10)
        
        self.results_summary = ttk.Label(summary_frame, text="No hay resultados aún")
        self.results_summary.pack(padx=10, pady=10)
        
        # Processing statistics
        stats_frame = ttk.LabelFrame(frm, text="Estadísticas de Procesamiento")
        stats_frame.pack(fill="x", pady=10)
        
        self.processing_stats = ttk.Label(stats_frame, text="Sin estadísticas disponibles", justify="left")
        self.processing_stats.pack(padx=10, pady=10, anchor="w")
        
        # Generated files
        files_frame = ttk.LabelFrame(frm, text="Archivos Generados")
        files_frame.pack(fill="x", pady=10)
        
        self.files_list = tk.Listbox(files_frame, height=4)
        self.files_list.pack(fill="x", padx=10, pady=5)
        self.files_list.bind("<Double-1>", self._open_selected_file)
        
        # Results content
        content_frame = ttk.LabelFrame(frm, text="Vista Previa de Contenido")
        content_frame.pack(fill="both", expand=True, pady=10)
        
        self.results_box = tk.Text(content_frame, height=12, wrap="word", state="disabled")
        results_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.results_box.yview)
        self.results_box.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_box.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        results_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Action buttons
        btns_frame = ttk.Frame(frm)
        btns_frame.pack(fill="x", pady=5)
        
        ttk.Button(btns_frame, text="Abrir carpeta de resultados", command=self._open_runs_folder).pack(side="left")
        ttk.Button(btns_frame, text="Actualizar vista", command=self._update_results_view).pack(side="left", padx=8)
        ttk.Button(btns_frame, text="Limpiar resultados", command=self._clear_results).pack(side="left")

    def _update_results_view(self):
        # Update summary
        results = self._state["results"]
        narrative = results.get("narrative")
        budget = results.get("budget")
        
        if narrative or budget:
            summary_parts = []
            if narrative and not narrative.startswith("Error"):
                summary_parts.append("✅ Narrativa generada")
            else:
                summary_parts.append("❌ Error en narrativa")
                
            if budget and not budget.get("error"):
                summary_parts.append("✅ Presupuesto generado")
                total = budget.get("total", 0)
                summary_parts.append(f"Total: ${total:,.2f}")
            else:
                summary_parts.append("❌ Error en presupuesto")
                
            self.results_summary.config(text=" | ".join(summary_parts))
        else:
            self.results_summary.config(text="No hay resultados aún")
        
        # Update processing statistics
        if self._state.get("tor_content"):
            chunks = self._state.get("tor_chunks", {})
            stats_text = f"""
Documento original: {len(self._state.get('tor_content', '')):,} caracteres
Tokens estimados: ~{TokenManager.estimate_tokens(self._state.get('tor_content', '')):,}
Chunks DeepSeek: {len(chunks.get('deepseek', []))}
Chunks Sonnet: {len(chunks.get('sonnet', []))}
Estrategia: {'Prompt único' if len(chunks.get('deepseek', [])) <= 1 else 'Prompts encadenados'}
            """.strip()
            self.processing_stats.config(text=stats_text)
        
        # Update files list
        self.files_list.delete(0, tk.END)
        output_paths = results.get("output_paths", {})
        for file_type, path in output_paths.items():
            if path and os.path.exists(path):
                filename = Path(path).name
                self.files_list.insert(tk.END, f"{file_type.upper()}: {filename}")
        
        # Update content preview
        self.results_box.config(state="normal")
        self.results_box.delete("1.0", "end")
        
        if narrative and not narrative.startswith("Error"):
            self.results_box.insert("end", "=== NARRATIVA ===\n\n")
            preview = narrative[:1500] + "..." if len(narrative) > 1500 else narrative
            self.results_box.insert("end", preview + "\n\n")
        
        if budget and not budget.get("error"):
            self.results_box.insert("end", "=== RESUMEN PRESUPUESTAL ===\n\n")
            self.results_box.insert("end", f"Total: ${budget.get('total', 0):,.2f}\n")
            self.results_box.insert("end", f"Moneda: {budget.get('currency', 'N/A')}\n")
            self.results_box.insert("end", f"Items: {len(budget.get('items', []))}\n\n")
            
            if budget.get('summary_by_category'):
                self.results_box.insert("end", "Resumen por categoría:\n")
                for category, amount in budget.get('summary_by_category', {}).items():
                    self.results_box.insert("end", f"  {category}: ${amount:,.2f}\n")
        
        self.results_box.config(state="disabled")

    def _open_selected_file(self, event):
        selection = self.files_list.curselection()
        if selection:
            item = self.files_list.get(selection[0])
            file_type = item.split(":")[0].lower()
            output_paths = self._state["results"].get("output_paths", {})
            
            if file_type in output_paths:
                path = output_paths[file_type]
                if os.path.exists(path):
                    self._open_file(path)

    def _open_file(self, path):
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")

    def _clear_results(self):
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres limpiar los resultados?"):
            self._state["results"] = {"narrative": None, "budget": None, "output_paths": {}}
            self._update_results_view()

    def _open_runs_folder(self):
        runs_path = Path.cwd() / "runs"
        runs_path.mkdir(parents=True, exist_ok=True)
        
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(runs_path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(runs_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(runs_path)])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {str(e)}")