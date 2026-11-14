"""Current track artwork URL and internal high-resolution URL for the AtlasCube card."""
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
    sensor = AtlasCubeArtworkSensor(hass)
    state = hass.data.setdefault(DOMAIN, {})
    state["artwork_sensor"] = sensor
    async_add_entities([sensor])


class AtlasCubeArtworkSensor(SensorEntity):
    """Expose the lightweight URL as state and the dashboard URL as an attribute."""

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

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Keep the large dashboard URL internal to this single HA entity."""
        return {
            "artwork_large": self.hass.data.get(DOMAIN, {}).get(
                "current_artwork_large", "none"
            )
        }
