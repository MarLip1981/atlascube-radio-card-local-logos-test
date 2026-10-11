# AtlasCube Radio Card — TEST LOKALNY DYSK LOGO v0.1.1

Wersja testowa niezależna od głównej karty AtlasCube. Wersja v0.1.1 ma odrębny typ Lovelace `custom:atlascube-radio-card-local-disk-test` i czerwony pasek TEST na karcie. Projekt zawiera kartę Lovelace i integrację Home Assistant, która przechowuje pobrane logotypy na dysku serwera.

## Instalacja testowa

1. Dodaj repozytorium w HACS jako Custom repository typu Integration.
2. Pobierz repozytorium.
3. Uruchom ponownie Home Assistant.
4. Wejdź w Ustawienia → Urządzenia i usługi → Dodaj integrację i wyszukaj AtlasCube Local Logos.
5. W Lovelace → Zasoby dodaj dokładnie `/atlascube-local-logos/atlascube-radio-card.js?v=0.1.1` jako **Moduł JavaScript**. Jeśli istnieje stary zasób prowadzący do poprzedniej karty testowej, nie używaj go do tej próby.
6. Odśwież aplikację/przeglądarkę Home Assistant. Przy dodawaniu ręcznym wybierz typ `custom:atlascube-radio-card-local-disk-test` — nie poprzedni `custom:atlascube-radio-card-local-logos-test`.

> To repozytorium jest w fazie testów. HACS pobiera kod, ale Home Assistant wymaga dodania integracji z poziomu UI; instalacja HACS nie uruchamia automatycznie integracji.

## Biblioteka

Kod karty jest dostarczany przez samą integrację pod adresem /atlascube-local-logos/atlascube-radio-card.js. Zasób Lovelace trzeba dodać raz w panelu zasobów.

Pliki logo są przechowywane w:
 /config/www/atlascube-radio-station-logos/

Są serwowane przez HA pod adresem:
 /local/atlascube-radio-station-logos/<plik>

Najpierw sprawdzana jest lokalna biblioteka. Gdy pliku nie ma, karta wykonuje wyszukiwanie sieciowe. Po poprawnym znalezieniu i zapisaniu logo kolejne odczyty korzystają z dysku. Ręczny wybór ma zastępować zapisane logo stacji.

## Ważne rozróżnienie testowe

- Typ nowej karty: `custom:atlascube-radio-card-local-disk-test`.
- Zasób JavaScript: `/atlascube-local-logos/atlascube-radio-card.js?v=0.1.1`.
- Jeśli w selektorze widać tylko stary typ karty, sprawdź zasób i odśwież frontend; nie traktuj starej karty jako testu integracji lokalnej.

## Status

Test integracji, zapisu plików, odczytu lokalnego, wyszukiwania, ręcznego wyboru i ponownego uruchomienia HA jest wymagany przed uznaniem wersji za gotową.
