# csire_message_studio/services/xml_builder.py
from lxml import etree
from typing import Dict, Any, Optional

from infra.logger import get_logger

log = get_logger(__name__)

class XmlBuilder:
    """
    Buduje dokument XML na podstawie zagnieżdżonego słownika Python,
    poprawnie obsługując złożone przestrzenie nazw (namespaces).
    """
    def build(self, data: Dict[str, Any], qname_map: Dict[str, str], nsmap: Dict[str, str]) -> str:
        """
        Główna metoda budująca XML.

        Args:
            data: Słownik z danymi (klucze to nazwy lokalne).
            qname_map: Mapa z {nazwa_lokalna: pełna_nazwa_kwalifikowana}.
            nsmap: Mapa z {prefix: URI_przestrzeni_nazw}.

        Returns:
            Sformatowany ciąg znaków XML.
        """
        if not data or len(data) != 1:
            msg = "Dane wejściowe dla XmlBuilder muszą być słownikiem z jednym kluczem głównym."
            log.error(msg)
            raise ValueError(msg)

        root_name = list(data.keys())[0]
        root_data = data[root_name]
        
        log.debug(f"Rozpoczynanie budowania XML dla elementu głównego: '{root_name}'")
        
        root_qname = qname_map.get(root_name)
        if not root_qname:
            raise ValueError(f"Nie znaleziono kwalifikowanej nazwy dla elementu głównego '{root_name}'")
        
        root_element = etree.Element(root_qname, nsmap=nsmap)
        self._build_recursive(root_element, root_data, qname_map)

        xml_string = etree.tostring(
            root_element,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        ).decode('utf-8')
        
        log.info(f"Pomyślnie zbudowano dokument XML dla '{root_name}'.")
        return xml_string

    def _build_recursive(self, parent_element: etree.Element, data: Any, qname_map: Dict[str, str]):
        """
        Rekurencyjnie buduje drzewo XML.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                qname = qname_map.get(key)
                if not qname:
                    log.warning(f"Nie znaleziono QName dla klucza '{key}', używam nazwy lokalnej. Może to prowadzić do błędów walidacji.")
                    qname = key
                
                if isinstance(value, list):
                    for item in value:
                        child_element = etree.SubElement(parent_element, qname)
                        self._build_recursive(child_element, item, qname_map)
                else:
                    child_element = etree.SubElement(parent_element, qname)
                    self._build_recursive(child_element, value, qname_map)
        elif data is not None:
            parent_element.text = str(data)