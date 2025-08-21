# csire_message_studio/infra/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from . import config  # Importujemy naszą konfigurację

# Zmienna globalna zapobiegająca wielokrotnej inicjalizacji loggera
_logger_initialized = False

def setup_logging():
    """
    Konfiguruje główny logger aplikacji.
    
    Ta funkcja powinna być wywołana tylko raz, na samym początku działania aplikacji.
    Konfiguruje logowanie do pliku i na konsolę zgodnie z ustawieniami w config.py.
    """
    global _logger_initialized
    if _logger_initialized:
        return

    # Upewnij się, że katalog na logi istnieje. `parents=True` tworzy całą ścieżkę.
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Pobranie głównego loggera (root). Wszystkie inne loggery będą po nim dziedziczyć.
    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)

    # Zdefiniuj format logów
    formatter = logging.Formatter(config.LOG_FORMAT)

    # --- Handler do zapisu logów w pliku z rotacją ---
    # RotatingFileHandler automatycznie zarządza wielkością i liczbą plików logów.
    file_handler = RotatingFileHandler(
        filename=config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # --- Handler do wyświetlania logów na konsoli ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    _logger_initialized = True
    logging.info("="*50)
    logging.info("Logger został pomyślnie skonfigurowany.")
    logging.info(f"Poziom logowania: {logging.getLevelName(config.LOG_LEVEL)}")
    logging.info(f"Plik logu: {config.LOG_FILE}")
    logging.info("="*50)


def get_logger(name: str) -> logging.Logger:
    """
    Zwraca instancję loggera dla danego modułu.
    Jest to standardowa praktyka, aby każdy moduł miał swój własny logger.

    Args:
        name: Nazwa loggera, zazwyczaj __name__ modułu, w którym jest używany.

    Returns:
        Instancja loggera.
    """
    return logging.getLogger(name)

# --- Przykład użycia (do testowania tego pliku w izolacji) ---
if __name__ == '__main__':
    print("Testowanie konfiguracji loggera...")
    setup_logging()
    
    # Pobieramy logger dla naszego testowego modułu
    test_logger = get_logger(__name__)
    
    test_logger.debug("To jest wiadomość debugowa.")
    test_logger.info("To jest informacja.")
    test_logger.warning("To jest ostrzeżenie.")
    test_logger.error("To jest błąd.")
    test_logger.critical("To jest błąd krytyczny!")

    print(f"\nLogi zostały zapisane w pliku: {config.LOG_FILE}")
    print("Sprawdź zawartość pliku oraz konsolę, aby zweryfikować działanie.")