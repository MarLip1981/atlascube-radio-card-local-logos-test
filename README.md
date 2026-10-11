# AtlasCube Radio Card — TEST LOKALNY DYSK LOGO v0.1.14

Niezależna wersja testowa — kandydat do przyszłej wersji oficjalnej. Nie zmienia głównej karty AtlasCube ani wcześniejszej karty testowej.

## Instalacja — bez ręcznego dodawania zasobu

1. W HACS zaktualizuj/pobierz repozytorium `MarLip1981/atlascube-radio-card-local-logos-test` jako **Custom repository → Integration**.
2. Uruchom ponownie Home Assistant.
3. Dodaj integrację **AtlasCube Local Logos** (jeśli już jest dodana, nie dodawaj jej ponownie).
4. Odśwież aplikację Home Assistant i otwórz edytor pulpitu.
5. Wyszukaj kartę **AtlasCube Radio Card — TEST LOKALNY DYSK ver0.1.14**.

**Nie dodawaj ręcznie zasobu w Ustawienia → Pulpity → Zasoby.** Integracja sama udostępnia plik JS i rejestruje go. W trybie Lovelace storage dodaje moduł do zasobów Lovelace; w trybie YAML korzysta z mechanizmu dodatkowego modułu JavaScript Home Assistanta. Rozpoznawanie trybu zasobów używa właściwości `resource_mode`.

Jeśli karta nadal nie pojawia się w selektorze, potrzebny będzie wpis z dziennika HA zawierający `AtlasCube`, `lovelace` lub `resource` — nie należy ręcznie dopisywać zasobu, bo chcemy potwierdzić automatyczny przebieg.

## Biblioteka logo

Pliki logo są przechowywane na serwerze HA w `/config/www/atlascube-radio-station-logos/` i udostępniane pod `/local/atlascube-radio-station-logos/<plik>`.

Karta najpierw sprawdza lokalną bibliotekę. Jeśli logo nie istnieje, wybiera wynik według ustalonej kolejności diagnostycznej i zapisuje go na dysku; jeśli diagnostyka nie zwróci kandydatów, używa wyszukiwania zapasowego. Ręczny wybór zapisuje wybrane logo lokalnie; przywrócenie automatycznego wyboru usuwa lokalne nadpisanie i uruchamia ponowne wyszukiwanie. Lokalne adresy obrazów otrzymują znacznik wersji, aby przeglądarka nie pokazywała starego pliku z cache.

## Status

To test integracji, zapisu/odczytu lokalnego logo, ręcznego wyboru i zachowania po restarcie HA.



## Wyszukiwanie logo — zachowana logika z testu v0.7

Integracja lokalna nie zastępuje algorytmu wyszukiwania. Zachowuje sprawdzoną kolejność z karty testowej v0.7:

1. Radio Browser po dokładnym adresie URL strumienia z playlisty urządzenia; nazwa wyniku musi pasować i nie może wskazywać innego wariantu stacji.
2. Jeśli nie ma wiarygodnego wyniku, Radio Browser po dokładnej nazwie stacji.
3. Następnie szersze wyszukiwanie Radio Browser po ustalonych aliasach; akceptowane są wyłącznie kanonicznie zgodne nazwy.
4. Wikimedia Commons jest ostatnim fallbackiem, z kontrolą nazwy pliku i odrzucaniem zdjęć oraz konfliktów wariantów.
5. Jeśli źródła nie dają pewnego wyniku, karta pokazuje samą nazwę stacji.

Osobno zachowana jest kolejność kandydatów diagnostycznych v0.7: **NAZWA-2 → SZUKAJ-1 → COMMONS → SZUKAJ-2 → NAZWA-1 → URL-1 → URL-2**. Lista służy wyłącznie do opcjonalnego wyboru ręcznego — nie zastępuje i nie przerywa algorytmu automatycznego.

## Warstwa lokalnego dysku

- Po automatycznym znalezieniu logo integracja zapisuje obraz i źródłowy URL w `/config/www/atlascube-radio-station-logos/`.
- Przy kolejnych odczytach używa zapisanej kopii zamiast pobierać logo za każdym razem.
- Ręczny wybór pozostaje opcją dodatkową, a „Przywróć wybór automatyczny” ponownie uruchamia algorytm v0.7.
- „Odśwież zapisane logo” pobiera obraz ponownie z tego samego źródła.
- Wszystko działa w jednej integracji Home Assistant; nie wymaga drugiej integracji ani osobnego ręcznego zasobu Lovelace.


W wersji 0.1.14 zapytania do Radio Browser i Wikimedia Commons są wykonywane przez backend integracji Home Assistant, a nie bezpośrednio przez przeglądarkę. Błędy połączenia są zapisywane w logu HA zamiast być bezgłośnie zamieniane na puste wyniki.
