"""Config flow for AtlasCube Local Logos."""
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class AtlasCubeLocalLogosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the integration from the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the integration entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="AtlasCube Local Logos", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return AtlasCubeLocalLogosOptionsFlow()


class AtlasCubeLocalLogosOptionsFlow(config_entries.OptionsFlow):
    """Options flow placeholder compatible with current Home Assistant."""

    async def async_step_init(self, user_input=None):
        """Show an empty options page."""
        if user_input is not None:
            return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="init")
