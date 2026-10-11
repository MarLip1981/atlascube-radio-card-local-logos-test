# AtlasCube Radio Card — TEST LOCAL LOGOS

Wersja testowa niezależna od głównej karty AtlasCube. Projekt zawiera kartę Lovelace i integrację Home Assistant, która przechowuje pobrane logotypy na dysku serwera.

## Instalacja testowa

1. Dodaj repozytorium w HACS jako Custom repository typu Integration.
2. Pobierz repozytorium.
3. Uruchom ponownie Home Assistant.
4. Wejdź w Ustawienia → Urządzenia i usługi → Dodaj integrację i wyszukaj AtlasCube Local Logos.
5. Dodaj zasób karty Lovelace wskazujący na /atlascube-local-logos/atlascube-radio-card.js i odśwież przeglądarkę.

> To repozytorium jest w fazie testów. HACS pobiera kod, ale Home Assistant wymaga dodania integracji z poziomu UI; instalacja HACS nie uruchamia automatycznie integracji.

## Biblioteka

Kod karty jest dostarczany przez samą integrację pod adresem /atlascube-local-logos/atlascube-radio-card.js. Zasób Lovelace trzeba dodać raz w panelu zasobów.

Pliki logo są przechowywane w:
 /config/www/atlascube-radio-station-logos/

Są serwowane przez HA pod adresem:
 /local/atlascube-radio-station-logos/<plik>

Najpierw sprawdzana jest lokalna biblioteka. Gdy pliku nie ma, karta wykonuje wyszukiwanie sieciowe. Po poprawnym znalezieniu i zapisaniu logo kolejne odczyty korzystają z dysku. Ręczny wybór ma zastępować zapisane logo stacji.

## Status

Test integracji, zapisu plików, odczytu lokalnego, wyszukiwania, ręcznego wyboru i ponownego uruchomienia HA jest wymagany przed uznaniem wersji za gotową.
