from homeassistant.helpers.entity import Entity

async def async_setup_entry(hass, config_entry, async_add_entities):
    host = config_entry.data["host"]
    # You would fetch your junction data here, but this is a placeholder
    async_add_entities([JunctionRelaySensor("Test Junction", host)], True)

class JunctionRelaySensor(Entity):
    def __init__(self, name, host):
        self._name = name
        self._state = "Idle"
        self._host = host

    @property
    def name(self):
        return f"JunctionRelay {self._name}"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        # Fetch from backend (placeholder)
        self._state = "Active"
