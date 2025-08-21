# csire_message_studio/app/controllers/response_controller.py
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import json
import datetime
from typing import Optional
from collections import defaultdict

from infra import config
from infra.logger import get_logger
from services.xsd_parser import XsdParser
from services.xml_builder import XmlBuilder
from domain.validation.xsd_validator import XsdValidator
from app.views.widgets.dynamic_form import DynamicForm
from infra.file_handler import read_file, write_file
from services.converters import extract_ids_from_json_envelope


log = get_logger(__name__)

class ResponseController:
    def __init__(self, view, status_bar):
        self.view = view
        self.status_bar = status_bar
        log.info("Inicjalizacja ResponseController.")
        
        self.xml_builder = XmlBuilder()
        self.xsd_parser = None
        self.xsd_validator = None
        self.dynamic_form = None
        self.rules = {}

        self._setup_dynamic_form()
        self._bind_events()

    def _setup_dynamic_form(self):
        try:
            log.info(f"Próba załadowania schematu odpowiedzi R_1 z: {config.XSD_RESPONSE_R1_PATH}")

            self.xsd_parser = XsdParser(config.XSD_RESPONSE_R1_PATH)
            self.xsd_validator = XsdValidator(self.xsd_parser.schema)
            self.root_element_name = list(self.xsd_parser.schema.elements.keys())[0]
            self.form_sections = self.xsd_parser.get_form_structure_for_element(self.root_element_name)
            
            self.dynamic_form = DynamicForm(self.view.form_container, self.form_sections, rules={}, process_info={}, message_info={})
            self.dynamic_form.pack(fill="both", expand=True)

            timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
            self.dynamic_form.set_field_value_by_name("MessageTimestamp", timestamp)
            log.info(f"Automatycznie ustawiono MessageTimestamp w formularzu R_1: {timestamp}")
            
            self._load_and_apply_rules(None)

        except Exception as e:
            log.critical(f"Nie udało się załadować schematu R_1 i zbudować formularza odpowiedzi!", exc_info=True)
            messagebox.showerror("Błąd krytyczny", f"Nie można załadować schematu dla odpowiedzi R_1:\n\n{e}")

    def _load_and_apply_rules(self, business_process: Optional[str]):
        """Dynamicznie ładuje i aplikuje reguły na podstawie procesu biznesowego."""
        rules_file_to_load = config.SYSTEM_MESSAGES["Response_R1"]["rules_file"]
        
        if business_process:
            specific_rules_filename = f"R_1_{business_process.replace('.', '_').strip('_')}.json"
            specific_rules_path = config.MESSAGE_RULES_DIR / specific_rules_filename
            if specific_rules_path.exists():
                rules_file_to_load = specific_rules_filename
                log.info(f"Znaleziono dedykowany plik reguł dla procesu '{business_process}': {specific_rules_filename}")
            else:
                log.warning(f"Nie znaleziono dedykowanego pliku reguł '{specific_rules_filename}'. Używam domyślnego {rules_file_to_load}.")
        else:
            log.info("Brak procesu biznesowego. Ładowanie domyślnych reguł dla R_1.")

        rules_path = config.MESSAGE_RULES_DIR / rules_file_to_load
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f).get("rules", {})
            log.info(f"Pomyślnie załadowano {len(self.rules)} reguł z pliku {rules_file_to_load}.")
        else:
            self.rules = {}
            log.error(f"Plik reguł '{rules_path}' nie został znaleziony!")

        if self.dynamic_form:
            self.dynamic_form.rule_engine.update_rules(self.rules)
            self.dynamic_form.rule_engine.apply_all_rules()
            log.debug("Zaktualizowano i przeładowano reguły w silniku formularza.")

    def _bind_events(self):
        self.view.import_button.config(command=self.import_message)
        self.view.populate_button.config(command=self.populate_with_test_data)
        self.view.generate_button.config(command=self.generate_response)
        self.view.save_button.config(command=self.save_xml)

    def import_message(self):
        file_path_str = filedialog.askopenfilename(
            title="Importuj komunikat w kopercie JSON",
            filetypes=[("Pliki JSON", "*.json"), ("Wszystkie pliki", "*.*")]
        )
        if not file_path_str: return

        content = read_file(Path(file_path_str))
        if not content:
            messagebox.showerror("Błąd odczytu", f"Nie udało się odczytać pliku: {file_path_str}")
            return
        
        try:
            extracted_data = extract_ids_from_json_envelope(content)
            
            self._load_and_apply_rules(extracted_data.get("business_process"))
            
            if self.dynamic_form:
                self.dynamic_form.rule_engine.apply_import_rules(extracted_data)

            self.status_bar.config(text=f"Pomyślnie zaimportowano dane i reguły z: {Path(file_path_str).name}")

        except Exception as e:
            log.error(f"Nie udało się przetworzyć importowanego pliku JSON: {file_path_str}", exc_info=True)
            messagebox.showerror("Błąd importu", f"Błąd przetwarzania pliku JSON:\n\n{e}")

    def _build_dependency_hierarchy(self):
        log.info("Rozpoczynanie budowania hierarchii zależności dla odpowiedzi...")
        if not self.dynamic_form:
            log.error("Nie można zbudować hierarchii - formularz dynamiczny nie istnieje.")
            return None

        all_fields = set(self.dynamic_form.fields_by_path.keys())
        dependencies = defaultdict(set)
        dependents = defaultdict(set)
        
        for target_path, rule_definitions in self.rules.items():
            for rule in rule_definitions.values():
                condition = rule.get("condition")
                if not condition: continue
                
                conditions_to_check = condition.get("conditions", [condition])
                for cond in conditions_to_check:
                    if "field_path" in cond:
                        trigger_path = cond["field_path"]
                        if trigger_path in all_fields:
                            dependencies[target_path].add(trigger_path)
                            dependents[trigger_path].add(target_path)
                            
        levels = []
        in_degree = {field: len(dependencies.get(field, [])) for field in all_fields}
        queue = [field for field, degree in in_degree.items() if degree == 0]
        
        while queue:
            levels.append(sorted(queue))
            next_queue = []
            for u in sorted(queue):
                for v in sorted(list(dependents.get(u, []))):
                    if v in in_degree:
                        in_degree[v] -= 1
                        if in_degree[v] == 0:
                            next_queue.append(v)
            queue = next_queue
        
        remaining_nodes = {node for node, degree in in_degree.items() if degree > 0}
        if remaining_nodes:
            log.error(f"Wykryto cykl w zależnościach reguł! Pola, których nie można było umieścić w hierarchii: {remaining_nodes}")
            return None

        return levels

    def populate_with_test_data(self):
        from services.data_generators import generate_valid_data, reset_address_generation_state
        
        if not self.dynamic_form:
            messagebox.showwarning("Brak formularza", "Formularz nie został zainicjowany.")
            return
        
        log.info("Rozpoczynanie generowania danych dla odpowiedzi R_1.")
        reset_address_generation_state()
        
        self.dynamic_form.clear_generated_data(self.rules)
        self.dynamic_form.rule_engine.apply_all_rules()
        
        hierarchy = self._build_dependency_hierarchy()
        if hierarchy is None:
             messagebox.showerror("Błąd krytyczny", "Wykryto cykl w regułach zależności. Sprawdź pliki JSON z regułami i logi aplikacji.")
             return

        self.dynamic_form.populate_with_data(generate_valid_data, self.rules, hierarchy)
        
        self.status_bar.config(text="Wypełniono formularz odpowiedzi danymi testowymi.")

    def generate_response(self):
        if not self.dynamic_form:
            messagebox.showerror("Błąd", "Formularz odpowiedzi nie został poprawnie zainicjowany.")
            return
        form_data, is_valid = self.dynamic_form.get_values()
        if not is_valid:
            messagebox.showerror("Błąd walidacji", "Formularz zawiera błędy.")
            return
        try:
            root_key = list(form_data.keys())[0]
            if "Header" in form_data[root_key]:
                timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
                form_data[root_key]["Header"]["MessageTimestamp"] = timestamp
                log.info(f"Automatycznie wstawiono/nadpisano MessageTimestamp: {timestamp}")

            nsmap = self.xsd_parser.schema.namespaces.copy()
            if '' in nsmap:
                nsmap[None] = nsmap.pop('')
            if 'xs' in nsmap:
                del nsmap['xs']

            qname_map = {}
            def build_map_recursively(sections):
                for section in sections:
                    qname_map[section.name] = section.qname
                    for field in section.fields:
                        qname_map[field.name] = field.qname
                    build_map_recursively(section.sub_sections)
            
            qname_map[self.root_element_name] = self.xsd_parser.schema.elements[self.root_element_name].name
            build_map_recursively(self.form_sections)
            
            xml_string = self.xml_builder.build(form_data, qname_map, nsmap)
            
            self.view.xml_viewer.show_xml(xml_string)
            
            if not self.xsd_validator:
                raise Exception("Walidator XSD nie został zainicjalizowany.")
            
            is_valid_xsd, error_message = self.xsd_validator.validate(xml_string)
            
            if is_valid_xsd:
                self.status_bar.config(text="Komunikat R_1 wygenerowany i zwalidowany pomyślnie.")
            else:
                self.status_bar.config(text="Błąd walidacji XSD dla R_1.")
                messagebox.showerror("Błąd walidacji XSD", f"Wygenerowany XML nie jest zgodny ze schematem R_1:\n\n{error_message}")
                
        except Exception as e:
            log.error("Błąd podczas budowania XML dla R_1 przez XmlBuilder", exc_info=True)
            messagebox.showerror("Błąd budowania XML", f"Błąd generowania pliku XML:\n\n{e}")

    def save_xml(self):
        xml_content = self.view.xml_viewer.get_content()
        if not xml_content or "Oczekiwanie" in xml_content:
            messagebox.showwarning("Zapis", "Brak komunikatu XML do zapisania.")
            return
        
        file_path_str = filedialog.asksaveasfilename(
            defaultextension=".xml", filetypes=[("Pliki XML", "*.xml")], title="Zapisz komunikat R_1 jako..."
        )
        if file_path_str:
            if write_file(Path(file_path_str), xml_content):
                self.status_bar.config(text=f"Zapisano plik: {file_path_str}")
            else:
                messagebox.showerror("Błąd zapisu", f"Błąd podczas zapisu pliku:\n{file_path_str}")