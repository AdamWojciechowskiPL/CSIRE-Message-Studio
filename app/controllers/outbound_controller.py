# csire_message_studio/app/controllers/outbound_controller.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import json
from collections import defaultdict
import datetime
from services.xsd_parser import XsdParser
from services.xml_builder import XmlBuilder
from domain.validation.xsd_validator import XsdValidator
from infra import config
from infra.logger import get_logger
from app.views.widgets.dynamic_form import DynamicForm
from services.data_generators import generate_valid_data, reset_address_generation_state
from infra.file_handler import write_file
from services.preset_manager import PresetManager

log = get_logger(__name__)

class OutboundController:
    def __init__(self, view, status_bar):
        self.view = view
        self.status_bar = status_bar
        self.dynamic_form = None
        self.xml_builder = XmlBuilder()
        self.preset_manager = PresetManager()
        self.xsd_parser = None
        self.xsd_validator = None
        self.form_sections_definitions = None
        
        self.current_message_code = None
        self.rules = {}

        self._setup_process_selection()
        self._bind_events()

    def _setup_process_selection(self):
        processes = list(config.SUPPORTED_PROCESSES.keys())
        self.view.process_combobox['values'] = processes
        if processes:
            self.view.process_combobox.current(0)
            self._on_process_selected()

    def _bind_events(self):
        self.view.process_combobox.bind("<<ComboboxSelected>>", self._on_process_selected)
        self.view.message_type_combobox.bind("<<ComboboxSelected>>", self._on_message_selected)
        self.view.build_form_button.config(command=self.build_form_from_selection)
        self.view.generate_button.config(command=self.generate_xml)
        self.view.populate_button.config(command=self.populate_with_test_data)
        self.view.save_button.config(command=self.save_xml)
        
        self.view.preset_combobox.bind("<<ComboboxSelected>>", self._on_preset_selected)
        self.view.save_preset_button.config(command=self._save_preset)
        self.view.rename_preset_button.config(command=self._rename_preset)
        self.view.delete_preset_button.config(command=self._delete_preset)

    def _on_process_selected(self, event=None):
        selected_process = self.view.process_combobox.get()
        messages = config.SUPPORTED_PROCESSES.get(selected_process, {}).get("messages", {})
        message_names = list(messages.keys())
        self.view.message_type_combobox['values'] = message_names
        self.view.message_type_combobox.set('')
        if message_names:
            self.view.message_type_combobox.config(state="readonly")
            self.view.message_type_combobox.current(0)
            self._on_message_selected()
        else:
            self.view.message_type_combobox.config(state="disabled")
            self.view.rules_combobox.config(state="disabled")
            self.view.rules_combobox.set('')
            self.current_message_code = None
            self._load_and_display_presets()

    def _on_message_selected(self, event=None):
        process_name = self.view.process_combobox.get()
        message_name = self.view.message_type_combobox.get()
        if process_name and message_name:
            try:
                message_info = config.SUPPORTED_PROCESSES[process_name]["messages"][message_name]
                self.current_message_code = message_info.get("type_code")
                self._load_and_display_rules() # Ładujemy reguły dla wybranego komunikatu
            except KeyError:
                self.current_message_code = None
                self._load_and_display_rules() # Czyścimy listę reguł
        else:
            self.current_message_code = None
            self._load_and_display_rules() # Czyścimy listę reguł
        
        if self.dynamic_form:
            self._load_and_display_presets()
            
    def _load_and_display_rules(self):
        process_name = self.view.process_combobox.get()
        message_name = self.view.message_type_combobox.get()
        
        rules_list = []
        if process_name and message_name:
            try:
                message_info = config.SUPPORTED_PROCESSES[process_name]["messages"][message_name]
                rules_dir_name = message_info.get("rules_dir_name")
                if rules_dir_name:
                    rules_dir = config.MESSAGE_RULES_DIR / rules_dir_name
                    if rules_dir.is_dir():
                        rules_list = sorted([p.stem for p in rules_dir.glob('*.json')])
                        log.info(f"Znaleziono {len(rules_list)} zestawów reguł w katalogu '{rules_dir_name}'.")
            except (KeyError, FileNotFoundError):
                log.warning("Nie znaleziono katalogu z regułami dla wybranego komunikatu.")
        
        self.view.rules_combobox['values'] = rules_list
        if rules_list:
            self.view.rules_combobox.config(state="readonly")
            self.view.rules_combobox.current(0)
        else:
            self.view.rules_combobox.config(state="disabled")
            self.view.rules_combobox.set('')

    def build_form_from_selection(self):
        if not self.current_message_code:
            messagebox.showwarning("Brak wyboru", "Proszę wybrać proces biznesowy i typ komunikatu.")
            return

        selected_rule_set = self.view.rules_combobox.get()
        if not selected_rule_set:
            messagebox.showwarning("Brak reguł", "Nie wybrano zestawu reguł do zbudowania formularza.")
            return

        try:
            process_info = config.SUPPORTED_PROCESSES[self.view.process_combobox.get()]
            message_info = process_info["messages"][self.view.message_type_combobox.get()]
            xsd_path = config.XSD_OUTBOUND_DIR / message_info["xsd_file"]
            
            self.rules = {}
            rules_dir_name = message_info.get("rules_dir_name")
            if rules_dir_name:
                rules_path = config.MESSAGE_RULES_DIR / rules_dir_name / f"{selected_rule_set}.json"
                if rules_path.exists():
                    with open(rules_path, 'r', encoding='utf-8') as f:
                        self.rules = json.load(f).get("rules", {})
                    log.info(f"Pomyślnie załadowano {len(self.rules)} reguł z pliku {rules_path.name}")
                else:
                    log.warning(f"Plik reguł '{rules_path.name}' nie istnieje.")
            
            self.xsd_parser = XsdParser(str(xsd_path))
            self.xsd_validator = XsdValidator(self.xsd_parser.schema)
            
            element_to_parse = list(self.xsd_parser.schema.elements.keys())[0]
            self.form_sections_definitions = self.xsd_parser.get_form_structure_for_element(element_to_parse)
            
            if self.dynamic_form: self.dynamic_form.destroy()
            
            self.dynamic_form = DynamicForm(
                self.view.form_container, 
                self.form_sections_definitions, 
                rules=self.rules, 
                process_info=process_info, 
                message_info=message_info
            )
            self.dynamic_form.pack(fill="both", expand=True, padx=5, pady=5)

            timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
            self.dynamic_form.set_field_value_by_name("MessageTimestamp", timestamp)
            log.info(f"Automatycznie ustawiono MessageTimestamp w formularzu: {timestamp}")
            
            self._load_and_display_presets()
            
            self.status_bar.config(text=f"Zbudowano formularz dla '{self.view.message_type_combobox.get()}' używając reguł '{selected_rule_set}'.")
        except Exception as e:
            log.error(f"Błąd podczas budowania formularza: {e}", exc_info=True)
            messagebox.showerror("Błąd budowania formularza", f"Wystąpił nieoczekiwany błąd:\n\n{e}")

    def _build_dependency_hierarchy(self):
        log.info("Rozpoczynanie budowania hierarchii zależności...")
        all_fields = set(self.dynamic_form.fields_by_path.keys())
        dependencies = defaultdict(set)
        dependents = defaultdict(set)
        
        for target_path, rule_definitions in self.rules.items():
            for rule in rule_definitions.values():
                condition = rule.get("condition")
                if not condition: continue
                
                conditions = condition.get("conditions", [condition])
                for cond in conditions:
                    if "field_path" in cond:
                        trigger_path = cond["field_path"]
                        if trigger_path in all_fields:
                            dependencies[target_path].add(trigger_path)
                            dependents[trigger_path].add(target_path)
                            
        levels = []
        in_degree = {field: 0 for field in all_fields}
        for target_path, deps in dependencies.items():
            if target_path in in_degree:
                in_degree[target_path] = len(deps)
        
        queue = [field for field, degree in in_degree.items() if degree == 0]
        
        while queue:
            levels.append(queue)
            next_queue = []
            for u in sorted(queue):
                for v in sorted(list(dependents[u])):
                    if v in in_degree:
                        in_degree[v] -= 1
                        if in_degree[v] == 0:
                            next_queue.append(v)
            queue = sorted(next_queue)
        
        remaining_nodes = {node: degree for node, degree in in_degree.items() if degree > 0}
        if remaining_nodes:
            log.error(f"Wykryto cykl w zależnościach reguł! Pola, których nie można było umieścić w hierarchii: {remaining_nodes}")
            log.error("--- DIAGNOSTYKA CYKLU ---")
            for node in remaining_nodes:
                log.error(f"  -> Pole '{node}' nadal czeka na: {dependencies.get(node)}")
            log.error("--------------------------")
            return None

        return levels

    def populate_with_test_data(self):
        if not self.dynamic_form:
            messagebox.showwarning("Brak formularza", "Najpierw zbuduj formularz.")
            return
        
        log.info("Rozpoczynanie hierarchicznego generowania danych.")
        reset_address_generation_state()
        
        self.dynamic_form.clear_generated_data(self.rules)
        self.dynamic_form.rule_engine.apply_all_rules()
        
        hierarchy = self._build_dependency_hierarchy()
        if hierarchy is None:
             messagebox.showerror("Błąd krytyczny", "Wykryto cykl w regułach zależności. Sprawdź pliki JSON z regułami i logi aplikacji.")
             return
             
        self.dynamic_form.populate_with_data(generate_valid_data, self.rules, hierarchy)
        
    def generate_xml(self):
        if not self.dynamic_form or not self.xsd_parser:
            messagebox.showwarning("Brak formularza", "Najpierw zbuduj formularz.")
            return
        
        form_data, is_valid = self.dynamic_form.get_values()
        
        if not is_valid:
            messagebox.showerror("Błąd walidacji", "Formularz zawiera błędy. Popraw podświetlone pola.")
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
            
            root_element_name = list(form_data.keys())[0]
            root_qname = self.xsd_parser.schema.elements[root_element_name].name
            qname_map[root_element_name] = root_qname
            build_map_recursively(self.form_sections_definitions)
            
            xml_string = self.xml_builder.build(form_data, qname_map, nsmap)
            
            self.view.xml_viewer.show_xml(xml_string)
            
            if not self.xsd_validator:
                raise Exception("Walidator XSD nie został zainicjalizowany.")

            is_valid_xsd, error_message = self.xsd_validator.validate(xml_string)
            
            if is_valid_xsd:
                self.status_bar.config(text="Pomyślnie wygenerowano i zwalidowano XML.")
            else:
                self.status_bar.config(text="Błąd walidacji XSD. Sprawdź szczegóły w oknie błędu.")
                messagebox.showerror("Błąd walidacji XSD", f"Wygenerowany XML nie jest zgodny ze schematem:\n\n{error_message}")

        except Exception as e:
            log.error(f"Błąd podczas generowania XML: {e}", exc_info=True)
            messagebox.showerror("Błąd generowania XML", f"Wystąpił błąd podczas budowania XML:\n\n{e}")

    def save_xml(self):
        xml_content = self.view.xml_viewer.get_content()
        if not xml_content or "Wybierz proces" in xml_content:
            messagebox.showwarning("Zapis", "Brak komunikatu XML do zapisania. Najpierw wygeneruj komunikat.")
            return
        
        file_path_str = filedialog.asksaveasfilename(
            defaultextension=".xml", filetypes=[("Pliki XML", "*.xml")], title="Zapisz komunikat jako..."
        )
        if file_path_str:
            if write_file(Path(file_path_str), xml_content):
                self.status_bar.config(text=f"Zapisano plik: {file_path_str}")
            else:
                messagebox.showerror("Błąd zapisu", f"Błąd podczas zapisu pliku:\n{file_path_str}")
        
    def _load_and_display_presets(self):
        if not self.current_message_code:
            self.view.preset_combobox.set('')
            self.view.preset_combobox['values'] = []
            self.view.preset_combobox.config(state="disabled")
            return

        presets = self.preset_manager.get_presets_for_message(self.current_message_code)
        self.view.preset_combobox['values'] = presets
        self.view.preset_combobox.set('')
        if presets:
            self.view.preset_combobox.config(state="readonly")
        else:
            self.view.preset_combobox.config(state="disabled")
    
    def _on_preset_selected(self, event=None):
        preset_name = self.view.preset_combobox.get()
        if not self.dynamic_form or not preset_name or not self.current_message_code:
            return
            
        preset_data = self.preset_manager.load_preset(self.current_message_code, preset_name)
        if not preset_data:
            messagebox.showerror("Błąd", f"Nie udało się wczytać danych dla presetu '{preset_name}'.")
            return
            
        self.dynamic_form.populate_from_dict(preset_data)
        
        timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
        self.dynamic_form.set_field_value_by_name("MessageTimestamp", timestamp)
        log.info(f"Automatycznie ustawiono MessageTimestamp po załadowaniu presetu: {timestamp}")
        
        self.status_bar.config(text=f"Załadowano preset: {preset_name}")
        log.info(f"Formularz wypełniony danymi z presetu '{preset_name}'.")

    def _save_preset(self):
        if not self.dynamic_form or not self.current_message_code:
            messagebox.showwarning("Zapis presetu", "Najpierw zbuduj formularz.")
            return

        preset_name = simpledialog.askstring("Zapisz preset", "Podaj nazwę dla presetu:", parent=self.view)
        if not preset_name or not preset_name.strip():
            return
            
        preset_name = preset_name.strip()
        
        data, is_valid = self.dynamic_form.get_values()
        if not is_valid:
            messagebox.showerror("Błąd walidacji", "Formularz zawiera błędy i nie może zostać zapisany jako preset.")
            return
            
        root_key = list(data.keys())[0]
        form_data = data[root_key]
        
        if "Header" in form_data and "MessageTimestamp" in form_data["Header"]:
            del form_data["Header"]["MessageTimestamp"]
            
        if self.preset_manager.save_preset(self.current_message_code, preset_name, form_data):
            self.status_bar.config(text=f"Zapisano preset: {preset_name}")
            self._load_and_display_presets()
            self.view.preset_combobox.set(preset_name)
        else:
            messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać presetu '{preset_name}'.")

    def _delete_preset(self):
        preset_name = self.view.preset_combobox.get()
        if not preset_name or not self.current_message_code:
            messagebox.showwarning("Usuwanie presetu", "Wybierz preset do usunięcia.")
            return

        if messagebox.askyesno("Potwierdzenie", f"Czy na pewno chcesz usunąć preset '{preset_name}'?"):
            if self.preset_manager.delete_preset(self.current_message_code, preset_name):
                self.status_bar.config(text=f"Usunięto preset: {preset_name}")
                self._load_and_display_presets()
            else:
                messagebox.showerror("Błąd", f"Nie udało się usunąć presetu '{preset_name}'.")
    
    def _rename_preset(self):
        old_name = self.view.preset_combobox.get()
        if not old_name or not self.current_message_code:
            messagebox.showwarning("Zmiana nazwy", "Wybierz preset, którego nazwę chcesz zmienić.")
            return

        new_name = simpledialog.askstring("Zmiana nazwy", "Podaj nową nazwę dla presetu:", initialvalue=old_name, parent=self.view)
        if not new_name or not new_name.strip() or new_name.strip() == old_name:
            return
            
        new_name = new_name.strip()

        if self.preset_manager.rename_preset(self.current_message_code, old_name, new_name):
            self.status_bar.config(text=f"Zmieniono nazwę presetu na: {new_name}")
            self._load_and_display_presets()
            self.view.preset_combobox.set(new_name)
        else:
            messagebox.showerror("Błąd", f"Nie udało się zmienić nazwy presetu. Być może nazwa '{new_name}' już istnieje.")