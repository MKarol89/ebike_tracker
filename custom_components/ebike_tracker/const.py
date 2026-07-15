"""Constants for E-bike Tracker."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "ebike_tracker"
NAME = "E-bike Tracker"

PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.BINARY_SENSOR]

CONF_BIKE_NAME = "bike_name"
CONF_ODOMETER = "odometer_km"
CONF_ENERGY_ENTITY_ID = "energy_entity_id"
CONF_POWER_ENTITY_ID = "power_entity_id"
CONF_ENERGY_PRICE = "energy_price"
CONF_BATTERY_CAPACITY_WH = "battery_capacity_wh"
CONF_CHARGING_POWER_THRESHOLD = "charging_power_threshold"

DEFAULT_CHARGING_POWER_THRESHOLD = 5.0

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = DOMAIN

ATTR_PREVIOUS_ODOMETER = "previous_odometer_km"
ATTR_NEW_ODOMETER = "new_odometer_km"
ATTR_ODOMETER_DELTA = "delta_km"
ATTR_BATTERY_CAPACITY_WH = "battery_capacity_wh"
