# csire_message_studio/app/views/response_view.py
import tkinter as tk
from tkinter import ttk
from .widgets.xml_viewer import XmlViewer

class ResponseView(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill="both")

        controls_frame = ttk.Labelframe(paned_window, text="Sterowanie i dane wejściowe", padding=10)
        paned_window.add(controls_frame, weight=1)

        self.import_button = ttk.Button(controls_frame, text="Importuj komunikat (1.1.1.1 / 1.2.1.1)...")
        self.import_button.pack(fill='x', pady=(0, 5))

        self.populate_button = ttk.Button(controls_frame, text="Uzupełnij danymi testowymi")
        self.populate_button.pack(fill='x', pady=(0, 10))

        self.form_container = ttk.Frame(controls_frame)
        self.form_container.pack(fill='both', expand=True, pady=10, anchor='n')

        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill='x', side='bottom', pady=(20, 0))
        
        self.generate_button = ttk.Button(action_frame, text="Generuj i Waliduj R_1")
        self.generate_button.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.save_button = ttk.Button(action_frame, text="Zapisz XML...")
        self.save_button.pack(side='left', expand=True, fill='x', padx=(5, 0))

        viewer_frame = ttk.Labelframe(paned_window, text="Podgląd wygenerowanego XML", padding=10)
        paned_window.add(viewer_frame, weight=2)
        self.xml_viewer = XmlViewer(viewer_frame)
        self.xml_viewer.pack(expand=True, fill="both")
        self.xml_viewer.show_xml("<!-- Oczekiwanie na wygenerowanie komunikatu... -->")