# csire_message_studio/infra/file_handler.py
from pathlib import Path
from typing import Optional

from .logger import get_logger

log = get_logger(__name__)

def read_file(path: Path) -> Optional[str]:
    """
    Bezpiecznie odczytuje zawartość pliku tekstowego.

    Args:
        path: Ścieżka do pliku jako obiekt Path.

    Returns:
        Zawartość pliku jako string, lub None w przypadku błędu.
    """
    log.debug(f"Próba odczytu pliku: {path}")
    try:
        with path.open('r', encoding='utf-8') as f:
            content = f.read()
            log.info(f"Pomyślnie odczytano plik: {path}")
            return content
    except FileNotFoundError:
        log.error(f"Plik nie został znaleziony: {path}")
        return None
    except Exception:
        log.error(f"Wystąpił nieoczekiwany błąd podczas odczytu pliku: {path}", exc_info=True)
        return None

def write_file(path: Path, content: str) -> bool:
    """
    Bezpiecznie zapisuje zawartość do pliku tekstowego.
    Nadpisuje plik, jeśli istnieje.

    Args:
        path: Ścieżka do pliku jako obiekt Path.
        content: Zawartość do zapisania.

    Returns:
        True, jeśli zapis się powiódł, False w przeciwnym razie.
    """
    log.debug(f"Próba zapisu do pliku: {path}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as f:
            f.write(content)
            log.info(f"Pomyślnie zapisano plik: {path}")
            return True
    except Exception:
        log.error(f"Wystąpił nieoczekiwany błąd podczas zapisu do pliku: {path}", exc_info=True)
        return False

# --- NOWE FUNKCJE ---

def delete_file(path: Path) -> bool:
    """
    Bezpiecznie usuwa plik.

    Args:
        path: Ścieżka do pliku do usunięcia.

    Returns:
        True, jeśli usunięcie się powiodło, False w przeciwnym razie.
    """
    log.debug(f"Próba usunięcia pliku: {path}")
    if not path.exists():
        log.warning(f"Plik do usunięcia nie istnieje: {path}")
        return False
    try:
        path.unlink()
        log.info(f"Pomyślnie usunięto plik: {path}")
        return True
    except Exception:
        log.error(f"Wystąpił nieoczekiwany błąd podczas usuwania pliku: {path}", exc_info=True)
        return False

def rename_file(old_path: Path, new_path: Path) -> bool:
    """
    Bezpiecznie zmienia nazwę pliku.

    Args:
        old_path: Obecna ścieżka do pliku.
        new_path: Nowa ścieżka dla pliku.

    Returns:
        True, jeśli zmiana nazwy się powiodła, False w przeciwnym razie.
    """
    log.debug(f"Próba zmiany nazwy z {old_path} na {new_path}")
    if not old_path.exists():
        log.error(f"Plik źródłowy do zmiany nazwy nie istnieje: {old_path}")
        return False
    if new_path.exists():
        log.error(f"Nie można zmienić nazwy, plik docelowy już istnieje: {new_path}")
        return False
    try:
        old_path.rename(new_path)
        log.info(f"Pomyślnie zmieniono nazwę pliku na {new_path}")
        return True
    except Exception:
        log.error(f"Wystąpił nieoczekiwany błąd podczas zmiany nazwy pliku: {old_path}", exc_info=True)
        return False