"""Sensor platform for JunctionRelay integration."""
import logging
import aiohttp
import async_timeout

from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_HOST

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up JunctionRelay sensors from a config entry."""
    host = config_entry.data[CONF_HOST]
    
    # Ensure host has protocol
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"

    sensors = []
    
    try:
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{host}/api/junctions/summary") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                    else:
                        _LOGGER.error(f"Failed to fetch junctions: HTTP {resp.status}")
                        data = []
    except Exception as e:
        _LOGGER.warning(f"Failed to fetch junctions from {host}: {e}")
        data = []

    for junction in data:
        sensors.append(JunctionRelaySensor(junction["name"], junction["id"], host))

    if sensors:
        async_add_entities(sensors, True)
        _LOGGER.info(f"Added {len(sensors)} JunctionRelay sensors")
    else:
        _LOGGER.warning("No junction sensors found")


class JunctionRelaySensor(Entity):
    """Representation of a JunctionRelay sensor."""

    def __init__(self, name, junction_id, host):
        """Initialize the sensor."""
        self._name = name
        self._id = junction_id
        self._host = host
        self._state = None
        self._available = True

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"JunctionRelay {self._name}"

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return f"junctionrelay_{self._id}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def available(self):
        """Return if entity is available."""
        return self._available

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": "JunctionRelay",
            "manufacturer": "JunctionRelay",
            "model": "Junction Monitor",
        }

    async def async_update(self):
        """Update the sensor."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self._host}/api/junctions/{self._id}") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self._state = data.get("status", "Unknown")
                            self._available = True
                        else:
                            _LOGGER.error(f"Failed to update junction {self._id}: HTTP {resp.status}")
                            self._available = False
        except Exception as e:
            _LOGGER.warning(f"Failed to update junction {self._id}: {e}")
            self._state = "Unavailable"
            self._available = False