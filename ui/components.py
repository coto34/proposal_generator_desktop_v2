import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

# Backward compatibility - keep original classes
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
        self.button = ttk.Button(row, text="Examinar", command=self._pick)
        self.button.pack(side="left", padx=6)

    def _pick(self):
        path = filedialog.askopenfilename(filetypes=self.patterns)
        if path:
            self.var.set(path)
            self.callback(path)
    
    def clear(self):
        """Clear the file path"""
        self.var.set("")
class EnhancedLabeledEntry(ttk.Frame):
    """Enhanced labeled entry with modern styling"""
    def __init__(self, master, label, var, placeholder="", required=False):
        super().__init__(master)
        
        # Color scheme
        self.colors = {
            'primary': '#E8F5E8',
            'secondary': '#C8E6C9', 
            'accent': '#4CAF50',
            'text': '#2E7D32',
            'white': '#FFFFFF',
            'border': '#A5D6A7',
            'placeholder': '#9E9E9E'
        }
        
        self.var = var
        self.placeholder = placeholder
        self.required = required
        
        # Label with required indicator
        label_text = f"{label}{'*' if required else ''}"
        self.label = tk.Label(self, 
                            text=label_text,
                            bg=self.colors['white'],
                            fg=self.colors['accent'] if required else self.colors['text'],
                            font=('Segoe UI', 10, 'bold'))
        self.label.pack(anchor="w", pady=(0, 3))
        
        # Entry with enhanced styling
        self.entry = tk.Entry(self,
                            textvariable=var,
                            bg=self.colors['white'],
                            fg=self.colors['text'],
                            font=('Segoe UI', 10),
                            relief='solid',
                            bd=1,
                            highlightthickness=2,
                            highlightcolor=self.colors['accent'],
                            highlightbackground=self.colors['border'])
        self.entry.pack(fill="x", ipady=8)
        
        # Placeholder functionality
        if placeholder:
            self._setup_placeholder()
        
        # Validation styling
        if required:
            self.entry.bind('<FocusOut>', self._validate)
            self.entry.bind('<KeyRelease>', self._on_change)

    def _setup_placeholder(self):
        """Setup placeholder text functionality"""
        def on_focus_in(event):
            if self.entry.get() == self.placeholder:
                self.entry.delete(0, "end")
                self.entry.config(fg=self.colors['text'])
        
        def on_focus_out(event):
            if self.entry.get() == "":
                self.entry.insert(0, self.placeholder)
                self.entry.config(fg=self.colors['placeholder'])
        
        # Set initial placeholder
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=self.colors['placeholder'])
        
        self.entry.bind('<FocusIn>', on_focus_in)
        self.entry.bind('<FocusOut>', on_focus_out)

    def _validate(self, event=None):
        """Validate required fields"""
        if self.required:
            value = self.var.get().strip()
            if not value or value == self.placeholder:
                self.entry.config(highlightbackground='red', highlightcolor='red')
                self.label.config(fg='red')
            else:
                self.entry.config(highlightbackground=self.colors['border'], 
                                highlightcolor=self.colors['accent'])
                self.label.config(fg=self.colors['accent'])

    def _on_change(self, event=None):
        """Handle text changes"""
        if self.required:
            self._validate()

    def get_value(self):
        """Get the actual value (not placeholder)"""
        value = self.var.get().strip()
        return value if value != self.placeholder else ""


class ModernFilePicker(ttk.Frame):
    """Modern file picker with drag & drop visual and preview"""
    def __init__(self, master, label, description, patterns, callback, multiple=False):
        super().__init__(master)
        
        # Color scheme
        self.colors = {
            'primary': '#E8F5E8',
            'secondary': '#C8E6C9',
            'accent': '#4CAF50',
            'text': '#2E7D32',
            'white': '#FFFFFF',
            'light_gray': '#F5F5F5',
            'border': '#A5D6A7'
        }
        
        self.patterns = patterns
        self.callback = callback
        self.multiple = multiple
        self.selected_files = []
        
        # Main container
        container = tk.Frame(self, bg=self.colors['white'])
        container.pack(fill="both", expand=True)
        
        # Header
        header = tk.Frame(container, bg=self.colors['white'])
        header.pack(fill="x", pady=(0, 10))
        
        title_label = tk.Label(header,
                             text=label,
                             bg=self.colors['white'],
                             fg=self.colors['text'],
                             font=('Segoe UI', 12, 'bold'))
        title_label.pack(anchor="w")
        
        if description:
            desc_label = tk.Label(header,
                                text=description,
                                bg=self.colors['white'],
                                fg=self.colors['text'],
                                font=('Segoe UI', 9))
            desc_label.pack(anchor="w", pady=(2, 0))
        
        # Drop zone
        self.drop_zone = tk.Frame(container,
                                bg=self.colors['light_gray'],
                                relief='solid',
                                bd=2,
                                height=100)
        self.drop_zone.pack(fill="x")
        self.drop_zone.pack_propagate(False)
        
        # Drop zone content
        self.drop_content = tk.Frame(self.drop_zone, bg=self.colors['light_gray'])
        self.drop_content.pack(expand=True)
        
        self.drop_icon = tk.Label(self.drop_content,
                                text="📁",
                                bg=self.colors['light_gray'],
                                fg=self.colors['text'],
                                font=('Segoe UI', 24))
        self.drop_icon.pack()
        
        self.drop_text = tk.Label(self.drop_content,
                                text="Arrastra archivos aquí o haz clic para seleccionar",
                                bg=self.colors['light_gray'],
                                fg=self.colors['text'],
                                font=('Segoe UI', 10))
        self.drop_text.pack(pady=(5, 0))
        
        # File info display
        self.info_frame = tk.Frame(container, bg=self.colors['white'])
        self.info_frame.pack(fill="x", pady=(10, 0))
        
        self.info_label = tk.Label(self.info_frame,
                                 text="Sin archivos seleccionados",
                                 bg=self.colors['white'],
                                 fg=self.colors['text'],
                                 font=('Segoe UI', 9))
        self.info_label.pack(anchor="w")
        
        # Bind click events
        self._bind_click_events()

    def _bind_click_events(self):
        """Bind click events to all clickable elements"""
        widgets = [self.drop_zone, self.drop_content, self.drop_icon, self.drop_text]
        for widget in widgets:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_hover_enter)
            widget.bind("<Leave>", self._on_hover_leave)

    def _on_hover_enter(self, event):
        """Handle hover enter"""
        self.drop_zone.config(bg=self.colors['secondary'])
        self.drop_content.config(bg=self.colors['secondary'])
        self.drop_icon.config(bg=self.colors['secondary'])
        self.drop_text.config(bg=self.colors['secondary'])

    def _on_hover_leave(self, event):
        """Handle hover leave"""
        self.drop_zone.config(bg=self.colors['light_gray'])
        self.drop_content.config(bg=self.colors['light_gray'])
        self.drop_icon.config(bg=self.colors['light_gray'])
        self.drop_text.config(bg=self.colors['light_gray'])

    def _on_click(self, event):
        """Handle file selection"""
        if self.multiple:
            paths = filedialog.askopenfilenames(filetypes=self.patterns)
            if paths:
                self.selected_files = list(paths)
                self._update_display_multiple(paths)
                self.callback(paths)
        else:
            path = filedialog.askopenfilename(filetypes=self.patterns)
            if path:
                self.selected_files = [path]
                self._update_display_single(path)
                self.callback(path)

    def _update_display_single(self, path):
        """Update display for single file"""
        file_path = Path(path)
        file_size = file_path.stat().st_size / 1024  # KB
        
        # Update drop zone
        self.drop_icon.config(text="✅")
        self.drop_text.config(text=f"{file_path.name}")
        
        # Update info
        self.info_label.config(
            text=f"📄 {file_path.name} ({file_size:.1f} KB)",
            fg=self.colors['accent']
        )

    def _update_display_multiple(self, paths):
        """Update display for multiple files"""
        file_count = len(paths)
        total_size = sum(Path(p).stat().st_size for p in paths) / 1024  # KB
        
        # Update drop zone
        self.drop_icon.config(text="✅")
        self.drop_text.config(text=f"{file_count} archivos seleccionados")
        
        # Update info
        file_list = "\n".join([f"• {Path(p).name}" for p in paths[:3]])
        if file_count > 3:
            file_list += f"\n• ... y {file_count - 3} más"
        
        self.info_label.config(
            text=f"📁 {file_count} archivos ({total_size:.1f} KB)\n{file_list}",
            fg=self.colors['accent']
        )

    def clear_selection(self):
        """Clear current selection"""
        self.selected_files = []
        self.drop_icon.config(text="📁")
        self.drop_text.config(text="Arrastra archivos aquí o haz clic para seleccionar")
        self.info_label.config(text="Sin archivos seleccionados", fg=self.colors['text'])


class ProgressCard(tk.Frame):
    """Progress card widget for showing completion status"""
    def __init__(self, master, title, steps):
        super().__init__(master)
        
        # Color scheme
        self.colors = {
            'primary': '#E8F5E8',
            'secondary': '#C8E6C9',
            'accent': '#4CAF50', 
            'text': '#2E7D32',
            'white': '#FFFFFF',
            'light_gray': '#F5F5F5',
            'border': '#A5D6A7',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336'
        }
        
        self.steps = steps
        self.current_step = 0
        
        # Main card
        self.card = tk.Frame(self, bg=self.colors['white'], relief='solid', bd=1)
        self.card.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        header = tk.Frame(self.card, bg=self.colors['white'])
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        title_label = tk.Label(header,
                             text=title,
                             bg=self.colors['white'],
                             fg=self.colors['text'],
                             font=('Segoe UI', 12, 'bold'))
        title_label.pack(anchor="w")
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(header,
                                          mode='determinate',
                                          length=300)
        self.progress_bar.pack(fill="x", pady=(10, 0))
        
        # Steps list
        self.steps_frame = tk.Frame(self.card, bg=self.colors['white'])
        self.steps_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.step_labels = []
        self._create_steps()

    def _create_steps(self):
        """Create step indicators"""
        for i, step in enumerate(self.steps):
            step_frame = tk.Frame(self.steps_frame, bg=self.colors['white'])
            step_frame.pack(fill="x", pady=2)
            
            # Status indicator
            status_label = tk.Label(step_frame,
                                  text="⏳",
                                  bg=self.colors['white'],
                                  fg=self.colors['text'],
                                  font=('Segoe UI', 10))
            status_label.pack(side="left", padx=(0, 10))
            
            # Step text
            text_label = tk.Label(step_frame,
                                text=step,
                                bg=self.colors['white'],
                                fg=self.colors['text'],
                                font=('Segoe UI', 10))
            text_label.pack(side="left", anchor="w")
            
            self.step_labels.append((status_label, text_label))

    def update_step(self, step_index, status="completed"):
        """Update step status"""
        if step_index < len(self.step_labels):
            status_label, text_label = self.step_labels[step_index]
            
            if status == "completed":
                status_label.config(text="✅", fg=self.colors['success'])
                text_label.config(fg=self.colors['success'])
            elif status == "current":
                status_label.config(text="🔄", fg=self.colors['warning'])
                text_label.config(fg=self.colors['warning'])
            elif status == "error":
                status_label.config(text="❌", fg=self.colors['error'])
                text_label.config(fg=self.colors['error'])
        
        # Update progress bar
        progress = (step_index + 1) / len(self.steps) * 100
        self.progress_bar['value'] = progress

    def reset(self):
        """Reset all steps to pending"""
        for status_label, text_label in self.step_labels:
            status_label.config(text="⏳", fg=self.colors['text'])
            text_label.config(fg=self.colors['text'])
        self.progress_bar['value'] = 0


class InfoCard(tk.Frame):
    """Information card widget"""
    def __init__(self, master, title, content, icon="ℹ️", card_type="info"):
        super().__init__(master)
        
        # Color scheme based on card type
        type_colors = {
            'info': {'bg': '#E3F2FD', 'border': '#2196F3', 'text': '#1976D2'},
            'success': {'bg': '#E8F5E8', 'border': '#4CAF50', 'text': '#2E7D32'},
            'warning': {'bg': '#FFF8E1', 'border': '#FF9800', 'text': '#F57C00'},
            'error': {'bg': '#FFEBEE', 'border': '#F44336', 'text': '#D32F2F'}
        }
        
        colors = type_colors.get(card_type, type_colors['info'])
        
        # Main card
        card = tk.Frame(self, 
                       bg=colors['bg'],
                       relief='solid',
                       bd=1,
                       highlightbackground=colors['border'],
                       highlightthickness=1)
        card.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Content
        content_frame = tk.Frame(card, bg=colors['bg'])
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header with icon and title
        header = tk.Frame(content_frame, bg=colors['bg'])
        header.pack(fill="x", pady=(0, 10))
        
        icon_label = tk.Label(header,
                            text=icon,
                            bg=colors['bg'],
                            fg=colors['text'],
                            font=('Segoe UI', 14))
        icon_label.pack(side="left", padx=(0, 10))
        
        title_label = tk.Label(header,
                             text=title,
                             bg=colors['bg'],
                             fg=colors['text'],
                             font=('Segoe UI', 11, 'bold'))
        title_label.pack(side="left")
        
        # Content text
        content_label = tk.Label(content_frame,
                               text=content,
                               bg=colors['bg'],
                               fg=colors['text'],
                               font=('Segoe UI', 10),
                               wraplength=400,
                               justify="left")
        content_label.pack(anchor="w")