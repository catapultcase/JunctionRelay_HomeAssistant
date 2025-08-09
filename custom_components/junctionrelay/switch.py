"""Switch platform for JunctionRelay integration."""
import logging
import aiohttp
import async_timeout

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up JunctionRelay switches from a config entry."""
    host = config_entry.data[CONF_HOST]
    
    # Ensure host has protocol
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"

    switches = []
    
    try:
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{host}/api/homeassistant/junctions/summary") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        _LOGGER.info(f"Received junction data for switches: {data}")
                    else:
                        _LOGGER.error(f"Failed to fetch junctions for switches: HTTP {resp.status}")
                        data = []
    except Exception as e:
        _LOGGER.warning(f"Failed to fetch junctions from {host}: {e}")
        data = []

    # Ensure data is a list
    if not isinstance(data, list):
        _LOGGER.error(f"Expected list, got {type(data)}: {data}")
        data = []

    _LOGGER.info(f"Processing {len(data)} junction switches")
    
    for i, junction in enumerate(data):
        _LOGGER.info(f"Processing junction switch {i}: {junction}")
        
        # Validate junction data
        if not isinstance(junction, dict):
            _LOGGER.warning(f"Junction {i} is not a dict: {junction}")
            continue
            
        if "name" not in junction or "id" not in junction:
            _LOGGER.warning(f"Junction {i} missing required fields: {junction}")
            continue
            
        try:
            switch = JunctionRelaySwitch(junction["name"], junction["id"], host)
            switches.append(switch)
            _LOGGER.info(f"Created switch for junction {junction['name']} (ID: {junction['id']})")
        except Exception as e:
            _LOGGER.error(f"Failed to create switch for junction {i}: {e}")

    if switches:
        _LOGGER.info(f"Adding {len(switches)} JunctionRelay switches to Home Assistant")
        async_add_entities(switches, True)
    else:
        _LOGGER.warning("No valid junction switches found to add")


class JunctionRelaySwitch(SwitchEntity):
    """Representation of a JunctionRelay switch."""

    def __init__(self, name, junction_id, host):
        """Initialize the switch."""
        self._name = name
        self._id = str(junction_id)
        self._host = host
        self._is_on = False
        self._available = True
        self._attr_has_entity_name = True

    @property
    def name(self):
        """Return the name of the switch."""
        return f"Junction {self._name} Control"

    @property
    def unique_id(self):
        """Return the unique ID of the switch."""
        return f"{DOMAIN}_{self._host.replace('http://', '').replace('https://', '').replace(':', '_').replace('/', '_')}_switch_{self._id}"

    @property
    def is_on(self):
        """Return if the switch is on."""
        return self._is_on

    @property
    def available(self):
        """Return if entity is available."""
        return self._available

    @property
    def entity_category(self):
        """Return the category of this entity."""
        return EntityCategory.CONFIG

    @property
    def icon(self):
        """Return the icon for the switch."""
        return "mdi:electric-switch" if self._is_on else "mdi:electric-switch-closed"

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return {
            "junction_id": self._id,
            "junction_name": self._name,
            "host": self._host,
        }

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": "JunctionRelay",
            "manufacturer": "JunctionRelay",
            "model": "Junction Monitor",
            "configuration_url": self._host,
        }

    async def async_turn_on(self, **kwargs):
        """Turn on the junction."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self._host}/api/homeassistant/connections/start/{self._id}") as resp:
                        if resp.status == 200:
                            self._is_on = True
                            self._available = True
                            _LOGGER.info(f"Successfully started junction {self._name} (ID: {self._id})")
                        else:
                            _LOGGER.error(f"Failed to start junction {self._id}: HTTP {resp.status}")
                            # Read response for more details
                            try:
                                error_text = await resp.text()
                                _LOGGER.error(f"Start junction error response: {error_text}")
                            except:
                                pass
                            self._available = False
        except Exception as e:
            _LOGGER.error(f"Error starting junction {self._id}: {e}")
            self._available = False

    async def async_turn_off(self, **kwargs):
        """Turn off the junction."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self._host}/api/homeassistant/connections/stop/{self._id}") as resp:
                        if resp.status == 200:
                            self._is_on = False
                            self._available = True
                            _LOGGER.info(f"Successfully stopped junction {self._name} (ID: {self._id})")
                        else:
                            _LOGGER.error(f"Failed to stop junction {self._id}: HTTP {resp.status}")
                            # Read response for more details
                            try:
                                error_text = await resp.text()
                                _LOGGER.error(f"Stop junction error response: {error_text}")
                            except:
                                pass
                            self._available = False
        except Exception as e:
            _LOGGER.error(f"Error stopping junction {self._id}: {e}")
            self._available = False

    async def async_update(self):
        """Update the switch state."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self._host}/api/homeassistant/junctions/{self._id}") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            status = data.get("status", "Unknown")
                            self._is_on = status.lower() == "running"
                            self._available = True
                        else:
                            _LOGGER.error(f"Failed to update junction switch {self._id}: HTTP {resp.status}")
                            self._available = False
        except Exception as e:
            _LOGGER.warning(f"Failed to update junction switch {self._id}: {e}")
            self._available = False