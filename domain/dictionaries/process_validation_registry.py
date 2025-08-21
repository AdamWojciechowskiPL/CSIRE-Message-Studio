# csire_message_studio/domain/dictionaries/process_validation_registry.py
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional

from infra.logger import get_logger

log = get_logger(__name__)

class ProcessValidationRegistry:
    """
    Zarządza macierzą walidacji wczytywaną z pliku CSV.
    Mapuje procesy biznesowe na listę dozwolonych kodów rezultatów (CE).
    """
    def __init__(self, csv_path: Path):
        self._rules: Dict[str, List[str]] = defaultdict(list)
        self._load_rules(csv_path)

    def _clean_process_name(self, raw_name: str) -> str:
        """Normalizuje nazwę procesu z nagłówka CSV do formatu używanego w komunikatach."""
        return raw_name.replace("UNK ", "").strip()

    def _load_rules(self, csv_path: Path):
        """Wczytuje i parsuje macierz walidacji z pliku CSV."""
        if not csv_path.exists():
            log.error(f"Nie znaleziono pliku macierzy walidacji: {csv_path}")
            return

        try:
            with open(csv_path, mode='r', encoding='utf-8-sig') as infile:
                # Pomijamy dwa pierwsze wiersze metadanych
                next(infile)
                next(infile)
                
                reader = csv.DictReader(infile, delimiter=';')
                if not reader.fieldnames or "Kod błędu" not in reader.fieldnames:
                    log.error(f"Plik CSV '{csv_path}' ma nieprawidłowy format lub nagłówki.")
                    return

                process_columns = [h for h in reader.fieldnames if h.startswith("UNK")]

                for row in reader:
                    error_code = row.get("Kod błędu")
                    if not error_code or not error_code.startswith("CE"):
                        continue
                    
                    for process_header in process_columns:
                        if row.get(process_header) == 'x':
                            clean_process_name = self._clean_process_name(process_header)
                            self._rules[clean_process_name].append(error_code)
            
            log.info(f"Pomyślnie załadowano macierz walidacji dla {len(self._rules)} procesów z pliku: {csv_path}")

        except Exception as e:
            log.error(f"Nie udało się wczytać lub przetworzyć macierzy walidacji z {csv_path}", exc_info=True)

    def get_valid_codes_for_process(self, process_type: str) -> Optional[List[str]]:
        """
        Zwraca listę dozwolonych kodów rezultatów (CE) dla danego typu procesu.
        """
        if not process_type:
            return None
        
        clean_process_type = process_type.strip()
        
        if clean_process_type in self._rules:
            codes = self._rules[clean_process_type]
            log.info(f"Znaleziono {len(codes)} dozwolonych kodów błędów dla procesu '{clean_process_type}'.")
            # Zawsze dołączamy kod sukcesu
            return ["CA0001"] + sorted(codes)
        else:
            log.warning(f"Nie znaleziono zdefiniowanych reguł walidacji dla procesu '{clean_process_type}' w macierzy.")
            return ["CA0001"] # Zwracamy przynajmniej kod sukcesu