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
                async with session.get(f"{host}/api/homeassistant/junctions/summary") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        _LOGGER.info(f"Received junction data for sensors: {data}")
                    else:
                        _LOGGER.error(f"Failed to fetch junctions for sensors: HTTP {resp.status}")
                        data = []
    except Exception as e:
        _LOGGER.warning(f"Failed to fetch junctions from {host}: {e}")
        data = []

    # Ensure data is a list
    if not isinstance(data, list):
        _LOGGER.error(f"Expected list, got {type(data)}: {data}")
        data = []

    _LOGGER.info(f"Processing {len(data)} junction sensors")
    
    for i, junction in enumerate(data):
        _LOGGER.info(f"Processing junction sensor {i}: {junction}")
        
        # Validate junction data
        if not isinstance(junction, dict):
            _LOGGER.warning(f"Junction {i} is not a dict: {junction}")
            continue
            
        if "name" not in junction or "id" not in junction:
            _LOGGER.warning(f"Junction {i} missing required fields: {junction}")
            continue
            
        try:
            sensor = JunctionRelaySensor(junction["name"], junction["id"], host)
            sensors.append(sensor)
            _LOGGER.info(f"Created sensor for junction {junction['name']} (ID: {junction['id']})")
        except Exception as e:
            _LOGGER.error(f"Failed to create sensor for junction {i}: {e}")

    if sensors:
        _LOGGER.info(f"Adding {len(sensors)} JunctionRelay sensors to Home Assistant")
        async_add_entities(sensors, True)
    else:
        _LOGGER.warning("No valid junction sensors found to add")


class JunctionRelaySensor(Entity):
    """Representation of a JunctionRelay sensor."""

    def __init__(self, name, junction_id, host):
        """Initialize the sensor."""
        self._name = name
        self._id = str(junction_id)
        self._host = host
        self._state = None
        self._available = True
        self._attr_has_entity_name = True

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Junction {self._name} Status"

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return f"{DOMAIN}_{self._host.replace('http://', '').replace('https://', '').replace(':', '_').replace('/', '_')}_sensor_{self._id}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def available(self):
        """Return if entity is available."""
        return self._available

    @property
    def icon(self):
        """Return the icon for the sensor."""
        if self._state == "Running":
            return "mdi:play-circle"
        elif self._state == "Idle":
            return "mdi:pause-circle"
        else:
            return "mdi:help-circle"

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

    async def async_update(self):
        """Update the sensor."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self._host}/api/homeassistant/junctions/{self._id}") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self._state = data.get("status", "Unknown")
                            self._available = True
                        else:
                            _LOGGER.error(f"Failed to update junction sensor {self._id}: HTTP {resp.status}")
                            self._available = False
        except Exception as e:
            _LOGGER.warning(f"Failed to update junction sensor {self._id}: {e}")
            self._state = "Unavailable"
            self._available = False