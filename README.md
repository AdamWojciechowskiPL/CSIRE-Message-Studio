# CSIRE Message Studio

**CSIRE Message Studio** to zaawansowane, inteligentne narzędzie deweloperskie, którego architektura jest w pełni sterowana przez zewnętrzne definicje i reguły. Zostało zaprojektowane, aby całkowicie zautomatyzować i drastycznie przyspieszyć proces tworzenia, testowania i walidacji komunikatów XML w standardzie CSIRE, eliminując praktycznie wszystkie manualne błędy.

Aplikacja jest przeznaczona dla deweloperów, testerów i analityków, którzy wymagają elastycznego i niezawodnego narzędzia do pracy ze złożonymi, warunkowymi strukturami danych.

## Kluczowe Funkcjonalności

### 1. Dynamiczne Formularze Sterowane Schematem XSD
Rdzeniem aplikacji jest potężny silnik, który na podstawie plików `.xsd` dynamicznie buduje interfejs użytkownika. System w pełni rozumie i respektuje złożoną architekturę schematów CSIRE, w tym:
*   **Złożone Przestrzenie Nazw (Namespaces):** Aplikacja automatycznie rozpoznaje i stosuje wszystkie przestrzenie nazw (np. `tech`, `unk`) zdefiniowane w schematach, generując XML z poprawnymi prefiksami.
*   **Poprawna Kolejność Elementów (`<xs:sequence>`):** Parser XSD i renderer formularzy ściśle respektują kolejność elementów zdefiniowaną w schemacie, co gwarantuje poprawność strukturalną generowanych komunikatów.
*   **Krotność Elementów:** Obsługuje sekcje opcjonalne (`minOccurs="0"`) i wielokrotne (`maxOccurs="unbounded"`), pozwalając na intuicyjne dodawanie i usuwanie instancji w GUI.
*   **Typy Danych i Słowniki:** Waliduje typy danych (daty, liczby) i automatycznie tworzy listy wyboru dla wartości słownikowych (`enumeration`).

### 2. Silnik Reguł Sterowany Plikami JSON
Logika biznesowa aplikacji nie jest zaszyta w kodzie. Jest ona dynamicznie wczytywana z dedykowanych plików `.json`, co pozwala na błyskawiczne dostosowanie aplikacji do dowolnego, nawet najbardziej złożonego komunikatu.
*   **Wiele Zestawów Reguł:** Aplikacja pozwala na definiowanie **wielu plików z regułami dla jednego typu komunikatu**. Użytkownik może dynamicznie przełączać się między różnymi scenariuszami (np. "Umowa Dystrybucyjna", "Umowa Kompleksowa") bezpośrednio w interfejsie.
*   **Logika Warunkowa:** Definiuj złożone, wielopoziomowe warunki (z operatorami `AND`/`OR`) bazujące na wartościach innych pól.
*   **Dynamiczna Widoczność i Wymagalność:** Automatycznie pokazuj/ukrywaj całe sekcje lub dynamicznie zmieniaj pola z opcjonalnych na wymagane.
*   **Mapowanie Danych z Importu:** Reguły pozwalają na zdefiniowanie, które dane z importowanego pliku JSON mają zostać wstawione do konkretnych pól formularza, z opcją ich zablokowania.
*   **Automatyczne Czyszczenie Danych:** Gdy reguła powoduje ukrycie lub wyłączenie pola, jego wartość jest automatycznie czyszczona, co zapobiega wysyłaniu nieprawidłowych danych.

### 3. Inteligentny Generator Danych Testowych
Moduł do automatycznego wypełniania formularzy generuje logicznie i biznesowo spójne dane, w pełni respektując nową architekturę reguł.
*   **Asynchroniczne, Iteracyjne Generowanie:** Generator współpracuje z pętlą zdarzeń interfejsu. Gwarantuje to, że nawet najbardziej złożone, wielopoziomowe zależności między polami są rozwiązywane poprawnie.
*   **Respektowanie Reguł Filtrowania:** Generator jest w pełni świadomy reguł `filter_values`. Jeśli lista wyboru w interfejsie została dynamicznie ograniczona, generator wylosuje wartość **wyłącznie spośród aktualnie dostępnych opcji**.
*   **Ochrona Zablokowanych Pól:** Generator nigdy nie nadpisuje wartości w polach, które zostały zablokowane (np. w wyniku importu danych).
*   **Poprawne Identyfikatory i Wzorce:** Tworzy numery **NIP**, **PESEL** i **PPE** z poprawnymi sumami kontrolnymi oraz wartości zgodne ze wzorcami XSD.
*   **Realistyczne Dane:** Dzięki integracji z biblioteką **Faker** (`pl_PL`) generuje polskie dane osobowe, adresowe i nazwy firm.

### 4. Zaawansowany System Presetów
Wypełniaj skomplikowane formularze jednym kliknięciem. System presetów pozwala zapisywać i wczytywać kompletne zestawy danych, co jest idealne do testowania powtarzalnych scenariuszy.
*   **Pełne Zarządzanie z GUI:** Zapisuj, wczytuj, zmieniaj nazwy i usuwaj presety bezpośrednio z interfejsu.
*   **Powiązanie z Komunikatem:** Presety są inteligentnie powiązane z konkretnym typem komunikatu. Po zmianie komunikatu lista dostępnych presetów automatycznie się aktualizuje.
*   **Inteligentna Obsługa Pól Technicznych:** System automatycznie ignoruje i generuje na nowo pola wrażliwe na czas, takie jak `MessageTimestamp`.

### 5. Zintegrowana Walidacja XSD i Budowanie XML
Proces generowania komunikatu jest w pełni zautomatyzowany i zabezpieczony.
*   **Automatyzacja Pól Technicznych:** Pola takie jak `MessageId` i `MessageTimestamp` są wypełniane automatycznie tuż przed generacją.
*   **Walidacja "w locie":** Po kliknięciu "Generuj i Waliduj XML", aplikacja nie tylko buduje dokument, ale natychmiast weryfikuje go względem pełnego schematu XSD.
*   **Precyzyjne Komunikaty o Błędach:** W przypadku niezgodności, użytkownik otrzymuje szczegółowy komunikat o błędzie, zawierający powód i ścieżkę do problematycznego elementu.

### 6. Import Danych Wejściowych dla Odpowiedzi
Zakładka "Odpowiedzi (R_1)" posiada funkcję importu pliku `.json`, która automatycznie uzupełnia kluczowe pola potrzebne do wygenerowania odpowiedzi (np. `SenderMessageId`, `BusinessProcess`). Aplikacja obsługuje dwa formaty.

#### Format 1: Surowy JSON (zalecany)
Jest to prosty format przeznaczony do ręcznego tworzenia lub prostych integracji.

*   `CsireMessageId`: (string) ID komunikatu, na który odpowiadasz. Zostanie zmapowane na pole `SenderMessageId` w odpowiedzi R_1.
*   `ProcessType`: (string) Pełny typ procesu z komunikatu, na który odpowiadasz (np. "1.2.1.1."). Aplikacja użyje go do wywnioskowania `BusinessProcess` ("1.2.") i załadowania odpowiedniego zestawu reguł.
*   `Body.MeteringPointData.MeteringPointCode`: (string, zagnieżdżony) Kod PPE, którego dotyczy komunikat.

**Przykład:**
```json
{
  "CsireMessageId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "ProcessType": "1.2.1.1.",
  "Body": {
    "MeteringPointData": {
      "MeteringPointCode": "590000000000000001"
    }
  }
}
```

#### Format 2: Koperta LUXhub
Format ten jest przeznaczony do testowania scenariuszy, w których komunikaty są opakowane w standardową "kopertę" systemową.

*   `payload`: (string) Cały komunikat XML, na który chcesz odpowiedzieć, zakodowany w **Base64**. Aplikacja automatycznie zdekoduje treść i wyodrębni z niej `MessageId`, `BusinessProcess` oraz `MeteringPointCode`.

**Przykład:**
```json
{
  "payload": "PE5vdGlmaWNhdGlvbj48SGVhZGVyPjxNZXNzYWdlSWQ+ZjFlMmQzYzQtYjVhNi00ZjdlLThkOWMtMGExYjJjM2Q0ZTVmPC9NZXNzYWdlSWQ+PC9IZWFkZXI+PFByb2Nlc3NFbmVyZ3lDb250ZXh0PjxCdXNpbmVzc1Byb2Nlc3M+MS4xLjwvQnVzaW5lc3NQcm9jZXNzPjwvUHJvY2Vzc0VuZXJneUNvbnRleHQ+PFBheWxvYWQ+PE1ldGVyaW5nUG9pbnREYXRhX0Jhc2ljPjxNZXRlcmluZ1BvaW50Q29kZT41OTAxMTExMTExMTExMTExMTExPC9NZXRlcmluZ1BvaW50Q29kZT48L01ldGVyaW5nUG9pbnREYXRhX0Jhc2ljPjwvUGF5bG9hZD48L05vdGlmaWNhdGlvbj4="
}
```

## Konfiguracja i Architektura Sterowana Danymi
Potęga aplikacji leży w jej zdolności do adaptacji poprzez zewnętrzne pliki konfiguracyjne, bez konieczności modyfikacji kodu źródłowego.

### A. Pliki Schematów XSD
*   **Rola:** Definiują strukturę, kolejność, typy danych i ograniczenia dla komunikatów XML. Są podstawą do dynamicznego budowania interfejsu graficznego.
*   **Lokalizacja:** `xsd/` (z podziałem na `inbound_responses` i `outbound`).
*   **Wymagania:** Kluczowe jest, aby ścieżki `schemaLocation` wewnątrz plików XSD były poprawne **względem siebie**. Parser `xmlschema` używa tych ścieżek do poprawnego resolwowania importów i inkludów.

### B. Pliki Reguł Biznesowych (`.json`)
*   **Rola:** Definiują całą logikę biznesową formularza: widoczność pól, wymagalność, wartości domyślne, filtrowanie list, mapowanie importu i logikę generatora danych.
*   **Lokalizacja:** `domain/definitions/message_rules/{nazwa_katalogu_reguł}/`

#### Struktura Pliku Reguł
Plik `.json` ma prostą strukturę. Główny obiekt zawiera klucz `"rules"`. Jego wartością jest obiekt, w którym każdy klucz to **pełna ścieżka do elementu docelowego** (`target_path`), a wartością jest obiekt definiujący jedną lub więcej reguł dla tego elementu.

```json
{
  "rules": {
    "Target.Element.Path": {
      "unique_rule_name_1": {
        "action": "...",
        "condition": { ... }
      },
      "unique_rule_name_2": { ... }
    },
    "Target.Element.Path2": { ... }
  }
}
```

#### Obiekt Warunku (`condition`)
Większość reguł jest warunkowa. Obiekt `condition` określa, kiedy reguła ma zostać aktywowana.

*   **Prosty warunek:**
    ```json
    "condition": {
      "field_path": "Trigger.Element.Path",
      "values": ["wartość_A", "wartość_B"] 
    }
    ```
*   **Złożony warunek (AND/OR):**
    ```json
    "condition": {
      "operator": "OR",
      "conditions": [
        { "field_path": "Path.One", "values": ["A"] },
        { "field_path": "Path.Two", "is_not_empty": true }
      ]
    }
    ```
*   **Dostępne klucze warunku:**
    *   `field_path`: Ścieżka do pola, które wyzwala regułę.
    *   `values`: Lista wartości, z których przynajmniej jedna musi pasować.
    *   `not_values`: Lista wartości, z których żadna nie może pasować.
    *   `is_not_empty`: `true` lub `false`.
    *   `operator`: `AND` (domyślny) lub `OR`.
    *   `conditions`: Lista obiektów pod-warunków.

#### Dostępne Akcje (`action`)

| Akcja | Opis | Przykład |
| :--- | :--- | :--- |
| **`set_value`** | Ustawia stałą wartość w polu i je blokuje. Działa, jeśli warunek jest spełniony. | `{ "action": "set_value", "value": "generate:uuid" }` |
| **`set_value_from_import`** | Wstawia wartość z zaimportowanego pliku i (domyślnie) blokuje pole. Działa tylko przy imporcie. | `{ "action": "set_value_from_import", "source_path": "message_id", "lock_field": true }` |
| **`show_if_value`** | Pokazuje element (pole/sekcję), jeśli warunek jest spełniony. W przeciwnym wypadku ukrywa i czyści wartość. | `{ "action": "show_if_value", "condition": { ... } }` |
| **`forbid_if_value`** | Ukrywa element i czyści jego wartość, jeśli warunek jest spełniony. W przeciwnym wypadku go pokazuje. | `{ "action": "forbid_if_value", "condition": { ... } }` |
| **`hide`** | Bezwarunkowo ukrywa element. | `{ "action": "hide" }` |
| **`require_if_value`** | Pokazuje element i oznacza go jako wymagany (`*`), jeśli warunek jest spełniony. W przeciwnym wypadku ukrywa i czyści wartość. | `{ "action": "require_if_value", "condition": { ... } }` |
| **`enable_if_value`** | Włącza/wyłącza pole do edycji w zależności od warunku. Wyłączenie czyści wartość. | `{ "action": "enable_if_value", "condition": { ... } }` |
| **`filter_values`** | Dynamicznie filtruje listę dostępnych opcji w `Combobox` do tych podanych w `values`. | `{ "action": "filter_values", "condition": { ... }, "values": ["A", "B"] }` |
| **`data_generation`** | Definiuje specjalne zachowanie dla generatora danych. Może być warunkowe. | `{ "action": "data_generation", "condition": { ... }, "generator": "business_sentence" }` |

### C. Słowniki Danych (`.csv`)
*   **Rola:** Dostarczają zewnętrznych danych referencyjnych używanych przez różne moduły aplikacji.
*   **Lokalizacja:** `resources/`
*   **Wymagania:** Pliki muszą być zakodowane w `UTF-8`.

1.  **`CSIRE_Kody_EIC_Operatorow.csv`**
    *   **Cel:** Zawiera listę kodów EIC operatorów. Używany przez generator danych do losowania realistycznych identyfikatorów.
    *   **Wymagane kolumny:** `EIC`, `Name`.
    *   **Separator:** średnik (`;`).
2.  **`Zestawienie_walidacji_w_procesach_CSIRE.csv`**
    *   **Cel:** Definiuje, które kody błędów (CE) są dozwolone w kontekście konkretnych procesów biznesowych. Używany przez generator `generate:error_code_for_process`.
    *   **Struktura:** Plik posiada specyficzny format. Dwie pierwsze linie są ignorowane. Wymagana jest kolumna `Kod błędu` oraz kolumny procesów w formacie `UNK X.Y.Z.A.`.

## Stos Technologiczny
*   **Język:** Python 3
*   **Interfejs Graficzny:** Tkinter (z wykorzystaniem nowoczesnych widgetów `ttk`)
*   **Obsługa XML:** `lxml` (budowanie), `xmlschema` (parsowanie i walidacja schematów)
*   **Generowanie Danych:** `Faker`, `exrex`
*   **Podświetlanie Składni:** `Pygments`

## Struktura Projektu
Projekt jest zorganizowany zgodnie z zasadami czystej architektury, oddzielając logikę biznesową od interfejsu i infrastruktury.

```
csire_message_studio/
│
├── app/
│ ├── controllers/
│ ├── views/
│ │ ├── widgets/
│ │ │ ├── dynamic_form_components/
│ │ │ │ ├── form_data_handler.py
│ │ │ │ ├── form_renderer.py
│ │ │ │ └── rule_engine.py
│ │ │ ├── dynamic_form.py
│ │ │ └── xml_viewer.py
│ └── main.py
│
├── domain/
│ ├── definitions/
│ │ └── message_rules/
│ │ └── 3_1_1_1/
│ ├── dictionaries/
│ └── validation/
│
├── infra/
│
├── services/
│
├── presets/
│
├── resources/
│
└── xsd/
```
    
## Instalacja i Uruchomienie

1.  **Wymagania:** Python 3.8+
2.  **Klonowanie repozytorium:**
    ```bash
    git clone <adres-repozytorium>
    cd csire-message-studio
    ```
3.  **Utworzenie środowiska wirtualnego (zalecane):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Na Windows: venv\Scripts\activate
    ```
4.  **Instalacja zależności:**
    ```bash
    pip install lxml xmlschema faker pygments exrex
    ```
5.  **Struktura katalogów:** Upewnij się, że katalogi `xsd/`, `resources/`, `logs/`, `presets/` oraz `domain/definitions/message_rules/` istnieją w głównym folderze projektu. Umieść odpowiednie pliki `.xsd`, `.csv` oraz pliki z regułami `.json` w przeznaczonych dla nich miejscach.

6.  **Uruchomienie aplikacji:**
    ```bash
    python -m app.main
    ```