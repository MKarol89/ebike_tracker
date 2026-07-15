"""Config flow for E-bike Tracker."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import UnitOfPower
from homeassistant.helpers import selector
from homeassistant.helpers.selector import NumberSelectorMode
from homeassistant.util import slugify

from .const import (
    CONF_BATTERY_CAPACITY_WH,
    CONF_BIKE_NAME,
    CONF_CHARGING_POWER_THRESHOLD,
    CONF_ENERGY_ENTITY_ID,
    CONF_ENERGY_PRICE,
    CONF_ODOMETER,
    CONF_POWER_ENTITY_ID,
    DEFAULT_CHARGING_POWER_THRESHOLD,
    DOMAIN,
)


class EbikeTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for E-bike Tracker."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return EbikeTrackerOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            bike_name = user_input[CONF_BIKE_NAME].strip()
            if not bike_name:
                errors[CONF_BIKE_NAME] = "bike_name_required"
            else:
                await self.async_set_unique_id(f"{DOMAIN}_{slugify(bike_name)}")
                self._abort_if_unique_id_configured()
                data = _clean_optional_values(user_input)
                data[CONF_BIKE_NAME] = bike_name
                data[CONF_CHARGING_POWER_THRESHOLD] = DEFAULT_CHARGING_POWER_THRESHOLD
                return self.async_create_entry(title=bike_name, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )


class EbikeTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options for E-bike Tracker."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=_clean_options_values(user_input),
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(self.config_entry),
        )


def _user_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    """Return config flow schema."""
    defaults = user_input or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_BIKE_NAME,
                default=defaults.get(CONF_BIKE_NAME, ""),
            ): selector.TextSelector(),
            vol.Required(
                CONF_ODOMETER,
                default=defaults.get(CONF_ODOMETER, 0.0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=0.1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="km",
                )
            ),
            _required_key(
                CONF_ENERGY_ENTITY_ID,
                defaults.get(CONF_ENERGY_ENTITY_ID),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            _optional_key(
                CONF_POWER_ENTITY_ID,
                defaults.get(CONF_POWER_ENTITY_ID),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_ENERGY_PRICE,
                default=defaults.get(CONF_ENERGY_PRICE, 0.0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=0.01,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="PLN/kWh",
                )
            ),
            vol.Optional(
                CONF_BATTERY_CAPACITY_WH,
                default=defaults.get(CONF_BATTERY_CAPACITY_WH, 0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="Wh",
                )
            ),
        }
    )


def _options_schema(config_entry) -> vol.Schema:
    """Return options flow schema."""
    options = config_entry.options
    data = config_entry.data

    return vol.Schema(
        {
            vol.Required(
                CONF_ENERGY_PRICE,
                default=options.get(CONF_ENERGY_PRICE, data[CONF_ENERGY_PRICE]),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=0.01,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="PLN/kWh",
                )
            ),
            vol.Required(
                CONF_ENERGY_ENTITY_ID,
                default=options.get(
                    CONF_ENERGY_ENTITY_ID,
                    data[CONF_ENERGY_ENTITY_ID],
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            _optional_key(
                CONF_POWER_ENTITY_ID,
                options.get(
                    CONF_POWER_ENTITY_ID,
                    data.get(CONF_POWER_ENTITY_ID),
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_CHARGING_POWER_THRESHOLD,
                default=options.get(
                    CONF_CHARGING_POWER_THRESHOLD,
                    data.get(
                        CONF_CHARGING_POWER_THRESHOLD,
                        DEFAULT_CHARGING_POWER_THRESHOLD,
                    ),
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=0.1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement=UnitOfPower.WATT,
                )
            ),
            vol.Optional(
                CONF_BATTERY_CAPACITY_WH,
                default=options.get(
                    CONF_BATTERY_CAPACITY_WH,
                    data.get(CONF_BATTERY_CAPACITY_WH, 0),
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="Wh",
                )
            ),
        }
    )


def _required_key(key: str, default: Any) -> vol.Required:
    """Return a required schema key without serializing None as default."""
    if default in (None, ""):
        return vol.Required(key)
    return vol.Required(key, default=default)


def _optional_key(key: str, default: Any) -> vol.Optional:
    """Return an optional schema key without serializing None as default."""
    if default in (None, ""):
        return vol.Optional(key)
    return vol.Optional(key, default=default)


def _clean_optional_values(values: dict[str, Any]) -> dict[str, Any]:
    """Remove empty optional values."""
    cleaned = dict(values)
    for key in (CONF_POWER_ENTITY_ID, CONF_BATTERY_CAPACITY_WH):
        if cleaned.get(key) in ("", None, 0, 0.0):
            cleaned.pop(key, None)
    return cleaned


def _clean_options_values(values: dict[str, Any]) -> dict[str, Any]:
    """Keep explicit empty option values so they override initial config."""
    cleaned = dict(values)
    for key in (CONF_POWER_ENTITY_ID, CONF_BATTERY_CAPACITY_WH):
        if cleaned.get(key) in ("", 0, 0.0):
            cleaned[key] = None
        if key not in cleaned:
            cleaned[key] = None
    return cleaned
