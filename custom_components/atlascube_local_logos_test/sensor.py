"""Current server-selected track artwork URLs exposed to Home Assistant and ESPHome."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    small = AtlasCubeArtworkSensor(hass)
    large = AtlasCubeArtworkLargeSensor(hass)
    state = hass.data.setdefault(DOMAIN, {})
    state["artwork_sensor"] = small
    state["artwork_large_sensor"] = large
    async_add_entities([small, large])


class AtlasCubeArtworkSensor(SensorEntity):
    """Expose the lightweight local artwork URL for ESPHome."""

    _attr_has_entity_name = False
    _attr_name = "AtlasCube Radio Cover URL TEST"
    _attr_unique_id = "atlascube_radio_cover_url_test"
    _attr_suggested_object_id = "atlascube_radio_cover_url_test"
    _attr_icon = "mdi:album"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    @property
    def native_value(self) -> str:
        return self.hass.data.get(DOMAIN, {}).get("current_artwork", "none")


class AtlasCubeArtworkLargeSensor(SensorEntity):
    """Expose the high-resolution local artwork URL for the dashboard."""

    _attr_has_entity_name = False
    _attr_name = "AtlasCube Radio Cover URL Large TEST"
    _attr_unique_id = "atlascube_radio_cover_url_large_test"
    _attr_suggested_object_id = "atlascube_radio_cover_url_large_test"
    _attr_icon = "mdi:image"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    @property
    def native_value(self) -> str:
        return self.hass.data.get(DOMAIN, {}).get("current_artwork_large", "none")
