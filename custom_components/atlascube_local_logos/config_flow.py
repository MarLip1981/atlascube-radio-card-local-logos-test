"""Config flow for AtlasCube Local Logos."""
from homeassistant import config_entries

from .const import DOMAIN


class AtlasCubeLocalLogosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the integration from the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the integration entry; no user options are required."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="AtlasCube Local Logos", data={})
        return self.async_show_form(step_id="user", data_schema=None)
