# csire_message_studio/services/data_generators.py
import random
import string
import datetime
import uuid
from decimal import Decimal, getcontext
from typing import Dict, List, Optional
from faker import Faker
import exrex
from infra.logger import get_logger
from domain.dictionaries.operator_registry import OperatorRegistry
from domain.dictionaries.process_validation_registry import ProcessValidationRegistry
from infra import config
import re

log = get_logger(__name__)
faker = Faker('pl_PL')
getcontext().prec = 18

_address_generation_state: Dict[str, Dict[str, Optional[str]]] = {}

def reset_address_generation_state() -> None:
    """Resetuje stan generatora adresów, aby zapewnić spójność przy nowym generowaniu."""
    _address_generation_state.clear()
    log.debug("Stan generatora adresów został zresetowany.")

# --- Słowniki i rejestry ---
PPE_COMPANY_PREFIXES: List[str] = ["2438", "3106", "3224", "3641", "3801", "5069", "5435", "5701", "5711", "5815", "6815", "5088", "4619", "5045", "5324"]
operator_registry = OperatorRegistry(config.OPERATORS_CSV_PATH)
validation_registry = ProcessValidationRegistry(config.VALIDATION_MATRIX_CSV_PATH)

def generate_error_code_for_process(process_type: str) -> Optional[str]:
    """Pobiera dozwolone kody błędów dla procesu z macierzy i losuje jeden z nich."""
    if not process_type:
        log.warning("Generator kodów błędów: nie podano typu procesu. Zwracam domyślny błąd.")
        return "CE999"
        
    valid_codes = validation_registry.get_valid_codes_for_process(process_type)
    
    error_codes = [code for code in (valid_codes or []) if code.startswith("CE")]
    
    if error_codes:
        selected_code = random.choice(error_codes)
        log.info(f"Wylosowano kod błędu '{selected_code}' dla procesu '{process_type}'.")
        return selected_code
    else:
        log.warning(f"Nie znaleziono dozwolonych kodów BŁĘDÓW dla procesu '{process_type}'. Zwracam domyślny błąd.")
        return "CE999"

# --- Generatory Specjalistyczne ---
NIP_WEIGHTS: List[int] = [6, 5, 7, 2, 3, 4, 5, 6, 7]
PESEL_WEIGHTS: List[int] = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]

def _calculate_nip_checksum(digits: List[int]) -> int:
    check_sum = sum(d * w for d, w in zip(digits, NIP_WEIGHTS))
    return check_sum % 11

def generate_nip() -> str:
    max_attempts = 100
    for _ in range(max_attempts):
        first_digit = [random.randint(1, 9)]
        next_eight_digits = [random.randint(0, 9) for _ in range(8)]
        digits = first_digit + next_eight_digits
        checksum = _calculate_nip_checksum(digits)
        if checksum != 10:
            digits.append(checksum)
            return "".join(map(str, digits))
    log.warning("Nie udało się wygenerować NIP po maksymalnej liczbie prób.")
    return "1234567890"

def generate_pesel() -> str:
    digits = [random.randint(0, 9) for _ in range(10)]
    check_sum = sum(d * w for d, w in zip(digits, PESEL_WEIGHTS))
    control_digit = (10 - (check_sum % 10)) % 10
    digits.append(control_digit)
    return "".join(map(str, digits))

def generate_krs() -> str: return faker.numerify('##########')

def generate_global_tax_id() -> str:
    country_codes = ['DE', 'FR', 'PL', 'CZ', 'ES', 'IT', 'GB', 'NL', 'AT', 'BE']
    prefix = random.choice(country_codes)
    num_digits = random.randint(8, 12)
    number_part = faker.numerify('#' * num_digits)
    return f"{prefix}{number_part}"

def generate_custom_kse_user_id() -> str:
    eic = operator_registry.get_random_operator_eic() or "19XOPERATOR-PL-0"
    unique_part = faker.numerify('###########')
    return f"{eic}UKSE{unique_part}"

def generate_ppe() -> str:
    company_prefix = random.choice(PPE_COMPANY_PREFIXES)
    location_part = "".join(str(random.randint(0, 9)) for _ in range(10))
    payload_str = f"590{company_prefix}{location_part}"
    payload_digits = [int(d) for d in payload_str]
    check_sum = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(payload_digits)))
    control_digit = (10 - (check_sum % 10)) % 10
    return payload_str + str(control_digit)

def generate_operator_identifier() -> str:
    eic = operator_registry.get_random_operator_eic()
    if eic: return eic
    log.error("Nie udało się pobrać kodu EIC operatora z rejestru. Zwracam wartość zastępczą.")
    return "19X-BRAK-DANYCH-0"

def generate_uuid() -> str: return str(uuid.uuid4())
def generate_latitude_pl() -> str: return f"{random.uniform(49.0, 54.9):.6f}"
def generate_longitude_pl() -> str: return f"{random.uniform(14.1, 24.1):.6f}"
def generate_teryt_code() -> str: return faker.numerify('#####')

def generate_future_date(params: Dict[str, int]) -> str:
    days = params.get("days", 90)
    start_date = datetime.date.today() + datetime.timedelta(days=1)
    end_date = start_date + datetime.timedelta(days=days)
    random_date = start_date + datetime.timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
    return random_date.strftime('%Y-%m-%d')

def generate_past_date(params: Dict[str, int]) -> str:
    days = params.get("days", 365 * 2)
    end_date = datetime.date.today() - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=days)
    random_date = start_date + datetime.timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
    return random_date.strftime('%Y-%m-%d')

def business_sentence(params: Dict = {}) -> str: return faker.bs().capitalize() + "."
def generate_city() -> str: return faker.city()
def generate_postal_code() -> str: return faker.postcode()
def generate_street_name() -> str: return faker.street_name()
def generate_building_number() -> str: return faker.building_number()
def generate_apartment_number() -> str: return str(faker.random_int(min=1, max=150))
def generate_full_name() -> str: return faker.name()
def generate_email() -> str: return faker.email()
def generate_dso_phone_number() -> str: return faker.numerify('+48#########')
def generate_first_name() -> str: return faker.first_name()
def generate_last_name() -> str: return faker.last_name()
def generate_company_name() -> str: return faker.company()
def generate_plot_number() -> str: return f"działka nr {faker.random_int(min=1, max=500)}/{faker.random_int(min=1, max=20)}"
def generate_string(restrictions: Dict[str, int]) -> str:
    min_len = restrictions.get('minLength', 1)
    max_len = restrictions.get('maxLength', 10)
    if min_len > max_len: min_len = max_len
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
def generate_integer(restrictions: Dict[str, str]) -> str:
    min_val = int(restrictions.get('minInclusive', '0'))
    max_val = int(restrictions.get('maxInclusive', '10000'))
    if min_val > max_val: min_val, max_val = max_val, min_val
    return str(random.randint(min_val, max_val))
def generate_decimal(restrictions: Dict[str, str]) -> str:
    min_val = Decimal(str(restrictions.get('minInclusive', '0')))
    max_val = Decimal(str(restrictions.get('maxInclusive', '1000')))
    frac_digits = int(restrictions.get('fractionDigits', '2'))
    if min_val > max_val: min_val, max_val = max_val, min_val
    rand_val = min_val + (max_val - min_val) * Decimal(random.random())
    quantized = rand_val.quantize(Decimal('1.' + '0' * frac_digits))
    if frac_digits == 0: return str(int(quantized))
    return str(quantized)
def generate_date() -> str:
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=5 * 365)
    random_date = start_date + datetime.timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))
    return random_date.strftime('%Y-%m-%d')
def generate_datetime() -> str: return datetime.datetime.now().replace(microsecond=0).isoformat()
def generate_boolean() -> str: return random.choice(['true', 'false'])
def generate_from_pattern(pattern_obj: any) -> str:
    pattern_str = ""
    if isinstance(pattern_obj, re.Pattern): pattern_str = pattern_obj.pattern
    elif isinstance(pattern_obj, str): pattern_str = pattern_obj
    else:
        log.warning(f"Otrzymano nieoczekiwany typ dla wzorca: {type(pattern_obj)}. Używam generatora generycznego.")
        return generate_string({'minLength': 8, 'maxLength': 16})
    if pattern_str == r'(\d{2})([0-9A-Z\-]{14})':
        prefix = ''.join(random.choices(string.digits, k=2))
        suffix_chars = string.ascii_uppercase + string.digits + '-'
        suffix = ''.join(random.choices(suffix_chars, k=14))
        return prefix + suffix
    try:
        clean_pattern = pattern_str.replace('\\\\', '\\')
        return exrex.getone(clean_pattern)
    except Exception as e:
        log.warning(f"Nie udało się wygenerować wartości ze wzorca '{pattern_str}'. Błąd: {e}. Używam generatora generycznego.")
        return generate_string({'minLength': 8, 'maxLength': 16})

GENERATOR_MAPPING = {
    "generate_future_date": generate_future_date,
    "generate_past_date": generate_past_date,
    "business_sentence": business_sentence,
    "generate_nip": lambda params: generate_nip(),
    "generate_pesel": lambda params: generate_pesel(),
    "generate_krs": lambda params: generate_krs(),
    "generate_global_tax_id": lambda params: generate_global_tax_id(),
    "generate_custom_kse_user_id": lambda params: generate_custom_kse_user_id(),
    "generate_ppe": lambda params: generate_ppe(),
    "generate_operator_identifier": lambda params: generate_operator_identifier(),
    "generate_uuid": lambda params: generate_uuid(),
    "generate_latitude_pl": lambda params: generate_latitude_pl(),
    "generate_longitude_pl": lambda params: generate_longitude_pl(),
    "generate_teryt_code": lambda params: generate_teryt_code(),
    "generate_city": lambda params: generate_city(),
    "generate_postal_code": lambda params: generate_postal_code(),
    "generate_street_name": lambda params: generate_street_name(),
    "generate_building_number": lambda params: generate_building_number(),
    "generate_apartment_number": lambda params: generate_apartment_number(),
    "generate_full_name": lambda params: generate_full_name(),
    "generate_email": lambda params: generate_email(),
    "generate_dso_phone_number": lambda params: generate_dso_phone_number(),
    "generate_first_name": lambda params: generate_first_name(),
    "generate_last_name": lambda params: generate_last_name(),
    "generate_company_name": lambda params: generate_company_name(),
    "generate_plot_number": lambda params: generate_plot_number(),
    "generate_date": lambda params: generate_date(),
    "generate_datetime": lambda params: generate_datetime(),
    "generate_boolean": lambda params: generate_boolean()
}

def generate_valid_data(field_info, rules: Optional[Dict] = None, available_choices: Optional[List[str]] = None) -> Optional[str]:
    """Główny dyspatcher generowania danych."""
    rules = rules or {}
    path = field_info.path
    name_lower = field_info.name.lower()
    xsd_type_obj = field_info.xsd_type_obj
    xsd_type = field_info.xsd_type
    
    if path in rules:
        for rule in rules[path].values():
            if rule.get("action") == "set_value":
                return None
        
    if path in rules and "data_generation" in rules[path]:
        rule = rules[path]["data_generation"]
        generator_name = rule.get("generator")
        
        log.debug(f"LOG_GEN: Znaleziono regułę 'data_generation' dla pola '{path}': {rule}")
        
        if generator_name in GENERATOR_MAPPING:
            probability = float(rule.get("probability", 1.0))
            rand_val = random.random()
            
            log.debug(f"LOG_GEN_PROB: [START] Sprawdzanie prawdopodobieństwa dla '{path}'")
            log.debug(f"LOG_GEN_PROB: Próg z reguły (probability): {probability}")
            log.debug(f"LOG_GEN_PROB: Wylosowana wartość: {rand_val:.4f}")
            
            if rand_val < probability:
                log.debug(f"LOG_GEN_PROB: [SUKCES] Warunek ({rand_val:.4f} < {probability}) spełniony. Uruchamiam generator.")
                params = rule.get("params", {})
                log.info(f"LOG_GEN: Używam generatora '{generator_name}' zdefiniowanego w regułach dla pola '{path}'.")
                return GENERATOR_MAPPING[generator_name](params)
            else:
                log.debug(f"LOG_GEN_PROB: [PORAŻKA] Warunek ({rand_val:.4f} < {probability}) niespełniony. Pomijam generowanie.")
                log.info(f"LOG_GEN: Pole '{path}' nie zostanie wypełnione z powodu reguły prawdopodobieństwa.")
                return None
        else:
            log.warning(f"LOG_GEN: Generator '{generator_name}' zdefiniowany w regułach dla '{path}' nie został znaleziony w GENERATOR_MAPPING.")

    log.debug(f"LOG_GEN: Brak reguł 'data_generation'. Używam standardowego generatora dla pola '{path}' (typ: {xsd_type}).")
    
    # --- POPRAWKA: Generator teraz respektuje przefiltrowaną listę z GUI ---
    if available_choices:
        log.debug(f"LOG_GEN: Używam przefiltrowanej listy dostępnych opcji z GUI: {available_choices}")
        valid_options = [opt for opt in available_choices if opt]
        if valid_options:
            return random.choice(valid_options)

    if field_info.enumerations: return str(random.choice(field_info.enumerations))
    
    if xsd_type == 'CountryIsoCodeType': return 'PL'
    if xsd_type == 'KrsType': return generate_krs()
    if xsd_type == 'GlobalTaxIdentificationType': return generate_global_tax_id()
    if xsd_type == 'UuidType': return generate_uuid()
    if 'nip' in name_lower: return generate_nip()
    if 'pesel' in name_lower: return generate_pesel()
    if 'meteringpointcode' in name_lower or 'ppecode' in name_lower: return generate_ppe()
    if name_lower == 'customkseuseridentifier': return generate_custom_kse_user_id()
    
    address_related_fields = {
        'plotnumber', 'streetname', 'buildingnumber', 'apartmentnumber',
        'isstreetseparationpresent', 'latitude', 'longitude',
        'isstreetterytcodeavailable', 'teryt'
    }
    if name_lower in address_related_fields:
        group_path = path.rsplit('.', 1)[0]
        if group_path not in _address_generation_state:
            teryt_decision = random.choice([True, False])
            street_plot_decision = 'use_street' if teryt_decision else ('use_street' if random.random() < 0.8 else 'use_plot')
            lat, lon = (generate_latitude_pl(), generate_longitude_pl()) if random.choice([True, False]) else (None, None)
            _address_generation_state[group_path] = {
                'teryt_val': generate_teryt_code() if teryt_decision else None,
                'decision': street_plot_decision,
                'latitude_val': lat,
                'longitude_val': lon,
                'street_separation_val': 'true' if street_plot_decision == 'use_street' else 'false'
            }
        state = _address_generation_state[group_path]
        if name_lower == 'isstreetterytcodeavailable': return 'true' if state['teryt_val'] is not None else 'false'
        if name_lower == 'teryt': return state['teryt_val'] if state['teryt_val'] is not None else None
        if name_lower == 'isstreetseparationpresent': return state['street_separation_val']
        if name_lower == 'latitude': return state['latitude_val'] if state['latitude_val'] is not None else None
        if name_lower == 'longitude': return state['longitude_val'] if state['longitude_val'] is not None else None
        if name_lower == 'plotnumber': return generate_plot_number() if state['decision'] == 'use_plot' else None
        if name_lower in ('streetname', 'buildingnumber', 'apartmentnumber'):
            if state['decision'] == 'use_plot': return None
            if name_lower == 'streetname': return generate_street_name()
            if name_lower == 'buildingnumber': return generate_building_number()
            if name_lower == 'apartmentnumber': return generate_apartment_number()
    
    if 'cityname' in name_lower: return generate_city()
    if 'postalcode' in name_lower: return generate_postal_code()
    if 'recipientname' in name_lower: return generate_full_name()
    if 'dsoemailaddress' in name_lower: return generate_email()
    if 'dsophonenumber' in name_lower: return generate_dso_phone_number()
    if 'firstname' in name_lower: return generate_first_name()
    if 'lastname' in name_lower: return generate_last_name()
    if 'companyname' in name_lower: return generate_company_name()
    
    if xsd_type_obj:
        type_name = xsd_type_obj.local_name
        base_type_name = ""
        if hasattr(xsd_type_obj, 'base_type') and xsd_type_obj.base_type is not None:
            base_type_name = xsd_type_obj.base_type.local_name

        log.debug(f" -> Analiza typu: type_name='{type_name}', base_type_name='{base_type_name}'")

        if type_name == 'integer' or base_type_name == 'integer':
            log.debug(f" -> Rozpoznane jako INTEGER. Używam generate_integer.")
            return generate_integer(field_info.restrictions)
        elif type_name == 'decimal' or base_type_name == 'decimal':
            log.debug(f" -> Rozpoznane jako DECIMAL. Używam generate_decimal.")
            return generate_decimal(field_info.restrictions)
        elif type_name == 'date' or base_type_name == 'date':
             return generate_date()
        elif type_name == 'boolean' or base_type_name == 'boolean':
            return generate_boolean()

    if 'datetime' in (xsd_type or "").lower():
        return generate_datetime()
    
    if 'pattern' in field_info.restrictions:
        log.debug(f" -> Pole '{path}' ma wzorzec. Używam generate_from_pattern.")
        return generate_from_pattern(field_info.restrictions['pattern'])

    log.debug(f" -> Nie pasuje do żadnego typu bazowego. Używam generycznego generate_string.")
    return generate_string(field_info.restrictions)