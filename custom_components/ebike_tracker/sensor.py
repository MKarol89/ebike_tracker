"""Sensor entities for E-bike Tracker."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfLength, UnitOfPower

from .const import ATTR_BATTERY_CAPACITY_WH, DOMAIN
from .entity import EbikeTrackerEntity

UNIT_KWH_PER_100_KM = "kWh/100 km"
UNIT_WH_PER_KM = "Wh/km"
UNIT_PLN = "PLN"
UNIT_PLN_PER_100_KM = "PLN/100 km"


@dataclass(frozen=True, kw_only=True)
class EbikeSensorEntityDescription(SensorEntityDescription):
    """Description for e-bike sensors."""

    value_fn: Callable
    round_digits: int = 3


SENSOR_DESCRIPTIONS = (
    EbikeSensorEntityDescription(
        key="total_odometer",
        translation_key="total_odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda manager: manager.current_odometer_km,
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="distance_since_start",
        translation_key="distance_since_start",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda manager: manager.total_distance_km(),
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="daily_distance",
        translation_key="daily_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.day_distance_km(),
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="weekly_distance",
        translation_key="weekly_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.week_distance_km(),
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="monthly_distance",
        translation_key="monthly_distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.month_distance_km(),
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="average_daily_distance_7d",
        translation_key="average_daily_distance_7d",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.average_distance_km(7),
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="average_daily_distance_30d",
        translation_key="average_daily_distance_30d",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.average_distance_km(30),
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="total_energy",
        translation_key="total_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda manager: manager.total_energy_kwh(),
    ),
    EbikeSensorEntityDescription(
        key="weekly_energy",
        translation_key="weekly_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.week_energy_kwh(),
    ),
    EbikeSensorEntityDescription(
        key="monthly_energy",
        translation_key="monthly_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.month_energy_kwh(),
    ),
    EbikeSensorEntityDescription(
        key="kwh_per_100_km",
        translation_key="kwh_per_100_km",
        native_unit_of_measurement=UNIT_KWH_PER_100_KM,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.kwh_100_km(),
    ),
    EbikeSensorEntityDescription(
        key="wh_per_km",
        translation_key="wh_per_km",
        native_unit_of_measurement=UNIT_WH_PER_KM,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.wh_km(),
    ),
    EbikeSensorEntityDescription(
        key="cost_per_100_km",
        translation_key="cost_per_100_km",
        native_unit_of_measurement=UNIT_PLN_PER_100_KM,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.cost_100_km(),
    ),
    EbikeSensorEntityDescription(
        key="total_energy_cost",
        translation_key="total_energy_cost",
        native_unit_of_measurement=UNIT_PLN,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda manager: manager.total_cost(),
        round_digits=2,
    ),
    EbikeSensorEntityDescription(
        key="charging_power",
        translation_key="charging_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda manager: manager.current_power_w,
        round_digits=1,
    ),
    EbikeSensorEntityDescription(
        key="last_odometer_update",
        translation_key="last_odometer_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda manager: manager.last_update(),
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up sensor entities."""
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EbikeSensor(manager, description) for description in SENSOR_DESCRIPTIONS
    )


class EbikeSensor(EbikeTrackerEntity, SensorEntity):
    """E-bike tracker sensor."""

    entity_description: EbikeSensorEntityDescription

    @property
    def native_value(self):
        """Return sensor value."""
        value = self.entity_description.value_fn(self.manager)
        if isinstance(value, float):
            return self.manager.rounded(value, self.entity_description.round_digits)
        return value

    @property
    def extra_state_attributes(self):
        """Return optional attributes."""
        capacity = self.manager.battery_capacity_wh
        if capacity is None:
            return None
        return {ATTR_BATTERY_CAPACITY_WH: capacity}
