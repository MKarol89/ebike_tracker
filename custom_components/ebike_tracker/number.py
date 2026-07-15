"""Number entities for E-bike Tracker."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import UnitOfLength

from .const import DOMAIN
from .entity import EbikeTrackerEntity

ODOMETER_DESCRIPTION = NumberEntityDescription(
    key="odometer_input",
    translation_key="odometer_input",
    native_min_value=0,
    native_step=0.1,
    native_unit_of_measurement=UnitOfLength.KILOMETERS,
    mode=NumberMode.BOX,
    device_class=NumberDeviceClass.DISTANCE,
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up number entities."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EbikeOdometerNumber(manager, ODOMETER_DESCRIPTION)])


class EbikeOdometerNumber(EbikeTrackerEntity, RestoreNumber, NumberEntity):
    """Editable total odometer."""

    @property
    def native_value(self) -> float:
        """Return current odometer value."""
        return self.manager.rounded(self.manager.current_odometer_km, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set current odometer value."""
        await self.manager.async_set_odometer(value, allow_decrease=False)
