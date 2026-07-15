"""Binary sensor entities for E-bike Tracker."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import DOMAIN
from .entity import EbikeTrackerEntity

CHARGING_DESCRIPTION = BinarySensorEntityDescription(
    key="charging",
    translation_key="charging",
    device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up binary sensor entities."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EbikeChargingBinarySensor(manager, CHARGING_DESCRIPTION)])


class EbikeChargingBinarySensor(EbikeTrackerEntity, BinarySensorEntity):
    """Charging state sensor."""

    @property
    def is_on(self) -> bool | None:
        """Return whether the bike is charging."""
        return self.manager.is_charging()
