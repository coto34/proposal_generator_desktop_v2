import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ui.components import LabeledEntry, FilePicker
from pathlib import Path

class ProposalWizard(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self._state = {
            "project": {},
            "tor_path": None,
            "models": {"narrative": "DeepSeek", "budget": "Sonnet", "temperature": 0.2, "max_tokens": 4000, "language": "es"},
            "templates": {"docx": None, "xlsx": None}
        }
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
        messagebox.showinfo("OK", "Proyecto guardado.")

    def _build_tab2(self):
        top = ttk.Frame(self.tab2); top.pack(fill="x")
        self.tor_picker = FilePicker(top, "Seleccionar ToR (PDF/DOCX)", [("PDF","*.pdf"),("Word","*.docx")], self._on_pick_tor)
        self.tor_picker.pack(fill="x", pady=6)
        self.tor_info = ttk.Label(self.tab2, text="Sin archivo seleccionado.")
        self.tor_info.pack(anchor="w", pady=8)

    def _on_pick_tor(self, path):
        self._state["tor_path"] = path
        self.tor_info.config(text=f"ToR: {Path(path).name}")

    def _build_tab3(self):
        frm = ttk.Frame(self.tab3); frm.pack(fill="x")
        model_row1 = ttk.Frame(frm); model_row1.pack(fill="x", pady=6)
        ttk.Label(model_row1, text="Modelo narrativo").pack(side="left")
        self.narrative_var = tk.StringVar(value="DeepSeek")
        ttk.Combobox(model_row1, textvariable=self.narrative_var, values=["DeepSeek"], state="readonly", width=20).pack(side="left", padx=8)

        model_row2 = ttk.Frame(frm); model_row2.pack(fill="x", pady=6)
        ttk.Label(model_row2, text="Modelo presupuesto").pack(side="left")
        self.budget_var = tk.StringVar(value="Sonnet")
        ttk.Combobox(model_row2, textvariable=self.budget_var, values=["Sonnet"], state="readonly", width=20).pack(side="left", padx=8)

        tun_row = ttk.Frame(frm); tun_row.pack(fill="x", pady=6)
        ttk.Label(tun_row, text="Temperature").pack(side="left")
        self.temp_var = tk.DoubleVar(value=0.2)
        ttk.Scale(tun_row, variable=self.temp_var, from_=0.0, to=1.0, orient="horizontal").pack(side="left", padx=8, fill="x", expand=True)
        ttk.Label(tun_row, text="Max tokens").pack(side="left", padx=(16,0))
        self.max_tokens_var = tk.IntVar(value=4000)
        ttk.Entry(tun_row, textvariable=self.max_tokens_var, width=10).pack(side="left", padx=8)

        tpl_row = ttk.Frame(self.tab3); tpl_row.pack(fill="x", pady=12)
        self.docx_picker = FilePicker(tpl_row, "Plantilla DOCX", [("DOCX","*.docx")], self._on_pick_docx)
        self.xlsx_picker = FilePicker(tpl_row, "Plantilla XLSX", [("Excel","*.xlsx")], self._on_pick_xlsx)
        self.docx_picker.pack(fill="x", pady=6)
        self.xlsx_picker.pack(fill="x", pady=6)

        save_btn = ttk.Button(self.tab3, text="Guardar configuración", command=self._save_models_templates)
        save_btn.pack(anchor="e", pady=8)

    def _on_pick_docx(self, path):
        self._state["templates"]["docx"] = path

    def _on_pick_xlsx(self, path):
        self._state["templates"]["xlsx"] = path

    def _save_models_templates(self):
        self._state["models"]["narrative"] = self.narrative_var.get()
        self._state["models"]["budget"] = self.budget_var.get()
        self._state["models"]["temperature"] = float(self.temp_var.get())
        self._state["models"]["max_tokens"] = int(self.max_tokens_var.get())
        messagebox.showinfo("OK", "Configuración guardada.")

    def _build_tab4(self):
        frm = ttk.Frame(self.tab4); frm.pack(fill="both", expand=True)
        self.log = tk.Text(frm, height=20, wrap="word")
        self.log.pack(fill="both", expand=True, pady=8)
        btns = ttk.Frame(frm); btns.pack(fill="x")
        ttk.Button(btns, text="Generar Propuesta", command=self._on_generate).pack(side="left")
        ttk.Button(btns, text="Abortar", command=self._on_abort).pack(side="left", padx=8)

    def _on_generate(self):
        self._append_log("Iniciando pipeline...")
        self._append_log("Validando entradas...")
        if not self._state.get("project") or not self._state["project"].get("title"):
            self._append_log("Error: faltan datos del proyecto.")
            return
        if not self._state.get("tor_path"):
            self._append_log("Error: falta ToR.")
            return
        self._append_log("OK. Ejecutando tareas (placeholder).")
        self._append_log("Completado (demo).")

    def _on_abort(self):
        self._append_log("Abortado por el usuario.")

    def _append_log(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def _build_tab5(self):
        frm = ttk.Frame(self.tab5); frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Resultados").pack(anchor="w")
        self.results_box = tk.Text(frm, height=18, wrap="word")
        self.results_box.pack(fill="both", expand=True, pady=8)
        ttk.Button(frm, text="Abrir carpeta de ejecución", command=self._open_runs_folder).pack(anchor="e")

    def _open_runs_folder(self):
        path = Path.cwd() / "runs"
        path.mkdir(parents=True, exist_ok=True)
        try:
            os_start = "start" if Path().anchor[:1].isalpha() else "xdg-open"
        except:
            os_start = "start"
        try:
            import subprocess
            if os_start == "start":
                subprocess.run(["cmd", "/c", "start", str(path)])
            else:
                subprocess.run([os_start, str(path)])
        except Exception as e:
            messagebox.showerror("Error", str(e))
