# csire_message_studio/app/views/main_window.py
import tkinter as tk
from tkinter import ttk
from .response_view import ResponseView
from .outbound_view import OutboundView

class MainWindow(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(expand=True, fill="both")

        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Udostępniamy ramki jako atrybuty, aby kontrolery miały do nich dostęp
        self.response_frame = ResponseView(notebook)
        notebook.add(self.response_frame, text="Odpowiedzi (R_1)")

        self.outbound_frame = OutboundView(notebook)
        notebook.add(self.outbound_frame, text="CSIRE → System (np. 3.1.1.1)")
        
        self.status_bar = ttk.Label(self, text="Gotowy.", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)