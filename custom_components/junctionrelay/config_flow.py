import voluptuous as vol
from homeassistant import config_entries

class JunctionRelayConfigFlow(config_entries.ConfigFlow, domain="junctionrelay"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="JunctionRelay", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
            })
        )
