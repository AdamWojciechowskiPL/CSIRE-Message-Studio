# csire_message_studio/domain/dictionaries/operator_registry.py
import csv
import random
from typing import List, Dict, Optional

from infra.logger import get_logger

log = get_logger(__name__)

class OperatorRegistry:
    """
    Zarządza słownikiem operatorów (kody EIC) wczytywanych z pliku CSV.
    Jest odporny na różne kodowania plików (UTF-8 i Windows-1250).
    """
    def __init__(self, csv_path: str):
        self._operators: List[Dict[str, str]] = []
        self._load_operators(csv_path)

    def _load_operators(self, csv_path: str):
        """Wczytuje dane operatorów z pliku CSV, próbując różnych kodowań."""
        encodings_to_try = ['utf-8-sig', 'windows-1250']
        
        for encoding in encodings_to_try:
            try:
                log.debug(f"Próba otwarcia pliku operatorów '{csv_path}' z kodowaniem {encoding}...")
                with open(csv_path, mode='r', encoding=encoding) as infile:
                    reader = csv.DictReader(infile, delimiter=';')
                    expected_headers = {"EIC", "Name"}
                    if not expected_headers.issubset(reader.fieldnames or []):
                        log.error(f"Plik CSV '{csv_path}' ma nieprawidłowe nagłówki. Oczekiwano co najmniej: {expected_headers}")
                        return
                    
                    self._operators = list(reader)
                log.info(f"Pomyślnie załadowano {len(self._operators)} operatorów z pliku: {csv_path} (kodowanie: {encoding})")
                return # Sukces, przerywamy pętlę
            
            except UnicodeDecodeError:
                log.warning(f"Nie udało się odczytać pliku z kodowaniem {encoding}. Próbuję następnego...")
                continue
            
            except FileNotFoundError:
                log.error(f"Nie znaleziono pliku słownika operatorów: {csv_path}")
                return
                
            except Exception:
                log.error(f"Nie udało się wczytać lub przetworzyć słownika operatorów z {csv_path}", exc_info=True)
                return

        log.error(f"Nie udało się odczytać pliku '{csv_path}' przy użyciu żadnego z obsługiwanych kodowań: {encodings_to_try}")

    def get_random_operator_eic(self) -> Optional[str]:
        """Zwraca losowy kod EIC operatora z załadowanej listy."""
        if not self._operators:
            log.warning("Lista operatorów jest pusta. Nie można wylosować kodu EIC.")
            return None
        
        random_operator = random.choice(self._operators)
        return random_operator.get('EIC')