"""Current track artwork exposed to ESPHome."""
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
    """Set up the current artwork URL sensor."""
    entity = AtlasCubeArtworkSensor(hass)
    hass.data.setdefault(DOMAIN, {})["artwork_sensor"] = entity
    async_add_entities([entity])


class AtlasCubeArtworkSensor(SensorEntity):
    """Expose the local URL of the artwork currently selected by the card."""

    _attr_has_entity_name = False
    _attr_name = "AtlasCube Radio Cover URL"
    _attr_unique_id = "atlascube_radio_cover_url"
    _attr_suggested_object_id = "atlascube_radio_cover_url"
    _attr_icon = "mdi:album"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    @property
    def native_value(self) -> str:
        """Return a relative local URL, or 'none' when no cover is available."""
        return self.hass.data.get(DOMAIN, {}).get("current_artwork", "none")
