# csire_message_studio/app/views/widgets/dynamic_form_components/form_renderer.py
import tkinter as tk
from tkinter import ttk
from infra.logger import get_logger

log = get_logger(__name__)

class FormRenderer:
    """Odpowiada za budowanie interfejsu graficznego formularza."""

    def __init__(self, form_facade, rules):
        self.form = form_facade
        self.rules = rules
        self.vcmd = (self.form.register(self.form.data_handler._validate_entry), '%P', '%W')
        self.list_control_vars = {} 

    def _is_controlled_by_rule(self, section_path: str) -> bool:
        """Sprawdza, czy sekcja jest kontrolowana przez regułę widoczności lub wymagalności."""
        if section_path in self.rules:
            for rule_definitions in self.rules[section_path].values():
                action = rule_definitions.get("action", "")
                if action in ("show_if_value", "require_if_value", "forbid_if_value", "hide"):
                    return True
        return False

    def render(self):
        log.info("Rozpoczynanie renderowania formularza dynamicznego...")
        for section_def in self.form.form_sections_definitions:
            self._render_section_recursively(self.form.scrollable_frame, section_def, 0, None)
        log.info("Zakończono renderowanie formularza dynamicznego.")

    def _render_section_recursively(self, parent_widget, section_def, depth, parent_instance):
        is_controlled = self._is_controlled_by_rule(section_def.path)
        is_optional = section_def.min_occurs == 0

        if is_optional and not is_controlled:
            header_frame = ttk.Frame(parent_widget, style="Section.TFrame", padding=(depth * 20, 5, 0, 5))
            header_frame.pack(fill=tk.X, anchor="n")
            
            check_var = tk.BooleanVar(value=True)
            self.list_control_vars[section_def.path] = check_var
            check = ttk.Checkbutton(header_frame, text=section_def.name, variable=check_var, style="Optional.TCheckbutton")
            check.pack(side=tk.LEFT)
            
            instance_container = ttk.Frame(parent_widget)
            instance_container.pack(fill=tk.X, anchor="n", after=header_frame)

            def toggle_visibility(*args):
                if check_var.get():
                    instance_container.pack(fill=tk.X, anchor="n", after=header_frame)
                    if not self.form.rendered_sections.get(section_def.path):
                        self.add_section_instance(instance_container, section_def, 0, True, parent_instance, header_frame=header_frame)
                else:
                    for instance in list(self.form.rendered_sections.get(section_def.path, [])):
                        self._remove_section_instance(instance, update_buttons=False)
                    instance_container.pack_forget()

            check_var.trace_add("write", toggle_visibility)
            self.add_section_instance(instance_container, section_def, 0, True, parent_instance, header_frame=header_frame)
            self.form.bind_scroll_recursively(header_frame)

        else:
            num_to_render = section_def.min_occurs if not is_controlled else 1
            is_initially_enabled = not is_controlled

            for _ in range(num_to_render):
                self.add_section_instance(parent_widget, section_def, depth, is_initially_enabled, parent_instance)

    def add_section_instance(self, parent_widget, section_def, depth, is_initially_enabled, parent_instance, after_instance=None, header_frame=None):
        instance_idx = len(self.form.rendered_sections.get(section_def.path, []))
        log.debug(f"[RENDER] Tworzenie instancji {instance_idx} dla sekcji '{section_def.path}'")
        
        container = ttk.Frame(parent_widget, style="Section.TFrame")

        is_optional_list = section_def.min_occurs == 0 and not self._is_controlled_by_rule(section_def.path)
        if not is_optional_list:
             container.config(padding=(depth * 20, 5, 0, 5))

        if after_instance:
            container.pack(fill=tk.X, anchor="n", after=after_instance['container'])
        else:
            container.pack(fill=tk.X, anchor="n")

        header = ttk.Frame(container, style="Header.TFrame")
        header.pack(fill=tk.X)
        content = ttk.Labelframe(container, style="Content.TLabelframe", padding=10)
        check_var = tk.BooleanVar(value=is_initially_enabled)
        is_list = section_def.max_occurs is None or section_def.max_occurs > 1
        
        label_text = section_def.name
        if is_list and not is_optional_list:
            label_text = f"{section_def.name} [{instance_idx + 1}]"

        ttk.Label(header, text=label_text, style="Section.TLabel").pack(side=tk.LEFT)

        instance_data = {
            'container': container, 'content': content, 'check_var': check_var,
            'widgets': {}, 'section_def': section_def, 'parent_instance': parent_instance,
            'add_button': None, 'remove_button': None, '_allow_multiple': True,
            'header_frame': header_frame
        }

        if is_list and not is_optional_list:
            add_button = ttk.Button(header, text="+", width=2, command=lambda p=parent_widget, sd=section_def, d=depth, pi=parent_instance, current_instance=instance_data: self.add_section_instance(p, sd, d, True, pi, after_instance=current_instance))
            instance_data['add_button'] = add_button
            remove_button = ttk.Button(header, text="-", width=2, command=lambda i_data=instance_data: self._remove_section_instance(i_data))
            instance_data['remove_button'] = remove_button

        for field_def in section_def.fields:
            indexed_path = f"{field_def.path}[{instance_idx}]"
            field_widgets = self._create_field_row(content, field_def, indexed_path)
            instance_data['widgets'][field_def.path] = field_widgets
        
        for sub_section_def in section_def.sub_sections:
            self._render_section_recursively(content, sub_section_def, depth + 1, parent_instance=instance_data)
            
        self.form.rendered_sections[section_def.path].append(instance_data)
        if not is_optional_list:
            check_var.trace_add("write", lambda *args, i=instance_data: self._toggle_section_state(i))
        
        self._toggle_section_state(instance_data, is_initial_call=True)
        self.form.bind_scroll_recursively(container)

    def _remove_section_instance(self, instance_data, update_buttons=True):
        section_path = instance_data['section_def'].path
        log.debug(f"[RENDER] Rozpoczynanie usuwania instancji sekcji '{section_path}'")

        if instance_data not in self.form.rendered_sections.get(section_path, []):
            log.warning(f"Próba usunięcia instancji sekcji, której nie ma na liście: {section_path}")
            return

        for field_path in instance_data['widgets'].keys():
            instance_idx = self.form.rendered_sections[section_path].index(instance_data)
            indexed_path = f"{field_path}[{instance_idx}]"
            if indexed_path in self.form.widget_groups:
                del self.form.widget_groups[indexed_path]

        instance_data['container'].destroy()
        self.form.rendered_sections[section_path].remove(instance_data)
        log.debug(f"[RENDER] Pomyślnie usunięto instancję sekcji '{section_path}'.")
        
        if update_buttons:
            self._update_section_buttons(section_path)
        
        if not self.form.rendered_sections.get(section_path):
            if section_path in self.list_control_vars:
                log.debug(f"Ostatnia instancja '{section_path}' usunięta, odznaczam główny checkbox.")
                self.list_control_vars[section_path].set(False)

    def toggle_multiplicity_controls(self, section_path: str, allow_multiple: bool):
        instances = self.form.rendered_sections.get(section_path, [])
        if not instances: return
        
        log.debug(f"RENDERER: Zmieniam allow_multiple na {allow_multiple} dla sekcji {section_path}")
        for instance in instances:
            instance['_allow_multiple'] = allow_multiple
        self._update_section_buttons(section_path)

    def _update_section_buttons(self, section_path: str):
        instances = self.form.rendered_sections.get(section_path, [])
        if not instances: return

        section_def = instances[0]['section_def']
        if section_def.min_occurs == 0 and not self._is_controlled_by_rule(section_path):
            return

        num_instances = len(instances)
        allow_multiple = instances[-1].get('_allow_multiple', True)
        
        is_visibility_forced_by_rule = self._is_controlled_by_rule(section_path) and any(inst['check_var'].get() for inst in instances)
        
        should_show_remove = (num_instances > section_def.min_occurs) and allow_multiple
        if is_visibility_forced_by_rule and num_instances == 1:
            should_show_remove = False

        should_show_add = (section_def.max_occurs is None or num_instances < section_def.max_occurs) and allow_multiple

        for i, instance in enumerate(instances):
            is_last_instance = (i == num_instances - 1)
            add_btn = instance.get('add_button')
            rem_btn = instance.get('remove_button')

            if rem_btn:
                if should_show_remove: rem_btn.pack(side=tk.RIGHT)
                else: rem_btn.pack_forget()
            
            if add_btn:
                if is_last_instance and should_show_add: add_btn.pack(side=tk.RIGHT, padx=(2,0))
                else: add_btn.pack_forget()

    def _set_children_state_disabled(self, parent_widget):
        for child in parent_widget.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Combobox)):
                child.config(state='disabled')
            elif isinstance(child, (ttk.Frame, ttk.Labelframe)):
                self._set_children_state_disabled(child)

    def _restore_children_default_state(self, parent_widget):
        for child in parent_widget.winfo_children():
            if isinstance(child, ttk.Combobox):
                child.config(state='readonly')
            elif isinstance(child, ttk.Entry):
                child.config(state='normal')
            elif isinstance(child, (ttk.Frame, ttk.Labelframe)):
                self._restore_children_default_state(child)

    def _toggle_section_state(self, instance_data, is_initial_call=False):
        is_enabled = instance_data['check_var'].get()
        section_path = instance_data['section_def'].path
        
        if not is_initial_call:
            log.debug(f"[RENDER] Przełączanie stanu sekcji '{section_path}' na Włączony={is_enabled}")

        if is_enabled:
            instance_data['content'].pack(fill=tk.X, padx=10, pady=(0, 5))
            self._restore_children_default_state(instance_data['content'])
        else:
            instance_data['content'].pack_forget()
            self._set_children_state_disabled(instance_data['content'])
        
        self._update_section_buttons(section_path)
        self.form.update_idletasks()

    def _create_field_row(self, parent, field_def, indexed_path):
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=3, padx=5)
        label_text = f"{field_def.name}{' *' if field_def.is_required else ''}"
        label = ttk.Label(row_frame, text=label_text, width=25, anchor="w")
        label.pack(side=tk.LEFT, padx=(0, 5))
        field_def.label_widget = label

        fields_container = ttk.Frame(row_frame)
        fields_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
        created_widgets = []
        
        def add_field_gui_instance():
            widget = self._add_field_instance(fields_container, field_def, indexed_path)
            created_widgets.append(widget)

        add_field_gui_instance()

        if field_def.is_list:
            ttk.Button(row_frame, text="+", width=2, command=add_field_gui_instance).pack(side=tk.LEFT, padx=5)

        for widget in created_widgets:
            widget.row_frame = row_frame

        return created_widgets

    def _add_field_instance(self, parent, field_def, indexed_path):
        instance_frame = ttk.Frame(parent)
        instance_frame.pack(fill=tk.X, pady=(0, 2))

        if (field_def.xsd_type or "").lower() == 'boolean':
            widget = ttk.Combobox(instance_frame, values=['', 'true', 'false'], state="readonly")
        elif field_def.enumerations:
            widget = ttk.Combobox(instance_frame, values=[''] + field_def.enumerations, state="readonly")
        else:
            widget = ttk.Entry(instance_frame, validate="focusout", validatecommand=self.vcmd)
        
        widget.pack(side=tk.LEFT, expand=True, fill=tk.X)
        error_label = ttk.Label(instance_frame, text="", style="Error.TLabel", wraplength=250, justify=tk.LEFT)
        error_label.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        widget.error_label = error_label

        if not isinstance(indexed_path, str):
            log.critical(f"KRYTYCZNY BŁĄD RENDEROWANIA: Próba użycia klucza innego niż string dla widget_groups! Typ: {type(indexed_path)}, Wartość: {indexed_path}")
            return widget

        self.form.widget_groups[indexed_path].append(widget)

        callback = lambda event, p=field_def.path: self.form.rule_engine.evaluate_rules_for_trigger(p)
        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", callback)
        else:
            widget.bind("<FocusOut>", callback)
            widget.bind("<Return>", callback)
            
        return widget