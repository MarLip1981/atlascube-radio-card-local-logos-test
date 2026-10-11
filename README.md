# AtlasCube Radio Card — TEST LOKALNY DYSK LOGO v0.1.7

Niezależna wersja testowa. Nie zmienia głównej karty AtlasCube ani wcześniejszej karty testowej.

## Instalacja — bez ręcznego dodawania zasobu

1. W HACS zaktualizuj/pobierz repozytorium `MarLip1981/atlascube-radio-card-local-logos-test` jako **Custom repository → Integration**.
2. Uruchom ponownie Home Assistant.
3. Dodaj integrację **AtlasCube Local Logos** (jeśli już jest dodana, nie dodawaj jej ponownie).
4. Odśwież aplikację Home Assistant i otwórz edytor pulpitu.
5. Wyszukaj kartę **AtlasCube Radio Card — TEST LOKALNY DYSK ver0.1.7**.

**Nie dodawaj ręcznie zasobu w Ustawienia → Pulpity → Zasoby.** Integracja sama udostępnia plik JS i rejestruje go. W trybie Lovelace storage dodaje moduł do zasobów Lovelace; w trybie YAML korzysta z mechanizmu dodatkowego modułu JavaScript Home Assistanta. Rozpoznawanie trybu zasobów używa właściwości `resource_mode`.

Jeśli karta nadal nie pojawia się w selektorze, potrzebny będzie wpis z dziennika HA zawierający `AtlasCube`, `lovelace` lub `resource` — nie należy ręcznie dopisywać zasobu, bo chcemy potwierdzić automatyczny przebieg.

## Biblioteka logo

Pliki logo są przechowywane na serwerze HA w `/config/www/atlascube-radio-station-logos/` i udostępniane pod `/local/atlascube-radio-station-logos/<plik>`.

Karta najpierw sprawdza lokalną bibliotekę. Jeśli logo nie istnieje, wybiera wynik według ustalonej kolejności diagnostycznej i zapisuje go na dysku; jeśli diagnostyka nie zwróci kandydatów, używa wyszukiwania zapasowego. Ręczny wybór zapisuje wybrane logo lokalnie; przywrócenie automatycznego wyboru usuwa lokalne nadpisanie i uruchamia ponowne wyszukiwanie. Lokalne adresy obrazów otrzymują znacznik wersji, aby przeglądarka nie pokazywała starego pliku z cache.

## Status

To test integracji, zapisu/odczytu lokalnego logo, ręcznego wyboru i zachowania po restarcie HA.
