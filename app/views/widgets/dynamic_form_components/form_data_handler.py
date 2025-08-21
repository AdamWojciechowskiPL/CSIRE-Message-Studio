# csire_message_studio/app/views/widgets/dynamic_form_components/form_data_handler.py

import tkinter as tk
from tkinter import ttk
from infra.logger import get_logger
from typing import List, Optional, Dict, Any

log = get_logger(__name__)

class FormDataHandler:
    """Odpowiada za wszystkie operacje na danych formularza (wypełnianie, walidacja, zbieranie)."""

    def __init__(self, form_facade):
        self.form = form_facade
        self.validation_errors = set()

    def _set_widget_value_no_trigger(self, widget, value, *, caller: str) -> bool:
        """
        Bezpiecznie ustawia wartość widgetu bez wywoływania zdarzeń walidacji/reguł.
        """
        widget_name = f"'{widget.winfo_name()}' ({widget.winfo_class()})"
        safe_value = value if value is not None else ""

        if widget.get() == safe_value:
            log.debug(f"[SET_VALUE] Wartość w {widget_name} jest już poprawna ('{safe_value}'). Pomijam zapis.")
            return False

        original_state = str(widget.cget('state'))
        temporarily_enabled = False
        
        try:
            if original_state == 'disabled':
                privileged_callers = ('rule_engine_set_value', 'rule_engine_import', 'unconditional_clear', 'rule_engine_generation')
                if caller in privileged_callers:
                    log.debug(f"[SET_VALUE] {widget_name} jest wyłączony. Tymczasowe włączenie przez '{caller}'.")
                    widget.config(state='normal')
                    temporarily_enabled = True
                else:
                    log.warning(f"[SET_VALUE] ZABLOKOWANO zapis do wyłączonego widgetu {widget_name} przez '{caller}'.")
                    return False
            
            log.debug(f"[SET_VALUE] Ustawianie wartości '{safe_value}' w {widget_name}.")
            if isinstance(widget, ttk.Combobox):
                widget.set(safe_value)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, safe_value)
            
            return True

        except Exception:
            log.error(f"[SET_VALUE] Błąd podczas ustawiania wartości w {widget_name}.", exc_info=True)
            return False
        finally:
            if temporarily_enabled:
                log.debug(f"[SET_VALUE] Przywracanie stanu 'disabled' dla {widget_name}.")
                widget.config(state='disabled')

    def populate_with_data(self, data_generator_func, rules: Dict, hierarchy: List[List[str]]):
        """
        Wypełnia formularz danymi w sposób hybrydowy: najpierw deterministycznie wg hierarchii,
        a następnie iteracyjnie, aby uzupełnić pola ujawnione dynamicznie.
        """
        log.info("Rozpoczynanie hybrydowego generowania danych.")
        self.form.update_idletasks()

        # Faza 1: Przebieg deterministyczny oparty na grafie zależności
        log.info("==> Faza 1: Przebieg deterministyczny...")
        for level, field_paths in enumerate(hierarchy):
            log.debug(f"  -> Przetwarzanie poziomu {level+1}/{len(hierarchy)} hierarchii...")
            for field_path in field_paths:
                field_def = self.form.fields_by_path.get(field_path)
                if not field_def: continue

                widgets_to_fill = []
                for key, widgets in self.form.widget_groups.items():
                    if key.startswith(field_path):
                        widgets_to_fill.extend(widgets)
                
                for widget in widgets_to_fill:
                    if widget.winfo_exists() and str(widget.cget('state')) != 'disabled' and not widget.get():
                        available_choices = widget['values'] if isinstance(widget, ttk.Combobox) else None
                        value = data_generator_func(field_def, rules, available_choices)
                        
                        if value is not None:
                            self.set_value_and_trigger_dependencies(widget, value, caller="populate_with_data_deterministic")

        # Faza 2: Iteracyjne uzupełnianie pól, które stały się widoczne
        log.info("==> Faza 2: Iteracyjne uzupełnianie (mop-up)...")
        MAX_MOP_UP_LOOPS = 10
        mop_up_loops = 0
        while mop_up_loops < MAX_MOP_UP_LOOPS:
            mop_up_loops += 1
            filled_in_this_pass = 0
            log.debug(f"  -> Pętla uzupełniająca nr {mop_up_loops}")

            for field_path, field_def in self.form.fields_by_path.items():
                widgets_to_check = []
                for key, widgets in self.form.widget_groups.items():
                    if key.startswith(field_path):
                        widgets_to_check.extend(widgets)
                
                for widget in widgets_to_check:
                    if widget.winfo_exists() and str(widget.cget('state')) != 'disabled' and not widget.get():
                        available_choices = widget['values'] if isinstance(widget, ttk.Combobox) else None
                        value = data_generator_func(field_def, rules, available_choices)
                        
                        if value is not None:
                            self.set_value_and_trigger_dependencies(widget, value, caller="populate_with_data_mopup")
                            filled_in_this_pass += 1
            
            if filled_in_this_pass == 0:
                log.info(f"  -> Formularz stabilny. Zakończono fazę uzupełniającą po {mop_up_loops} pętlach.")
                break
            else:
                log.info(f"  -> W pętli {mop_up_loops} wypełniono {filled_in_this_pass} pól. Kontynuuję...")
                self.form.update_idletasks() # Pozwól UI zareagować na zmiany
        
        if mop_up_loops >= MAX_MOP_UP_LOOPS:
            log.warning("Przekroczono maksymalną liczbę pętli uzupełniających. Przerywam, aby uniknąć zawieszenia.")

        log.info("Zakończono generowanie danych.")
        self.form.update_idletasks()

    def populate_from_dict(self, data: dict):
        log.info("Rozpoczynanie wypełniania formularza z presetu.")
        self.clear_form()
        
        def populate_recursive(data_level, section_defs_level, parent_tk, parent_instance, depth):
            for section_def in section_defs_level:
                if section_def.name not in data_level: continue

                section_data = data_level[section_def.name]
                instances_data = section_data if isinstance(section_data, list) else [section_data]
                
                while len(self.form.rendered_sections[section_def.path]) < len(instances_data):
                    self.form.renderer.add_section_instance(parent_tk, section_def, depth, True, parent_instance)

                instances_ui = self.form.rendered_sections[section_def.path]
                for i, instance_data_dict in enumerate(instances_data):
                    instance_ui = instances_ui[i]
                    if not instance_ui['check_var'].get():
                        instance_ui['check_var'].set(True)

                    for field_def in instance_ui['section_def'].fields:
                        if field_def.name in instance_data_dict:
                            field_values = instance_data_dict[field_def.name]
                            widgets = instance_ui['widgets'][field_def.path]
                            
                            if isinstance(field_values, list):
                                for w, val in zip(widgets, field_values):
                                    self.set_value_and_trigger_dependencies(w, val)
                            else:
                                self.set_value_and_trigger_dependencies(widgets[0], field_values)
                    
                    if instance_ui['section_def'].sub_sections:
                        populate_recursive(instance_data_dict, instance_ui['section_def'].sub_sections, instance_ui['content'], instance_ui, depth + 1)
        
        populate_recursive(data, self.form.form_sections_definitions, self.form.scrollable_frame, None, 0)
        self.form.rule_engine.apply_all_rules()
        log.info("Zakończono wypełnianie formularza z presetu.")

    def get_values(self):
        self.validation_errors.clear()
        first_invalid_widget = None
        
        def validate_recursively(sections):
            nonlocal first_invalid_widget
            for section_def in sections:
                for instance in self.form.rendered_sections.get(section_def.path, []):
                    if not instance['check_var'].get(): continue
                    for field_def in section_def.fields:
                        for widget in instance['widgets'].get(field_def.path, []):
                            if widget.winfo_exists() and widget.cget('state') != 'disabled':
                                if not self._validate_entry(widget.get(), widget.winfo_name()):
                                    if first_invalid_widget is None:
                                        first_invalid_widget = widget
                    validate_recursively(section_def.sub_sections)
                    
        validate_recursively(self.form.form_sections_definitions)
        
        if self.validation_errors:
            log.warning(f"Walidacja formularza nie powiodła się. Znaleziono {len(self.validation_errors)} błędów.")
            if first_invalid_widget: first_invalid_widget.focus_set()
            return {}, False

        data = self._collect_data()
        return data, True

    def _collect_data(self) -> Dict[str, Any]:
        """Zbiera dane z aktywnych pól formularza do zagnieżdżonego słownika."""
        def collect_recursively(parent_dict, sections_definitions):
            for section_def in sections_definitions:
                active_instances_data = []
                for instance in self.form.rendered_sections.get(section_def.path, []):
                    if not instance['check_var'].get(): continue
                    
                    instance_data = {}
                    for field_def in section_def.fields:
                        values = [w.get() for w in instance['widgets'].get(field_def.path, []) if w.get() and w.cget('state') != 'disabled']
                        if values:
                            instance_data[field_def.name] = values if field_def.is_list else values[0]
                    
                    collect_recursively(instance_data, section_def.sub_sections)
                    
                    if instance_data: active_instances_data.append(instance_data)
                
                if active_instances_data:
                    parent_dict[section_def.name] = active_instances_data if section_def.max_occurs != 1 else active_instances_data[0]
        
        if not self.form.form_sections_definitions: return {}
        
        root_name = self.form.form_sections_definitions[0].path.split('.')[0]
        data = {root_name: {}}
        collect_recursively(data[root_name], self.form.form_sections_definitions)
        return data

    def clear_form(self):
        log.debug("Rozpoczynanie pełnego czyszczenia formularza.")
        for section_path, instances in list(self.form.rendered_sections.items()):
            if not instances: continue
            
            section_def = instances[0]['section_def']
            min_instances = 1 if section_def.min_occurs > 0 else 0
            
            while len(instances) > min_instances:
                self.form.renderer._remove_section_instance(instances[-1])

            for instance in instances:
                instance['check_var'].set(section_def.min_occurs > 0)
                for field_path, widgets in instance['widgets'].items():
                    if widgets:
                       self._set_widget_value_no_trigger(widgets[0], "", caller="unconditional_clear")
        log.info("Formularz został wyczyszczony.")

    def clear_generated_data(self, rules: Dict[str, Any]):
        """
        Czyści wszystkie pola formularza, które nie są zablokowane (disabled).
        """
        log.info("Inteligentne czyszczenie danych (pola zablokowane nie będą czyszczone)...")
        for widgets in self.form.widget_groups.values():
            for widget in widgets:
                if widget.winfo_exists() and str(widget.cget('state')) != 'disabled':
                    self._set_widget_value_no_trigger(widget, "", caller="unconditional_clear")
                    
        log.info("Zakończono czyszczenie danych generowanych.")
        self.form.update_idletasks()

    def set_field_value_by_name(self, field_name: str, value: str):
        for instances in self.form.rendered_sections.values():
            for instance in instances:
                if not instance['check_var'].get(): continue
                for field_def in instance['section_def'].fields:
                    if field_def.name == field_name:
                        widgets = instance['widgets'].get(field_def.path)
                        if widgets:
                            self.set_value_and_trigger_dependencies(widgets[0], value)
                            return
        log.warning(f"Nie znaleziono aktywnego pola o nazwie '{field_name}'.")

    def set_value_and_trigger_dependencies(self, widget, value, caller="set_value_and_trigger"):
        if self._set_widget_value_no_trigger(widget, value, caller=caller):
            field_def = self._get_field_def_for_widget(widget)
            if field_def:
                log.debug(f"Uruchamianie reguł zależnych od '{field_def.path}' po zmianie wartości.")
                self.form.rule_engine.evaluate_rules_for_trigger(field_def.path)
                # Dajemy szansę UI na odświeżenie się po zmianie wartości
                self.form.update_idletasks()

    def _get_field_def_for_widget(self, widget) -> Optional[Any]:
        for path, widgets in self.form.widget_groups.items():
            if widget in widgets:
                return self.form.fields_by_path.get(path.split('[')[0])
        return None

    def _validate_entry(self, value, widget_name) -> bool:
        try:
            widget = self.form.nametowidget(widget_name)
        except KeyError:
            self.validation_errors.discard(widget_name)
            return True
            
        field_def = self._get_field_def_for_widget(widget)
        if not field_def: return True
        
        is_valid, error_message = True, ""
        if field_def.is_required and not value:
            is_valid, error_message = False, "Pole jest wymagane."
        elif value:
            try:
                if field_def.xsd_type_obj:
                    field_def.xsd_type_obj.validate(value)
            except Exception as e:
                is_valid, error_message = False, str(e).splitlines()[0]
                
        if hasattr(widget, 'error_label'):
            widget.error_label.config(text=error_message if not is_valid else "")
        
        if not is_valid:
            self.validation_errors.add(widget_name)
        else:
            self.validation_errors.discard(widget_name)
            
        return is_valid