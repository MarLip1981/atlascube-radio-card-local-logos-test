"""Config flow for AtlasCube Local Logos."""
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN


class AtlasCubeLocalLogosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the integration from the Home Assistant UI."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="AtlasCube Local Logos", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AtlasCubeLocalLogosOptionsFlow(config_entry)


class AtlasCubeLocalLogosOptionsFlow(config_entries.OptionsFlow):
    """Options flow placeholder."""
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init")
