# csire_message_studio/services/preset_manager.py
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from infra import config
from infra.logger import get_logger
from infra.file_handler import read_file, write_file, delete_file, rename_file

log = get_logger(__name__)

class PresetManager:
    """
    Zarządza operacjami na presetach (zapis, odczyt, usuwanie, zmiana nazwy).
    Operuje na plikach JSON w dedykowanej strukturze katalogów.
    """
    def __init__(self):
        self.presets_dir = config.PRESETS_DIR
        # Upewnij się, że główny katalog presetów istnieje
        self.presets_dir.mkdir(exist_ok=True)
        log.info(f"PresetManager zainicjalizowany. Katalog główny: {self.presets_dir}")

    def _get_message_preset_dir(self, message_code: str, create_if_not_exists: bool = False) -> Path:
        """Zwraca ścieżkę do katalogu z presetami dla danego typu komunikatu."""
        message_dir = self.presets_dir / message_code.replace('.', '_') # Zabezpieczenie nazw katalogów
        if create_if_not_exists:
            message_dir.mkdir(exist_ok=True)
        return message_dir

    def get_presets_for_message(self, message_code: str) -> List[str]:
        """Zwraca listę nazw presetów dla danego typu komunikatu."""
        if not message_code:
            return []
        
        message_dir = self._get_message_preset_dir(message_code)
        if not message_dir.exists():
            return []
        
        try:
            presets = [p.stem for p in message_dir.glob('*.json')]
            log.info(f"Znaleziono {len(presets)} presetów dla komunikatu '{message_code}'.")
            return sorted(presets)
        except Exception as e:
            log.error(f"Błąd podczas odczytu listy presetów dla '{message_code}': {e}", exc_info=True)
            return []

    def load_preset(self, message_code: str, preset_name: str) -> Optional[Dict[str, Any]]:
        """Wczytuje dane presetu z pliku JSON."""
        if not message_code or not preset_name:
            return None
            
        message_dir = self._get_message_preset_dir(message_code)
        preset_file = message_dir / f"{preset_name}.json"

        if not preset_file.exists():
            log.error(f"Plik presetu nie istnieje: {preset_file}")
            return None
        
        content = read_file(preset_file)
        if content:
            try:
                data = json.loads(content)
                log.info(f"Pomyślnie załadowano preset '{preset_name}' z pliku {preset_file}.")
                return data.get("data")
            except json.JSONDecodeError as e:
                log.error(f"Błąd parsowania pliku JSON presetu '{preset_file}': {e}", exc_info=True)
                return None
        return None

    def save_preset(self, message_code: str, preset_name: str, data: Dict[str, Any]) -> bool:
        """Zapisuje dane presetu do pliku JSON."""
        if not message_code or not preset_name:
            log.error("Nie można zapisać presetu. Brak kodu komunikatu lub nazwy presetu.")
            return False
            
        message_dir = self._get_message_preset_dir(message_code, create_if_not_exists=True)
        preset_file = message_dir / f"{preset_name}.json"
        
        # Tworzymy pełny obiekt do zapisu, zgodnie z architekturą
        preset_content = {
            "name": preset_name,
            "data": data
        }
        
        try:
            json_string = json.dumps(preset_content, indent=4, ensure_ascii=False)
            if write_file(preset_file, json_string):
                log.info(f"Pomyślnie zapisano preset '{preset_name}' w pliku {preset_file}.")
                return True
            return False
        except Exception as e:
            log.error(f"Nieoczekiwany błąd podczas przygotowywania presetu '{preset_name}' do zapisu: {e}", exc_info=True)
            return False

    def delete_preset(self, message_code: str, preset_name: str) -> bool:
        """Usuwa plik presetu."""
        if not message_code or not preset_name:
            return False

        message_dir = self._get_message_preset_dir(message_code)
        preset_file = message_dir / f"{preset_name}.json"

        if delete_file(preset_file):
            log.info(f"Pomyślnie usunięto preset '{preset_name}' z {preset_file}.")
            return True
        return False
        
    def rename_preset(self, message_code: str, old_name: str, new_name: str) -> bool:
        """Zmienia nazwę pliku presetu."""
        if not message_code or not old_name or not new_name or old_name == new_name:
            return False
            
        message_dir = self._get_message_preset_dir(message_code)
        old_file = message_dir / f"{old_name}.json"
        new_file = message_dir / f"{new_name}.json"

        if new_file.exists():
            log.warning(f"Nie można zmienić nazwy. Preset o nazwie '{new_name}' już istnieje.")
            return False

        if rename_file(old_file, new_file):
            # Zaktualizuj również zawartość pliku, aby klucz "name" był spójny
            data = self.load_preset(message_code, new_name)
            if data:
                self.save_preset(message_code, new_name, data)
                log.info(f"Pomyślnie zmieniono nazwę presetu z '{old_name}' na '{new_name}'.")
                return True
        return False