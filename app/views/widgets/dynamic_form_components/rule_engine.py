# csire_message_studio/app/views/widgets/dynamic_form_components/rule_engine.py
import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from infra.logger import get_logger
from infra import config as app_config
from services import data_generators
import operator

from services.data_generators import validation_registry

log = get_logger(__name__)

OPERATOR_MAP = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge
}

class FormElement:
    """Klasa-adapter ujednolicająca interfejs do manipulacji polami i sekcjami."""
    def __init__(self, widget_or_section_instance, form_facade, field_def=None):
        self.element = widget_or_section_instance
        self.form = form_facade
        self.field_def = field_def

    def show(self, should_show=True):
        if isinstance(self.element, dict): # To jest sekcja
            container = self.element['container']
            header = self.element.get('header_frame')
            
            if header:
                parent_container_of_content = container.master
                if should_show:
                    header.pack(fill=tk.X, anchor="n")
                    parent_container_of_content.pack(fill=tk.X, anchor="n", after=header)
                    if not self.element['check_var'].get():
                        self.element['check_var'].set(True)
                else:
                    header.pack_forget()
                    parent_container_of_content.pack_forget()
                    if self.element['check_var'].get():
                        self.element['check_var'].set(False)
            else:
                if should_show:
                    container.pack(fill=tk.X, anchor="n")
                    if not self.element['check_var'].get():
                        self.element['check_var'].set(True)
                else:
                    container.pack_forget()
                    if self.element['check_var'].get():
                        self.element['check_var'].set(False)
        else: # To jest widget (pole)
            widget = self.element
            if hasattr(widget, 'row_frame'):
                if should_show:
                    widget.row_frame.pack(fill=tk.X, pady=3, padx=5)
                else:
                    widget.row_frame.pack_forget()

    def set_enabled(self, should_enable=True):
        elements_to_process = []
        if isinstance(self.element, dict):
            for widgets in self.element['widgets'].values():
                elements_to_process.extend(widgets)
        else:
            elements_to_process.append(self.element)

        for elem in elements_to_process:
            new_state = "disabled"
            if should_enable:
                new_state = "readonly" if isinstance(elem, ttk.Combobox) else "normal"
            
            if elem.cget('state') != new_state:
                elem.config(state=new_state)

    def set_required(self, should_be_required=True):
        if self.field_def and hasattr(self.field_def, 'label_widget'):
            label = self.field_def.label_widget
            current_text = label.cget("text")
            base_text = current_text.strip().removesuffix(" *")
            
            if should_be_required and not current_text.endswith(" *"):
                label.config(text=f"{base_text} *")
            elif not should_be_required and current_text.endswith(" *"):
                label.config(text=base_text)
            
            self.field_def.is_required = should_be_required

    def clear_value(self):
        """Bezwarunkowo czyści wartość widgetu lub wszystkich widgetów w sekcji."""
        elements_to_clear = []
        if isinstance(self.element, dict): # Sekcja
            for widgets_list in self.element['widgets'].values():
                elements_to_clear.extend(widgets_list)
        else: # Widget
            elements_to_clear.append(self.element)

        for elem in elements_to_clear:
            log.debug(f"Silnik reguł czyści wartość widgetu '{elem.winfo_name()}'")
            self.form.data_handler._set_widget_value_no_trigger(elem, "", caller="unconditional_clear")

    def set_multiple_allowed(self, should_allow=True):
        if isinstance(self.element, dict):
            section_path = self.element['section_def'].path
            self.form.renderer.toggle_multiplicity_controls(section_path, should_allow)

    def set_filtered_list(self, allowed_values=None):
        if not isinstance(self.element, ttk.Combobox) or not self.field_def or not self.field_def.enumerations: return
        widget = self.element
        full_list = [''] + self.field_def.enumerations
        
        new_list = []
        if allowed_values is None:
            log.debug(f"RULE ENGINE: Przywracanie pełnej listy dla Combobox '{self.field_def.path}'.")
            new_list = full_list
        else:
            log.debug(f"RULE ENGINE: Filtrowanie Combobox '{self.field_def.path}' do wartości: {allowed_values}.")
            new_list = [''] + [v for v in self.field_def.enumerations if v in allowed_values]

        current_value = widget.get()
        if current_value and current_value not in new_list:
            log.info(f"Wartość '{current_value}' w polu '{self.field_def.path}' nie jest już dozwolona po filtracji. Czyszczenie pola.")
            widget.set('')
        
        widget['values'] = new_list
    
    def set_choices(self, choices: list):
        if not isinstance(self.element, ttk.Combobox): return
        widget = self.element
        
        log.debug(f"RULE ENGINE: Ustawianie nowej listy opcji dla '{self.field_def.path}': {choices}")
        new_list = [''] + choices
        
        current_value = widget.get()
        if current_value and current_value not in new_list:
            widget.set('')
        
        widget['values'] = new_list
        self.set_enabled(True)


class RuleEngine:
    """Zarządza logiką biznesową formularza wczytaną z plików JSON."""
    def __init__(self, form, rules, process_info, message_info):
        self.form = form
        self.rules = rules
        self.process_info = process_info
        self.message_info = message_info
        self.rules_by_trigger = self._index_rules_by_trigger()
        self.imported_data_context = None
        log.info(f"Silnik reguł zainicjowany. Załadowano {len(rules)} reguł. Zindeksowano {len(self.rules_by_trigger)} pól wyzwalających.")

    def update_rules(self, new_rules):
        self.rules = new_rules
        self.rules_by_trigger = self._index_rules_by_trigger()
        log.info(f"Silnik reguł zaktualizowany. Przeindeksowano {len(self.rules_by_trigger)} pól wyzwalających dla {len(self.rules)} reguł.")

    def _index_rules_by_trigger(self):
        indexed = defaultdict(list)
        for target_path, rule_definitions in self.rules.items():
            for rule_name, rule in rule_definitions.items():
                if not rule.get("condition"):
                    indexed["__initial__"].append({"target_path": target_path, "rule": rule})
                    continue

                condition = rule.get("condition")
                conditions = condition.get("conditions", [condition])
                for cond in conditions:
                    if "field_path" in cond:
                        trigger_path = cond["field_path"]
                        indexed[trigger_path].append({"target_path": target_path, "rule": rule})
        return indexed

    def apply_all_rules(self):
        log.debug("Uruchamianie silnika reguł: Aplikowanie wszystkich reguł...")
        
        initial_rules = self.rules_by_trigger.get("__initial__", [])
        for item in initial_rules:
            self._execute_action(item["target_path"], item["rule"], True)

        for target_path, rule_definitions in self.rules.items():
            for rule in rule_definitions.values():
                condition = rule.get("condition")
                if condition:
                    is_met = self._evaluate_condition(condition, rule)
                    self._execute_action(target_path, rule, is_met)

        log.debug("Zakończono aplikowanie wszystkich reguł.")

    def apply_import_rules(self, imported_data: dict):
        log.info("Aplikowanie reguł importowych na podstawie załadowanych danych...")
        self.imported_data_context = imported_data
        
        for target_path, rule_definitions in self.rules.items():
            for rule in rule_definitions.values():
                if rule.get("action") == "set_value_from_import":
                    self._execute_action(target_path, rule, is_condition_met=True)

        self.imported_data_context = None
        log.info("Zakończono aplikowanie reguł importowych.")

    def evaluate_rules_for_trigger(self, trigger_path):
        if trigger_path not in self.rules_by_trigger: return
        
        rules_to_run = self.rules_by_trigger[trigger_path]
        log.debug(f"Wartość w '{trigger_path}' zmieniona. Uruchamianie {len(rules_to_run)} powiązanych reguł.")
        for item in rules_to_run:
            is_condition_met = self._evaluate_condition(item["rule"].get("condition"), item["rule"])
            self._execute_action(item["target_path"], item["rule"], is_condition_met)
            
    def _evaluate_condition(self, condition, parent_rule):
        if not condition: return True

        operator = condition.get("operator", "AND").upper()
        sub_conditions = condition.get("conditions", [condition])
        results = []

        for cond in sub_conditions:
            if "field_path" not in cond:
                if "permission_key" in cond:
                    results.append(app_config.PERMISSIONS.get(cond["permission_key"], False))
                elif "section_path" in cond:
                    section_instances = self.form.rendered_sections.get(cond["section_path"], [])
                    is_active = any(inst['check_var'].get() for inst in section_instances)
                    results.append(is_active)
                continue

            widget = self.form.get_widget_by_path(cond["field_path"])
            if not widget: 
                results.append(False)
                continue
            
            current_value = widget.get()
            
            if "values" in cond:
                results.append(current_value in cond["values"])
            elif "not_values" in cond:
                results.append(current_value not in cond["not_values"])
            elif "operator" in cond and "value" in cond:
                op_func = OPERATOR_MAP.get(cond["operator"])
                if not op_func:
                    log.warning(f"Nierozpoznany operator '{cond['operator']}' w regule dla '{cond['field_path']}'")
                    results.append(False)
                    continue
                try:
                    field_val = float(current_value)
                    rule_val = float(cond["value"])
                    results.append(op_func(field_val, rule_val))
                except (ValueError, TypeError):
                    results.append(False)
            elif "is_not_empty" in cond:
                is_not_empty = bool(current_value.strip())
                results.append(is_not_empty == cond["is_not_empty"])

        return all(results) if operator == "AND" else any(results)

    def _execute_action(self, target_path, rule, is_condition_met):
        action = rule.get("action")
        target_elements = self.form.get_elements_by_path(target_path)
        if not target_elements: return

        for element in target_elements:
            log.debug(f"RULE_ENGINE: Wykonuję akcję '{action}' na elemencie '{target_path}'. Warunek spełniony: {is_condition_met}")
            
            if action == "set_value":
                if is_condition_met:
                    value = self._get_value_from_rule(rule["value"])
                    log.debug(f"RULE_ENGINE: Akcja 'set_value'. Ustawiam wartość '{value}' dla '{target_path}'.")
                    if not isinstance(element.element, dict): 
                        self.form.data_handler.set_value_and_trigger_dependencies(element.element, value, caller="rule_engine_set_value")
                    element.set_enabled(False)
            elif action == "set_value_from_import":
                if not self.imported_data_context:
                    log.warning("Próba wykonania akcji 'set_value_from_import' bez aktywnego kontekstu importu.")
                    continue
                source_path = rule.get("source_path")
                value = self.imported_data_context.get(source_path)
                if value is not None:
                    log.info(f"IMPORT_RULE: Ustawianie wartości '{value}' z '{source_path}' do pola '{target_path}'.")
                    if not isinstance(element.element, dict):
                        self.form.data_handler.set_value_and_trigger_dependencies(element.element, value, caller="rule_engine_import")
                    if rule.get("lock_field", True):
                        element.set_enabled(False)
            elif action == "set_choices_from_process_matrix":
                if is_condition_met:
                    process_type = rule.get("process_type")
                    choices = validation_registry.get_valid_codes_for_process(process_type) or []
                    element.set_choices(choices)
                else:
                    log.debug(f"Warunek dla 'set_choices_from_process_matrix' dla '{target_path}' niespełniony. Nie podejmowano akcji.")
            elif action == "hide":
                element.show(False)
            elif action in ("show_if_permission", "show_if_section_exists", "show_if_value"):
                if not is_condition_met:
                    element.clear_value()
                element.show(is_condition_met)
            elif action == "forbid_if_value":
                if is_condition_met:
                    element.clear_value()
                element.show(not is_condition_met)
            elif action == "require_if_value":
                element.show(is_condition_met)
                element.set_required(is_condition_met)
                if not is_condition_met:
                    element.clear_value()
                element.set_enabled(is_condition_met)
            elif action == "enable_if_value":
                if not is_condition_met:
                    element.clear_value()
                element.set_enabled(is_condition_met)
            elif action == "allow_multiple_if_value":
                element.set_multiple_allowed(is_condition_met)
            elif action == "filter_values":
                if is_condition_met:
                    element.set_filtered_list(rule.get("values", []))
                else:
                    element.set_filtered_list(None)
            elif action == "data_generation":
                if is_condition_met and element.field_def:
                    generator_name = rule.get("generator")
                    params = rule.get("params", {})
                    value = None
                    if generator_name == "error_code_for_process":
                        value = data_generators.generate_error_code_for_process(params.get("process_type"))
                    
                    if value is not None and not isinstance(element.element, dict):
                         log.info(f"RULE_ENGINE: Warunkowa generacja dla '{target_path}' zwróciła wartość '{value}'.")
                         self.form.data_handler.set_value_and_trigger_dependencies(element.element, value, caller="rule_engine_generation")
    
    def _get_value_from_rule(self, rule_value):
        if isinstance(rule_value, str):
            if rule_value.startswith("config:"):
                key = rule_value.split(":")[1]
                return getattr(app_config, key, f"BŁĄD_CONFIG: Nie znaleziono klucza '{key}'")
            if rule_value.startswith("generate:"):
                gen_parts = rule_value.split(":", 2)
                gen_type = gen_parts[1]

                if gen_type == "uuid":
                    return data_generators.generate_uuid()
                if gen_type == "error_code_for_process" and len(gen_parts) > 2:
                    param = gen_parts[2]
                    return data_generators.generate_error_code_for_process(param)
                else:
                    log.error(f"Błąd parsowania reguły generatora: {rule_value}.")
                    return None
            if rule_value.startswith("process."):
                key = rule_value.split('.')[1]
                return self.form.process_info.get(key, f"BŁĄD_PROCESS_INFO: Nie znaleziono klucza '{key}'")
            if rule_value.startswith("message."):
                key = rule_value.split('.')[1]
                return self.form.message_info.get(key, f"BŁĄD_MESSAGE_INFO: Nie znaleziono klucza '{key}'")
        return rule_value