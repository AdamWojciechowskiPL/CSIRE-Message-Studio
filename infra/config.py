# csire_message_studio/infra/config.py
import logging
from pathlib import Path

# --- Ścieżki podstawowe ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Konfiguracja aplikacji ---
APP_NAME = "CSIRE Message Studio"
DEFAULT_GEOMETRY = "1200x800"

# --- Identyfikatory ---
PHYSICAL_RECIPIENT_ID = "19XEKOVOLTIS-PLX"
JURIDICAL_RECIPIENT_ID = "19XEKOVOLTIS-PLX"

# --- Uprawnienia ---
PERMISSIONS = {
    "can_edit_is_mp_part_of_facility": True,
    "can_edit_phases_count": True,
    "can_view_transformers_data": True,
    "can_edit_is_end_buyer": True,
    "can_edit_is_end_user": True,
    "can_view_kse_user_address": True,
    "can_view_kse_user_mailing_address": True,
    "can_view_reading_schedule": True,
    "can_view_network_agreement_type": True,
    "can_edit_threat_to_life": True,
    "can_edit_operator_suspension": True,
    "can_edit_supplier_suspension": True,
    "can_edit_operator_deactivation": True,
    "can_edit_supplier_deactivation": True,
    "can_view_billing_method_micro": True,
    "can_view_tariff_group": True,
    "can_edit_specific_service_conditions": True,
    "can_view_unplanned_one_off_interruption": True,
    "can_view_sum_of_unplanned_interruptions": True,
    "can_view_excess_power_billing": True,
    "can_view_excess_reactive_power_billing": True,
    "can_view_supplier_billing_period_supply": True,
    "can_view_supplier_billing_period_complex": True,
}

# --- Mapa obsługiwanych procesów i komunikatów ---
SUPPORTED_PROCESSES = {
    "3.1. Powiadomienie o zmianie charakterystyki PP": {
        "type_code": "3.1.",
        "messages": {
            "Powiadomienie o zmianie charakterystyki PP (3.1.1)": {
                "xsd_file": "3_1_1_1.xsd",
                "type_code": "3.1_1",
                "business_process_message_type": "Powiadomienie",
                "rules_dir_name": "3_1_1_1" 
            }
        }
    }
}

# --- Komunikaty systemowe ---
SYSTEM_MESSAGES = {
    "Response_R1": {
        "xsd_file": "R_1.xsd",
        "rules_file": "R_1.json"
    }
}

# --- Ścieżki do zasobów ---
RESOURCES_DIR = PROJECT_ROOT / "resources"
XSD_DIR = PROJECT_ROOT / "xsd"
LOG_DIR = PROJECT_ROOT / "logs"
DEFINITIONS_DIR = PROJECT_ROOT / "domain" / "definitions"
MESSAGE_RULES_DIR = DEFINITIONS_DIR / "message_rules"
PRESETS_DIR = PROJECT_ROOT / "presets"

# Ścieżki do konkretnych zasobów
XSD_INBOUND_DIR = XSD_DIR / "inbound_responses"
XSD_OUTBOUND_DIR = XSD_DIR / "outbound"
OPERATORS_CSV_PATH = RESOURCES_DIR / "CSIRE_Kody_EIC_Operatorow.csv"
XSD_RESPONSE_R1_PATH = XSD_INBOUND_DIR / SYSTEM_MESSAGES["Response_R1"]["xsd_file"]
VALIDATION_MATRIX_CSV_PATH = RESOURCES_DIR / "Zestawienie_walidacji_w_procesach_CSIRE.csv"

# --- Konfiguracja logowania ---
LOG_FILE = LOG_DIR / "app.log"
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5