# csire_message_studio/app/views/widgets/dynamic_form.py

import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from infra.logger import get_logger
from .dynamic_form_components.rule_engine import RuleEngine, FormElement
from .dynamic_form_components.form_renderer import FormRenderer
from .dynamic_form_components.form_data_handler import FormDataHandler
from typing import Dict, Any

log = get_logger(__name__)

class DynamicForm(ttk.Frame):
    """
    Klasa-Fasada koordynująca pracę wyspecjalizowanych komponentów formularza.
    """
    def __init__(self, master, form_sections_definitions, rules=None, process_info=None, message_info=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.form_sections_definitions = form_sections_definitions
        self.rules = rules or {}
        self.process_info = process_info or {}
        self.message_info = message_info or {}

        self.fields_by_path = self._flatten_fields(form_sections_definitions)
        self.rendered_sections = defaultdict(list)
        self.widget_groups = defaultdict(list)

        self._setup_styles_and_canvas()

        self.data_handler = FormDataHandler(self)
        self.rule_engine = RuleEngine(self, self.rules, self.process_info, self.message_info)
        self.renderer = FormRenderer(self, self.rules)

        self.renderer.render()
        self.rule_engine.apply_all_rules()

    def _flatten_fields(self, sections):
        flat_map = {}
        def recurse(sub_sections):
            for section in sub_sections:
                for field in section.fields:
                    flat_map[field.path] = field
                recurse(section.sub_sections)
        recurse(sections)
        return flat_map

    def _setup_styles_and_canvas(self):
        style = ttk.Style()
        style.configure("Error.TLabel", foreground="red", font=("Helvetica", 8))
        style.configure("Section.TFrame")
        style.configure("Header.TFrame")
        style.configure("Content.TLabelframe")
        style.configure("Content.TLabelframe.Label", font=("Helvetica", 1, "bold"))
        style.configure("Section.TLabel", font=("Helvetica", 10, "bold"))
        style.configure("Optional.TCheckbutton", foreground="darkblue")

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mouse_wheel)


    def _on_mouse_wheel(self, event):
        """Przechwytuje zdarzenie kółka myszy, przewija canvas i zatrzymuje dalszą propagację."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def bind_scroll_recursively(self, widget):
        """Rekurencyjnie przypisuje handler przewijania do widgetu i wszystkich jego potomków."""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self.bind_scroll_recursively(child)

    def populate_with_data(self, data_generator_func, rules=None, hierarchy=None):
        self.data_handler.populate_with_data(data_generator_func, rules, hierarchy)

    def populate_from_dict(self, data: dict):
        self.data_handler.populate_from_dict(data)

    def get_values(self):
        return self.data_handler.get_values()

    def clear_form(self):
        self.data_handler.clear_form()

    def clear_generated_data(self, rules: Dict[str, Any]):
        """Przekazuje aktualne reguły do handlera, aby wiedział, co chronić."""
        self.data_handler.clear_generated_data(rules)

    def set_field_value_by_name(self, field_name: str, value: str):
        self.data_handler.set_field_value_by_name(field_name, value)

    def get_widget_by_path(self, path: str):
        for key, widgets in self.widget_groups.items():
            base_key = key.split('[')[0]
            if base_key == path and widgets:
                return widgets[0]
        log.warning(f"Nie udało się znaleźć widgetu dla ścieżki '{path}'")
        return None

    def get_elements_by_path(self, path: str):
        elements = []
        log.debug(f"GET_ELEMENTS: Szukam elementów dla ścieżki '{path}'.")
        
        if path in self.rendered_sections:
            log.debug(f"GET_ELEMENTS: Znaleziono pasującą sekcję w `rendered_sections`. Liczba instancji: {len(self.rendered_sections[path])}")
            elements.extend([FormElement(inst, self) for inst in self.rendered_sections[path]])

        for key, widgets in self.widget_groups.items():
            base_key = key.split('[')[0]
            if base_key == path:
                log.debug(f"GET_ELEMENTS: Znaleziono pasujące widgety w `widget_groups` dla klucza '{key}'. Liczba: {len(widgets)}")
                field_def = self.fields_by_path.get(base_key)
                elements.extend([FormElement(w, self, field_def) for w in widgets])

        if not elements:
            log.warning(f"GET_ELEMENTS: Nie znaleziono ŻADNYCH elementów dla ścieżki '{path}'")
        return elements