"""Server-side logo cache for the AtlasCube Lovelace card."""
from __future__ import annotations
import ipaddress
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
from .const import DOMAIN, LOGO_DIR, MAX_IMAGE_BYTES, WS_DELETE, WS_GET, WS_LIST, WS_SAVE

_LOGGER = logging.getLogger(__name__)

_CARD_URL = "/atlascube-local-logos/atlascube-radio-card.js"
_CARD_VERSION = "0.1.8"
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
            connection.send_result(msg["id"], {"logo": f"/local/{LOGO_DIR}/{path.name}" if path else None})
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
            connection.send_result(msg["id"], {"removed": removed})
        except (ValueError, OSError) as err:
            connection.send_error(msg["id"], "logo_delete_failed", str(err))

    @websocket_api.websocket_command({
        vol.Required("type"): WS_SAVE,
        vol.Required("station_key"): str,
        vol.Required("station"): str,
        vol.Required("url"): str,
    })
    @websocket_api.async_response
    async def ws_save(hass, connection, msg):
        try:
            key = _safe_key(msg["station_key"])
            url = _public_url(msg["url"])
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
            connection.send_result(msg["id"], {"logo": f"/local/{LOGO_DIR}/{target.name}", "station": msg["station"], "bytes": len(body)})
        except Exception as err:
            _LOGGER.warning("Nie udało się zapisać logo stacji: %s", err)
            connection.send_error(msg["id"], "logo_save_failed", str(err))

    websocket_api.async_register_command(hass, ws_get)
    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_save)
    websocket_api.async_register_command(hass, ws_delete)
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
