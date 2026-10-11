"""Server-side logo cache for the AtlasCube Lovelace card."""
from __future__ import annotations
import ipaddress
import json
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, LOGO_DIR, MAX_IMAGE_BYTES, WS_DELETE, WS_GET, WS_LIST, WS_SAVE, WS_REFRESH, WS_SEARCH

_LOGGER = logging.getLogger(__name__)

_CARD_URL = "/atlascube-local-logos/atlascube-radio-card.js"
_CARD_VERSION = "0.1.14"
_RESOURCE_URL = f"{_CARD_URL}?v={_CARD_VERSION}"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the bundled card and register it in Lovelace automatically."""
    card_path = Path(__file__).parent / "atlascube-radio-card.js"

    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(_CARD_URL, str(card_path), cache_headers=False)
        ])
    except Exception as err:  # noqa: BLE001
        # A duplicate route can occur after an integration reload. Continue only
        # for that known case; other failures should be visible in the HA log.
        message = str(err).lower()
        if "already registered" not in message and "duplicate" not in message:
            _LOGGER.warning("Nie udało się zarejestrować pliku karty AtlasCube: %s", err)
            return

    # Use Home Assistant's typed data key rather than a string literal.
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        _LOGGER.warning(
            "Karta AtlasCube jest dostępna pod %s, ale Lovelace nie udostępnił rejestru zasobów.",
            _CARD_URL,
        )
        return

    # YAML mode is read-only. Register the module through Home Assistant's
    # frontend helper instead of trying to write to the YAML resource list.
    if getattr(lovelace, "resource_mode", "storage") == "yaml":
        add_extra_js_url(hass, _RESOURCE_URL)
        _LOGGER.info("Zarejestrowano kartę AtlasCube jako dodatkowy moduł JS.")
        return

    resources = getattr(lovelace, "resources", None)
    if resources is None:
        _LOGGER.warning("Nie znaleziono rejestru zasobów Lovelace dla karty AtlasCube.")
        return

    try:
        # ResourceStorageCollection is lazy-loaded. Load it before async_items
        # or async_create_item to avoid overwriting existing dashboard resources.
        if not getattr(resources, "loaded", True):
            await resources.async_load()

        existing = list(resources.async_items())
        matching = [
            item for item in existing
            if str(item.get("url", "")).split("?", 1)[0] == _CARD_URL
        ]
        if matching:
            primary = matching[0]
            if primary.get("url") != _RESOURCE_URL or primary.get("res_type") != "module":
                await resources.async_update_item(
                    primary["id"], {"res_type": "module", "url": _RESOURCE_URL}
                )
            # Remove duplicates of this integration's URL, if any.
            for duplicate in matching[1:]:
                await resources.async_delete_item(duplicate["id"])
            _LOGGER.info("Zasób karty AtlasCube jest już zarejestrowany: %s", _RESOURCE_URL)
            return

        await resources.async_create_item({"res_type": "module", "url": _RESOURCE_URL})
        _LOGGER.info("Automatycznie dodano zasób karty AtlasCube do Lovelace: %s", _RESOURCE_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception(
            "Nie udało się automatycznie dodać zasobu karty AtlasCube. "
            "Karta może wymagać ponownego uruchomienia HA: %s", err
        )


_EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "image/x-icon": ".ico", "image/vnd.microsoft.icon": ".ico", "image/avif": ".avif"}


def _safe_key(value: str) -> str:
    value = str(value or "").strip().lower().encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value or value in {".", ".."}:
        raise ValueError("Nieprawidłowa nazwa stacji")
    return value[:100]


def _public_url(value: str) -> str:
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Dozwolone są tylko adresy HTTP/HTTPS")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".lan")):
        raise ValueError("Lokalne adresy źródłowe są zablokowane")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None and not ip.is_global:
        raise ValueError("Prywatne adresy IP są zablokowane")
    if parsed.username or parsed.password:
        raise ValueError("Adres z danymi logowania jest niedozwolony")
    return parsed.geturl()


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register websocket commands and prepare the local folder."""
    folder = Path(hass.config.path("www", LOGO_DIR))
    folder.mkdir(parents=True, exist_ok=True)
    hass.data.setdefault(DOMAIN, {})["folder"] = folder

    @websocket_api.websocket_command({vol.Required("type"): WS_GET, vol.Required("station_key"): str})
    @websocket_api.async_response
    async def ws_get(hass, connection, msg):
        try:
            key = _safe_key(msg["station_key"])
            folder = hass.data[DOMAIN]["folder"]
            path = next((folder / f"{key}{ext}" for ext in _EXTENSIONS.values() if (folder / f"{key}{ext}").is_file()), None)
            metadata_path = folder / f"{key}.json"
            metadata = {}
            if metadata_path.is_file():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    metadata = {}
            connection.send_result(msg["id"], {
                "logo": f"/local/{LOGO_DIR}/{path.name}" if path else None,
                "selection_mode": metadata.get("selection_mode", "legacy"),
                "algorithm_version": metadata.get("algorithm_version"),
                "source_url": metadata.get("source_url"),
            })
        except (ValueError, OSError) as err:
            connection.send_error(msg["id"], "invalid_station", str(err))

    @websocket_api.websocket_command({vol.Required("type"): WS_LIST})
    @websocket_api.async_response
    async def ws_list(hass, connection, msg):
        folder = hass.data[DOMAIN]["folder"]
        folder.mkdir(parents=True, exist_ok=True)
        logos = [{"key": p.stem, "logo": f"/local/{LOGO_DIR}/{p.name}"} for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in _EXTENSIONS.values()]
        connection.send_result(msg["id"], {"logos": logos})

    @websocket_api.websocket_command({vol.Required("type"): WS_DELETE, vol.Required("station_key"): str})
    @websocket_api.async_response
    async def ws_delete(hass, connection, msg):
        try:
            key = _safe_key(msg["station_key"])
            folder = hass.data[DOMAIN]["folder"]
            removed = False
            for ext in _EXTENSIONS.values():
                path = folder / f"{key}{ext}"
                if path.is_file():
                    path.unlink()
                    removed = True
            metadata = folder / f"{key}.json"
            if metadata.is_file():
                metadata.unlink()
                removed = True
            connection.send_result(msg["id"], {"removed": removed})
        except (ValueError, OSError) as err:
            connection.send_error(msg["id"], "logo_delete_failed", str(err))

    @websocket_api.websocket_command({
        vol.Required("type"): WS_SAVE,
        vol.Required("station_key"): str,
        vol.Required("station"): str,
        vol.Required("url"): str,
        vol.Optional("selection_mode", default="automatic"): str,
    })
    @websocket_api.async_response
    async def ws_save(hass, connection, msg):
        try:
            key = _safe_key(msg["station_key"])
            url = _public_url(msg["url"])
            selection_mode = msg.get("selection_mode", "automatic")
            if selection_mode not in {"automatic", "manual"}:
                raise ValueError("Nieprawidłowy tryb wyboru logo")
            session = async_get_clientsession(hass)
            # Walidujemy każdy skok przekierowania osobno, zanim wykonamy następne żądanie.
            current_url = url
            body = b""
            content_type = ""
            for redirect_count in range(4):
                current_url = _public_url(current_url)
                async with session.get(current_url, allow_redirects=False, timeout=15) as response:
                    if response.status in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location")
                        if not location or redirect_count == 3:
                            raise ValueError("Za dużo lub nieprawidłowe przekierowania źródła logo")
                        current_url = urljoin(current_url, location)
                        continue
                    if response.status != 200:
                        raise ValueError(f"Źródło logo zwróciło HTTP {response.status}")
                    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                    if content_type not in _EXTENSIONS:
                        raise ValueError("Źródło nie zwróciło obsługiwanego obrazu PNG/JPEG/WebP/GIF/ICO/AVIF")
                    if response.content_length is not None and response.content_length > MAX_IMAGE_BYTES:
                        raise ValueError("Logo przekracza limit 2 MB")
                    body = await response.content.read(MAX_IMAGE_BYTES + 1)
                    if not body or len(body) > MAX_IMAGE_BYTES:
                        raise ValueError("Pusty obraz lub przekroczony limit 2 MB")
                    break
            else:
                raise ValueError("Nie udało się pobrać logo")
            folder = hass.data[DOMAIN]["folder"]
            folder.mkdir(parents=True, exist_ok=True)
            ext = _EXTENSIONS[content_type]
            target = folder / f"{key}{ext}"
            for old_ext in _EXTENSIONS.values():
                old = folder / f"{key}{old_ext}"
                if old.exists() and old != target:
                    old.unlink()
            target.write_bytes(body)
            # Zapamiętujemy dokładny adres źródłowy, aby Odśwież pobierał ten sam wariant logo.
            metadata = folder / f"{key}.json"
            metadata.write_text(json.dumps({
                "source_url": url,
                "content_type": content_type,
                "selection_mode": selection_mode,
                "algorithm_version": "0.1.14",
            }, ensure_ascii=False), encoding="utf-8")
            connection.send_result(msg["id"], {
                "logo": f"/local/{LOGO_DIR}/{target.name}",
                "station": msg["station"],
                "bytes": len(body),
                "source_url": url,
                "selection_mode": selection_mode,
                "algorithm_version": "0.1.14",
            })
        except Exception as err:
            _LOGGER.warning("Nie udało się zapisać logo stacji: %s", err)
            connection.send_error(msg["id"], "logo_save_failed", str(err))

    @websocket_api.websocket_command({
        vol.Required("type"): WS_REFRESH,
        vol.Required("station_key"): str,
    })
    @websocket_api.async_response
    async def ws_refresh(hass, connection, msg):
        """Re-download the exact source URL previously used for this station."""
        try:
            key = _safe_key(msg["station_key"])
            folder = hass.data[DOMAIN]["folder"]
            metadata_path = folder / f"{key}.json"
            if not metadata_path.is_file():
                raise ValueError("Brak zapisanego adresu źródłowego dla tego logo. Wybierz logo ponownie z listy.")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            url = _public_url(metadata.get("source_url", ""))
            session = async_get_clientsession(hass)
            current_url = url
            body = b""
            content_type = ""
            for redirect_count in range(4):
                current_url = _public_url(current_url)
                async with session.get(current_url, allow_redirects=False, timeout=15) as response:
                    if response.status in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location")
                        if not location or redirect_count == 3:
                            raise ValueError("Za dużo lub nieprawidłowe przekierowania źródła logo")
                        current_url = urljoin(current_url, location)
                        continue
                    if response.status != 200:
                        raise ValueError(f"Źródło logo zwróciło HTTP {response.status}")
                    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                    if content_type not in _EXTENSIONS:
                        raise ValueError("Źródło nie zwróciło obsługiwanego obrazu PNG/JPEG/WebP/GIF/ICO/AVIF")
                    if response.content_length is not None and response.content_length > MAX_IMAGE_BYTES:
                        raise ValueError("Logo przekracza limit 2 MB")
                    body = await response.content.read(MAX_IMAGE_BYTES + 1)
                    if not body or len(body) > MAX_IMAGE_BYTES:
                        raise ValueError("Pusty obraz lub przekroczony limit 2 MB")
                    break
            else:
                raise ValueError("Nie udało się pobrać logo")
            ext = _EXTENSIONS[content_type]
            target = folder / f"{key}{ext}"
            for old_ext in _EXTENSIONS.values():
                old = folder / f"{key}{old_ext}"
                if old.exists() and old != target:
                    old.unlink()
            target.write_bytes(body)
            metadata["source_url"] = url
            metadata["content_type"] = content_type
            metadata["selection_mode"] = metadata.get("selection_mode", "legacy")
            metadata["algorithm_version"] = "0.1.14"
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
            connection.send_result(msg["id"], {
                "logo": f"/local/{LOGO_DIR}/{target.name}",
                "source_url": url,
                "selection_mode": metadata["selection_mode"],
                "bytes": len(body),
                "refreshed": True,
            })
        except Exception as err:
            _LOGGER.warning("Nie udało się odświeżyć logo stacji: %s", err)
            connection.send_error(msg["id"], "logo_refresh_failed", str(err))

    @websocket_api.websocket_command({
        vol.Required("type"): WS_SEARCH,
        vol.Required("provider"): vol.In(["radio_browser", "commons"]),
        vol.Optional("path"): str,
        vol.Optional("query"): str,
    })
    @websocket_api.async_response
    async def ws_search(hass, connection, msg):
        """Query logo sources server-side instead of relying on browser cross-origin requests."""
        session = async_get_clientsession(hass)
        provider = msg["provider"]
        try:
            if provider == "radio_browser":
                path = str(msg.get("path", ""))
                allowed_path = re.fullmatch(
                    r"/json/stations/(?:byurl|search)(?:\?[^#]*)?|/json/stations/bynameexact/[^/?#]+(?:\?[^#]*)?",
                    path,
                )
                if not allowed_path:
                    raise ValueError("Niedozwolona ścieżka wyszukiwania Radio Browser")
                last_error = "brak odpowiedzi"
                for host in ("all.api.radio-browser.info", "de1.api.radio-browser.info", "fi1.api.radio-browser.info"):
                    try:
                        async with session.get(
                            "https://" + host + path,
                            headers={"Accept": "application/json", "User-Agent": "AtlasCube-Local-Logos/0.1.14"},
                            timeout=12,
                        ) as response:
                            if response.status != 200:
                                last_error = f"{host}: HTTP {response.status}"
                                continue
                            data = await response.json(content_type=None)
                            if isinstance(data, list):
                                connection.send_result(msg["id"], {"results": data, "provider": provider, "host": host})
                                return
                            last_error = f"{host}: odpowiedź nie jest listą JSON"
                    except Exception as err:  # noqa: BLE001
                        last_error = f"{host}: {err}"
                raise ValueError("Radio Browser nie zwrócił wyników (" + last_error + ")")

            query = str(msg.get("query", "")).strip()
            if not query or len(query) > 200:
                raise ValueError("Nieprawidłowe zapytanie Wikimedia Commons")
            params = {
                "action": "query", "generator": "search", "gsrsearch": query,
                "gsrnamespace": "6", "gsrlimit": "20", "prop": "imageinfo",
                "iiprop": "url", "iiurlwidth": "500", "format": "json", "origin": "*",
            }
            async with session.get(
                "https://commons.wikimedia.org/w/api.php",
                params=params,
                headers={"Accept": "application/json", "User-Agent": "AtlasCube-Local-Logos/0.1.14 (Home Assistant integration)"},
                timeout=15,
            ) as response:
                if response.status != 200:
                    raise ValueError(f"Wikimedia Commons zwróciło HTTP {response.status}")
                data = await response.json(content_type=None)
            pages = list((data.get("query", {}).get("pages") or {}).values())
            connection.send_result(msg["id"], {"pages": pages, "provider": provider, "count": len(pages)})
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Wyszukiwanie logo (%s) nie powiodło się: %s", provider, err)
            connection.send_error(msg["id"], "logo_search_failed", str(err))

    websocket_api.async_register_command(hass, ws_get)
    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_save)
    websocket_api.async_register_command(hass, ws_delete)
    websocket_api.async_register_command(hass, ws_refresh)
    websocket_api.async_register_command(hass, ws_search)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ensure storage directory exists when integration is added."""
    folder = Path(hass.config.path("www", LOGO_DIR))
    folder.mkdir(parents=True, exist_ok=True)
    hass.data.setdefault(DOMAIN, {})["folder"] = folder
    # Config-entry setup also runs when the user adds the integration after HA
    # has already started, so registration must happen here rather than waiting
    # for EVENT_HOMEASSISTANT_STARTED.
    await _async_register_frontend(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Keep logo files when integration is unloaded."""
    return True
