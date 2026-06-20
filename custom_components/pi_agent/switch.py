"""Switch platform for Pi Agent services."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pi Agent switches based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    host = hass.data[DOMAIN][entry.entry_id]["host"]
    port = hass.data[DOMAIN][entry.entry_id]["port"]
    
    device_name = entry.title
    mac = entry.data.get("mac", "unknown_mac")
    
    tracked_services = set()

    @callback
    def handle_coordinator_update() -> None:
        """Handle updated data from the coordinator."""
        if not coordinator.data or "services" not in coordinator.data:
            return
            
        new_switches = []
        current_services = {srv["id"]: srv for srv in coordinator.data["services"]}
        
        # 1. Clean up orphaned entities from HA registry on startup or dynamically
        from homeassistant.helpers import entity_registry as er
        entity_reg = er.async_get(hass)
        entries = er.async_entries_for_config_entry(entity_reg, entry.entry_id)
        
        for entity_entry in entries:
            # unique_id is format: {mac}_switch_{service_id}
            if "_switch_" in entity_entry.unique_id:
                svc_id = entity_entry.unique_id.split("_switch_", 1)[1]
                # If the service no longer exists, wipe it from HA registry completely
                if svc_id not in current_services:
                    entity_reg.async_remove(entity_entry.entity_id)
                    
        # 2. Add new entities
        for service_id, service in current_services.items():
            if service_id not in tracked_services:
                tracked_services.add(service_id)
                new_switches.append(
                    PiAgentServiceSwitch(
                        coordinator, host, port, device_name, mac,
                        service_id, service["name"], service["type"]
                    )
                )
        
        if new_switches:
            async_add_entities(new_switches)

    # Listen for updates to dynamically add new entities
    coordinator.async_add_listener(handle_coordinator_update)
    
    # Run once initially
    handle_coordinator_update()

class PiAgentServiceSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Pi Agent service switch."""

    def __init__(self, coordinator, host, port, device_name, mac, service_id, service_name, service_type):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._host = host
        self._port = port
        self._service_id = service_id
        
        if service_type == "usb":
            prefix = "USB"
            self._attr_icon = "mdi:usb-flash-drive"
        elif service_type == "docker":
            prefix = "Docker"
            self._attr_icon = "mdi:docker"
        else:
            prefix = "System"
            self._attr_icon = "mdi:cog"
            
        self._attr_name = f"{device_name} {prefix}: {service_name}"
        self._attr_unique_id = f"{mac}_switch_{service_id}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "name": device_name,
            "manufacturer": "Raspberry Pi",
            "model": "Pi Agent Node",
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator and self-destruct if removed."""
        if self.coordinator.data and "services" in self.coordinator.data:
            exists = any(srv["id"] == self._service_id for srv in self.coordinator.data["services"])
            if not exists:
                # The service/USB is gone, remove this entity from HA
                self.hass.async_create_task(self.async_remove(force_remove=True))
                return
        super()._handle_coordinator_update()

    @property
    def is_on(self):
        """Return true if the service is running/mounted."""
        if not self.coordinator.data or "services" not in self.coordinator.data:
            return False
            
        for srv in self.coordinator.data["services"]:
            if srv["id"] == self._service_id:
                return srv["state"] == "running"
        return False

    async def async_turn_on(self, **kwargs):
        """Turn the service/mount on."""
        await self._async_control_service("start")

    async def async_turn_off(self, **kwargs):
        """Turn the service/unmount off."""
        await self._async_control_service("stop")

    async def _async_control_service(self, action: str):
        """Send command to Pi Agent to control the service."""
        url = f"http://{self._host}:{self._port}/api/services/{self._service_id}"
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(url, json={"action": action}, timeout=10) as response:
                response.raise_for_status()
                # Immediately refresh the coordinator to get the new state
                await self.coordinator.async_request_refresh()
        except Exception as e:
            pass
