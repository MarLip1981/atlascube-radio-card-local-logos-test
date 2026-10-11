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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, LOGO_DIR, MAX_IMAGE_BYTES, WS_GET, WS_LIST, WS_SAVE

_LOGGER = logging.getLogger(__name__)
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
    # The integration itself serves the Lovelace card file, so HACS only needs
    # to install this single integration repository.
    card_path = Path(__file__).parent / "atlascube-radio-card.js"
    await hass.http.async_register_static_paths([
        StaticPathConfig("/atlascube-local-logos/atlascube-radio-card.js", str(card_path), cache_headers=False)
    ])

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
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ensure storage directory exists when integration is added."""
    folder = Path(hass.config.path("www", LOGO_DIR))
    folder.mkdir(parents=True, exist_ok=True)
    hass.data.setdefault(DOMAIN, {})["folder"] = folder
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Keep logo files when integration is unloaded."""
    return True
