# csire_message_studio/services/xsd_parser.py

import xmlschema
from collections import namedtuple
from typing import List, Dict, Any, Optional

from infra.logger import get_logger

log = get_logger(__name__)

class FormField:
    def __init__(self, name, qname, path, xsd_type, is_required, is_list,
                 restrictions, documentation, xsd_type_obj, enumerations):
        self.name = name
        self.qname = qname
        self.path = path
        self.xsd_type = xsd_type
        self.is_required = is_required
        self.is_list = is_list
        self.restrictions = restrictions
        self.documentation = documentation
        self.xsd_type_obj = xsd_type_obj
        self.enumerations = enumerations

FormSection = namedtuple('FormSection', [
    'name', 'qname', 'path', 'min_occurs', 'max_occurs', 'fields', 'sub_sections'
])

class XsdParser:
    def __init__(self, xsd_path: str):
        self.schema: Optional[xmlschema.XMLSchema] = None
        try:
            self.schema = xmlschema.XMLSchema(xsd_path, base_url=xsd_path)
            log.info(f"Schemat XSD '{xsd_path}' załadowany pomyślnie.")
            log.info(f"Schemat załadowany. Target Namespace: '{self.schema.target_namespace}'")
            if not self.schema.is_valid:
                raise xmlschema.XMLSchemaParseError("Schemat zawiera błędy lub brakujące importy.")
        except xmlschema.XMLSchemaParseError as e:
            log.error(f"Błąd parsowania schematu XSD: {e}")
            raise ValueError(f"Nie udało się załadować schematu XSD z powodu błędów: {e}") from e
        except Exception as e:
            log.critical(f"Krytyczny błąd podczas ładowania schematu XSD: {xsd_path}", exc_info=True)
            raise ValueError(f"Nie udało się załadować schematu XSD: {e}") from e

    def get_form_structure_for_element(self, element_name: str) -> List[FormSection]:
        if not self.schema: raise ValueError("Schemat XSD nie załadowany.")
        if element_name not in self.schema.elements: raise KeyError(f"Element '{element_name}' nie istnieje w schemacie.")

        root_element = self.schema.elements[element_name]
        log.info(f"Rozpoczynanie parsowania struktury dla elementu głównego: '{element_name}'")
        
        root_section_node = self._build_section_tree_recursive(root_element, path_prefix="")
        
        log.info(f"Zakończono parsowanie struktury dla '{element_name}'.")
        
        return root_section_node.sub_sections if root_section_node else []

    # --- POCZĄTEK OSTATECZNEJ POPRAWKI: Przepisanie logiki parsera ---
    def _build_section_tree_recursive(self, element: xmlschema.XsdElement, path_prefix: str) -> FormSection:
        """
        Rekurencyjnie buduje drzewo sekcji i pól formularza na podstawie elementu XSD,
        używając niezawodnej metody iter_components() do przechodzenia po strukturze.
        """
        current_path = f"{path_prefix}.{element.local_name}" if path_prefix else element.local_name
        log.debug(f"Przetwarzam sekcję: '{current_path}' (Typ: {element.type.local_name})")

        fields_in_this_section: List[FormField] = []
        sub_sections_in_this_section: List[FormSection] = []

        if element.type.is_complex():
            # Używamy iter_components(), aby niezawodnie przejść przez *wszystkie*
            # komponenty (atrybuty, elementy, zagnieżdżone grupy) w poprawnej kolejności.
            for component in element.type.iter_components():
                if isinstance(component, xmlschema.XsdAttribute):
                    fields_in_this_section.append(self._create_form_field_from_attribute(component, current_path))
                
                elif isinstance(component, xmlschema.XsdElement):
                    if not component.type.is_complex() or component.type.has_simple_content():
                        fields_in_this_section.append(self._create_form_field(component, current_path))
                    else:
                        sub_sections_in_this_section.append(self._build_section_tree_recursive(component, current_path))

        return FormSection(
            name=element.local_name,
            qname=element.name,
            path=current_path,
            min_occurs=element.min_occurs,
            max_occurs=element.max_occurs if element.max_occurs != 'unbounded' else None,
            fields=fields_in_this_section,
            sub_sections=sub_sections_in_this_section
        )
    # --- KONIEC OSTATECZNEJ POPRAWKI ---

    def _get_restrictions_and_enums(self, xsd_type: xmlschema.XsdType) -> (Dict[str, Any], List[str]):
        """Zbiera ograniczenia i enumeracje, poprawnie odczytując wzorzec (pattern)."""
        restrictions, enums = {}, []

        if hasattr(xsd_type, 'enumeration') and xsd_type.enumeration is not None:
            enums = list(xsd_type.enumeration)
            
        if hasattr(xsd_type, 'facets'):
            for name, facet in xsd_type.facets.items():
                if name is None or facet is None: continue
                simple_name = name.split('}')[-1]
                
                if simple_name == 'pattern':
                    if hasattr(facet, 'patterns') and isinstance(facet.patterns, list) and facet.patterns:
                        restrictions[simple_name] = facet.patterns[0]
                else:
                    value = getattr(facet, 'value', None)
                    if value is not None:
                        restrictions[simple_name] = value
                        
        return restrictions, enums

    def _create_form_field(self, element: xmlschema.XsdElement, parent_section_path: str) -> FormField:
        is_list = element.max_occurs is None or element.max_occurs > 1
        is_required = element.min_occurs >= 1
        restrictions, enums = self._get_restrictions_and_enums(element.type)
        full_field_path = f"{parent_section_path}.{element.local_name}"
        doc = element.annotation.documentation[0].text.strip() if element.annotation and element.annotation.documentation else ""
        
        log.debug(f" [FIELD CREATED] Tworzenie pola dla elementu: path='{full_field_path}', type='{element.type.local_name}', qname='{element.name}', required={is_required}")
        
        return FormField(
            name=element.local_name,
            qname=element.name,
            path=full_field_path,
            xsd_type=element.type.local_name or "xs:anyType",
            is_required=is_required,
            is_list=is_list,
            restrictions=restrictions,
            documentation=doc,
            xsd_type_obj=element.type,
            enumerations=enums
        )

    def _create_form_field_from_attribute(self, attribute: xmlschema.XsdAttribute, parent_section_path: str) -> FormField:
        is_required = attribute.is_required()
        restrictions, enums = self._get_restrictions_and_enums(attribute.type)
        full_field_path = f"{parent_section_path}.{attribute.local_name}"
        doc = attribute.annotation.documentation[0].text.strip() if attribute.annotation and attribute.annotation.documentation else ""

        log.debug(f" [FIELD CREATED] Tworzenie pola dla atrybutu: path='{full_field_path}', type='{attribute.type.local_name}', qname='{attribute.name}', required={is_required}")

        return FormField(
            name=attribute.local_name,
            qname=attribute.name,
            path=full_field_path,
            xsd_type=attribute.type.local_name or "xs:anyType",
            is_required=is_required,
            is_list=False,
            restrictions=restrictions,
            documentation=doc,
            xsd_type_obj=attribute.type,
            enumerations=enums
        )