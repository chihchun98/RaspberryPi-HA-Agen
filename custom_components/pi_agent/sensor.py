"""Sensor platform for Pi Agent."""
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pi Agent sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    device_name = entry.title
    mac = entry.data.get("mac", "unknown_mac")
    
    sensors = [
        PiAgentSensor(coordinator, device_name, mac, "cpu_percent", "CPU Usage", "%", None, SensorStateClass.MEASUREMENT),
        PiAgentSensor(coordinator, device_name, mac, "ram_percent", "RAM Usage", "%", None, SensorStateClass.MEASUREMENT),
        PiAgentSensor(coordinator, device_name, mac, "temperature", "Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        PiAgentSensor(coordinator, device_name, mac, "uptime", "Uptime", "s", SensorDeviceClass.DURATION, SensorStateClass.TOTAL_INCREASING),
        PiAgentSensor(coordinator, device_name, mac, "power_w", "Estimated Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    ]
    
    async_add_entities(sensors)

class PiAgentSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pi Agent sensor."""

    def __init__(self, coordinator, device_name, mac, key, name, unit, device_class, state_class):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{device_name} {name}"
        self._attr_unique_id = f"{mac}_{key}"
        self._attr_native_unit_of_measurement = unit
        if device_class:
            self._attr_device_class = device_class
        if state_class:
            self._attr_state_class = state_class

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "name": device_name,
            "manufacturer": "Raspberry Pi",
            "model": "Pi Agent Node",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data or "metrics" not in self.coordinator.data:
            return None
        return self.coordinator.data["metrics"].get(self._key)
