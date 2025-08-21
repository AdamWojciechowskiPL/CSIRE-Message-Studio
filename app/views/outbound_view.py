# csire_message_studio/app/views/outbound_view.py
import tkinter as tk
from tkinter import ttk
from .widgets.xml_viewer import XmlViewer

class OutboundView(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill="both")

        form_frame = ttk.Labelframe(paned_window, text="Dane komunikatu", padding=10)
        paned_window.add(form_frame, weight=2)

        selection_frame = ttk.Frame(form_frame)
        selection_frame.pack(fill='x', pady=(0, 10), anchor='n')
        selection_frame.columnconfigure(1, weight=1)

        ttk.Label(selection_frame, text="Proces biznesowy:").grid(row=0, column=0, sticky='w', padx=(0, 5), pady=2)
        self.process_combobox = ttk.Combobox(selection_frame, state="readonly")
        self.process_combobox.grid(row=0, column=1, sticky='ew', pady=2)

        ttk.Label(selection_frame, text="Typ komunikatu:").grid(row=1, column=0, sticky='w', padx=(0, 5), pady=2)
        self.message_type_combobox = ttk.Combobox(selection_frame, state="disabled")
        self.message_type_combobox.grid(row=1, column=1, sticky='ew', pady=2)

        ttk.Label(selection_frame, text="Zestaw reguł:").grid(row=2, column=0, sticky='w', padx=(0, 5), pady=2)
        self.rules_combobox = ttk.Combobox(selection_frame, state="disabled")
        self.rules_combobox.grid(row=2, column=1, sticky='ew', pady=2)

        self.build_form_button = ttk.Button(selection_frame, text="Zbuduj formularz")
        self.build_form_button.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10, 0))

        preset_frame = ttk.Labelframe(form_frame, text="Presety", padding=10)
        preset_frame.pack(fill='x', pady=(10, 5), anchor='n')
        preset_frame.columnconfigure(1, weight=1)

        ttk.Label(preset_frame, text="Wybierz preset:").grid(row=0, column=0, sticky='w', padx=(0, 5), pady=2)
        self.preset_combobox = ttk.Combobox(preset_frame, state="disabled")
        self.preset_combobox.grid(row=0, column=1, columnspan=3, sticky='ew', pady=2)

        self.save_preset_button = ttk.Button(preset_frame, text="Zapisz...")
        self.save_preset_button.grid(row=1, column=1, sticky='ew', pady=(5, 0), padx=(0, 2))
        
        self.rename_preset_button = ttk.Button(preset_frame, text="Zmień nazwę...")
        self.rename_preset_button.grid(row=1, column=2, sticky='ew', pady=(5, 0), padx=2)

        self.delete_preset_button = ttk.Button(preset_frame, text="Usuń")
        self.delete_preset_button.grid(row=1, column=3, sticky='ew', pady=(5, 0), padx=(2, 0))

        self.form_container = ttk.Frame(form_frame)
        self.form_container.pack(fill="both", expand=True)

        right_panel = ttk.Frame(paned_window)
        paned_window.add(right_panel, weight=3)
        right_panel.rowconfigure(0, weight=1)
        right_panel.columnconfigure(0, weight=1)

        viewer_frame = ttk.Labelframe(right_panel, text="Podgląd wygenerowanego XML", padding=10)
        viewer_frame.grid(row=0, column=0, sticky="nsew")
        
        # --- ZMIANA: Usunięto argument 'wrap' i powiązanie zdarzenia MouseWheel ---
        self.xml_viewer = XmlViewer(viewer_frame)
        self.xml_viewer.pack(expand=True, fill="both")
        self.xml_viewer.show_xml("<!-- Wybierz proces i komunikat, a następnie zbuduj formularz... -->")

        action_frame = ttk.Frame(right_panel, padding=(10, 10, 0, 0))
        action_frame.grid(row=1, column=0, sticky="ew")
        
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        action_frame.columnconfigure(2, weight=1)
        
        self.populate_button = ttk.Button(action_frame, text="Uzupełnij danymi testowymi")
        self.populate_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.generate_button = ttk.Button(action_frame, text="Generuj i Waliduj XML")
        self.generate_button.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        
        self.save_button = ttk.Button(action_frame, text="Zapisz XML...")
        self.save_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))