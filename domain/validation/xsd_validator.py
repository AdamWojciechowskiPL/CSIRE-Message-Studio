# csire_message_studio/domain/validation/xsd_validator.py
from typing import Optional, Tuple
import xmlschema

from infra.logger import get_logger

log = get_logger(__name__)

class XsdValidator:
    """
    Enkapsuluje logikę walidacji dokumentu XML względem schematu XSD.
    """
    def __init__(self, schema: xmlschema.XMLSchema):
        """
        Inicjalizuje walidator z załadowanym wcześniej obiektem schematu.

        Args:
            schema: Obiekt schematu z biblioteki xmlschema.
        """
        if not isinstance(schema, xmlschema.XMLSchema):
            raise TypeError("Argument 'schema' musi być instancją xmlschema.XMLSchema")
        self.schema = schema
        log.debug(f"XsdValidator zainicjowany ze schematem: {schema.filepath or 'ze źródła w pamięci'}")

    def validate(self, xml_string: str) -> Tuple[bool, Optional[str]]:
        """
        Waliduje podany ciąg XML względem załadowanego schematu.

        Args:
            xml_string: Dokument XML do walidacji jako ciąg znaków.

        Returns:
            Krotka (is_valid, error_message), gdzie:
            - is_valid (bool): True, jeśli dokument jest poprawny, False w przeciwnym razie.
            - error_message (str | None): Komunikat błędu, jeśli walidacja się nie powiodła,
              w przeciwnym razie None.
        """
        try:
            self.schema.validate(xml_string)
            log.info("Walidacja XML względem schematu XSD zakończona pomyślnie.")
            return True, None
        except xmlschema.XMLSchemaValidationError as e:
            log.warning(f"Walidacja XML nie powiodła się. Powód: {e.reason}", exc_info=False)
            
            # --- POPRAWKA: Uodpornienie na brak atrybutów 'line' i 'column' ---
            if hasattr(e, 'line') and e.line is not None:
                location_info = f"Błąd w linii {e.line}, kolumnie {e.column}:"
            else:
                location_info = "Błąd walidacji:"

            error_message = f"{location_info}\n{e.reason}\nŚcieżka: {e.path}"
            return False, error_message
            # --- KONIEC POPRAWKI ---
            
        except Exception as e:
            log.error("Wystąpił nieoczekiwany błąd podczas walidacji XML.", exc_info=True)
            return False, f"Błąd krytyczny podczas walidacji: {e}"