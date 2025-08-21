# csire_message_studio/app/main.py
import tkinter as tk

# KROK 1: Konfiguracja musi być zaimportowana jako pierwsza
from infra import config
from infra.logger import setup_logging, get_logger

# KROK 2: Inicjalizacja loggera na samym początku
setup_logging()
log = get_logger(__name__)

# KROK 3: Import reszty komponentów aplikacji
from app.views.main_window import MainWindow
from app.controllers.response_controller import ResponseController
from app.controllers.outbound_controller import OutboundController

if __name__ == "__main__":
    log.info(f"Uruchamianie aplikacji {config.APP_NAME}...")
    try:
        root = tk.Tk()
        root.title(config.APP_NAME)
        root.geometry(config.DEFAULT_GEOMETRY)

        # Utwórz główny widok aplikacji
        app_view = MainWindow(root)

        # Utwórz kontrolery, przekazując im odpowiednie widoki i pasek statusu
        response_controller = ResponseController(app_view.response_frame, app_view.status_bar)
        outbound_controller = OutboundController(app_view.outbound_frame, app_view.status_bar)

        log.info("Aplikacja została pomyślnie zainicjowana. Uruchamianie pętli głównej.")
        root.mainloop()

    except Exception as e:
        log.critical("Wystąpił nieobsługiwany błąd krytyczny. Aplikacja zostanie zamknięta.", exc_info=True)
    
    log.info(f"Aplikacja {config.APP_NAME} została zamknięta.")