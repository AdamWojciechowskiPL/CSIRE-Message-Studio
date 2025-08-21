# csire_message_studio/services/converters.py
import json
import base64
from typing import Dict, Any, Optional
from lxml import etree

from infra.logger import get_logger

log = get_logger(__name__)

def json_to_xml(json_data: Dict[str, Any]) -> str:
    """
    Konwertuje dane w formacie JSON (słownik Python) na XML.
    Ta funkcjonalność może być potrzebna przy imporcie.

    Args:
        json_data: Słownik z danymi.

    Returns:
        Ciąg znaków XML.
    """
    log.warning("Funkcja 'json_to_xml' nie jest jeszcze zaimplementowana.")
    raise NotImplementedError("Konwersja z JSON do XML nie została jeszcze zaimplementowana.")


def extract_from_luxhub_envelope(envelope: Dict[str, Any]) -> str:
    """
    Wydobywa i dekoduje właściwy komunikat XML z "koperty" w formacie JSON
    zgodnym ze standardem LUXhub (payload zakodowany w Base64).
    """
    log.info("Próba ekstrakcji XML z koperty LUXhub.")
    if "payload" not in envelope:
        log.error("Brak klucza 'payload' w dostarczonej kopercie.")
        raise KeyError("Koperta nie zawiera klucza 'payload'.")

    base64_payload = envelope["payload"]
    try:
        decoded_payload_bytes = base64.b64decode(base64_payload)
        xml_string = decoded_payload_bytes.decode('utf-8')
        log.info("Pomyślnie zdekodowano payload z Base64.")
        return xml_string
    except Exception as e:
        log.error("Nie udało się zdekodować payloadu z Base64.", exc_info=True)
        raise ValueError(f"Błąd podczas dekodowania payloadu: {e}") from e


def extract_ids_from_json_envelope(json_string: str) -> Dict[str, Optional[str]]:
    """
    Parsuje plik JSON, aby wyodrębnić identyfikatory potrzebne do odpowiedzi,
    zgodnie ze zdefiniowaną logiką biznesową.

    Args:
        json_string: Zawartość pliku JSON jako ciąg znaków.

    Returns:
        Słownik z kluczami 'message_id', 'business_process' i 'metering_point_code'.
    """
    log.info("Próba ekstrakcji identyfikatorów z pliku JSON na potrzeby odpowiedzi.")
    try:
        envelope = json.loads(json_string)
        
        message_id = None
        business_process = None
        metering_point_code = None

        if "payload" in envelope: # Scenariusz 1: Koperta LUXhub
            log.info("Wykryto format koperty z kluczem 'payload'. Przetwarzanie XML...")
            xml_bytes = base64.b64decode(envelope["payload"])
            imported_root = etree.fromstring(xml_bytes)
            
            message_id = imported_root.findtext('.//{*}Header/{*}MessageId')
            business_process = imported_root.findtext('.//{*}ProcessEnergyContext/{*}BusinessProcess')
            metering_point_code = imported_root.findtext('.//{*}MeteringPointData_Basic/{*}MeteringPointCode')

            log.info(f"Znaleziono w kopercie XML: MessageId='{message_id}', BusinessProcess='{business_process}', MeteringPointCode='{metering_point_code}'")

        else: # Scenariusz 2: Surowy JSON
            log.info("Wykryto format surowego JSON. Stosowanie nowej logiki.")
            
            message_id = envelope.get("CsireMessageId")
            if not message_id:
                log.warning("Nie znaleziono klucza 'CsireMessageId'. Pole SenderMessageId nie zostanie ustawione.")

            process_type = envelope.get("ProcessType")
            if process_type and isinstance(process_type, str):
                parts = process_type.strip('.').split('.')
                if len(parts) >= 2:
                    business_process = f"{parts[0]}.{parts[1]}."
                    log.info(f"Wyderowano 'BusinessProcess' ({business_process}) z 'ProcessType' ({process_type}).")
                else:
                    log.warning(f"Nie udało się wyderować BusinessProcess z ProcessType: '{process_type}'. Zbyt mało części.")
            else:
                log.warning("Nie znaleziono klucza 'ProcessType' lub ma on nieprawidłowy format. Pole BusinessProcess nie zostanie ustawione.")

            # --- NOWA LOGIKA: Bezpieczne pobieranie MeteringPointCode ---
            metering_point_code = envelope.get("Body", {}).get("MeteringPointData", {}).get("MeteringPointCode")
            if not metering_point_code:
                log.warning("Nie znaleziono 'MeteringPointCode' w ścieżce Body.MeteringPointData.MeteringPointCode.")

        return {
            "message_id": message_id, 
            "business_process": business_process,
            "metering_point_code": metering_point_code
        }

    except json.JSONDecodeError as e:
        log.error("Błąd parsowania pliku JSON.", exc_info=True)
        raise ValueError(f"Plik nie jest poprawnym formatem JSON: {e}") from e
    except Exception as e:
        log.error("Nieoczekiwany błąd podczas ekstrakcji ID z pliku JSON.", exc_info=True)
        raise ValueError(f"Błąd przetwarzania pliku JSON: {e}") from e