"""Entity helpers for E-bike Tracker."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class EbikeTrackerEntity(Entity):
    """Base entity for one tracked e-bike."""

    _attr_has_entity_name = True

    def __init__(self, manager, description) -> None:
        """Initialize the entity."""
        self.manager = manager
        self.entity_description = description
        self._attr_unique_id = f"{manager.entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, manager.entry.entry_id)},
            name=manager.name,
            manufacturer="E-bike Tracker",
            model="Tracked e-bike",
        )
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to tracker updates."""
        await super().async_added_to_hass()
        self._remove_listener = self.manager.async_add_listener(
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from tracker updates."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
