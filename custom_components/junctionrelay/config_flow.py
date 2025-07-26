"""Config flow for JunctionRelay integration."""
import logging
import voluptuous as vol
import aiohttp
import async_timeout

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
})


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    
    try:
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{host}/api/junctions/summary") as resp:
                    if resp.status != 200:
                        raise CannotConnect
                    await resp.json()
    except Exception:
        raise CannotConnect

    return {"title": "JunctionRelay", "host": host}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JunctionRelay."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Save the host with protocol
            data_with_protocol = user_input.copy()
            data_with_protocol[CONF_HOST] = info["host"]
            return self.async_create_entry(title=info["title"], data=data_with_protocol)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""