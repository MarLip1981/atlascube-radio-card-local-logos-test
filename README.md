# AtlasCube Radio Card — TEST LOKALNY DYSK LOGO v0.1.2

To jest niezależna wersja testowa. Nie zmienia głównej karty AtlasCube ani wcześniejszej karty testowej z wyszukiwaniem logo.

## Instalacja — bez ręcznego dodawania zasobu JS

1. W HACS dodaj repozytorium `MarLip1981/atlascube-radio-card-local-logos-test` jako **Custom repository → Integration**.
2. Pobierz/zaaktualizuj integrację.
3. Uruchom ponownie Home Assistant.
4. Wejdź w **Ustawienia → Urządzenia i usługi → Dodaj integrację** i dodaj **AtlasCube Local Logos**.
5. Odśwież aplikację Home Assistant (jeśli karta nie pojawi się od razu, zamknij i otwórz aplikację ponownie).
6. W edytorze pulpitu dodaj kartę **AtlasCube Radio Card — TEST LOKALNY DYSK ver0.1.2**.

**Nie dodawaj ręcznie zasobu w Ustawienia → Pulpity → Zasoby.** Integracja sama udostępnia plik JS i rejestruje go w zasobach Lovelace. W logu HA powinien pojawić się wpis o automatycznej rejestracji.

Dodanie samej karty do wybranego pulpitu pozostaje osobnym krokiem wykonywanym w interfejsie Home Assistanta.

## Biblioteka logo

Pliki logo są przechowywane na serwerze HA w:

`/config/www/atlascube-radio-station-logos/`

i udostępniane pod adresem:

`/local/atlascube-radio-station-logos/<plik>`

Karta najpierw sprawdza lokalną bibliotekę. Jeśli logo nie istnieje, wyszukuje je online i próbuje zapisać wybrane logo na dysku. Ręczny wybór logo zapisuje wybraną wersję lokalnie; przywrócenie automatycznego wyboru usuwa lokalne nadpisanie i uruchamia ponowne wyszukiwanie.

## Ważne w pierwszym teście

- Typ karty: `custom:atlascube-radio-card-local-disk-test`.
- Zasób JS rejestrowany automatycznie: `/atlascube-local-logos/atlascube-radio-card.js?v=0.1.2`.
- Pliki logo pozostają na dysku także po usunięciu i ponownym dodaniu integracji.
- To wersja testowa; trzeba potwierdzić automatyczną rejestrację, wybór karty, pobieranie i zapis logo, ponowne użycie lokalnego pliku oraz zachowanie po restarcie HA.
