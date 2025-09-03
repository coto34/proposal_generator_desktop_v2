import tkinter as tk
from tkinter import ttk, filedialog

class LabeledEntry(ttk.Frame):
    def __init__(self, master, label, var):
        super().__init__(master)
        ttk.Label(self, text=label).pack(anchor="w")
        ttk.Entry(self, textvariable=var).pack(fill="x")

class FilePicker(ttk.Frame):
    def __init__(self, master, label, patterns, callback):
        super().__init__(master)
        self.patterns = patterns
        self.callback = callback
        self.var = tk.StringVar()
        ttk.Label(self, text=label).pack(anchor="w")
        row = ttk.Frame(self); row.pack(fill="x")
        ttk.Entry(row, textvariable=self.var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Examinar", command=self._pick).pack(side="left", padx=6)

    def _pick(self):
        path = filedialog.askopenfilename(filetypes=self.patterns)
        if path:
            self.var.set(path)
            self.callback(path)
