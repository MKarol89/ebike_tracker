"""E-bike Tracker integration."""

from __future__ import annotations

from typing import Any


async def async_setup(hass, config: dict[str, Any]) -> bool:
    """Set up integration services."""
    import voluptuous as vol
    from homeassistant.exceptions import HomeAssistantError

    from .const import DOMAIN

    hass.data.setdefault(DOMAIN, {})

    async def async_correct_odometer(call) -> None:
        """Correct odometer value after explicit administrator confirmation."""
        entry_id = call.data["config_entry_id"]
        confirm = call.data["confirm"]
        mileage = call.data["mileage"]

        if not confirm:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="correction_not_confirmed",
            )

        user_id = call.context.user_id
        user = await hass.auth.async_get_user(user_id) if user_id else None
        if user is None or not user.is_admin:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="administrator_required",
            )

        manager = hass.data[DOMAIN].get(entry_id)
        if manager is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="entry_not_found",
            )

        await manager.async_set_odometer(mileage, allow_decrease=True)

    hass.services.async_register(
        DOMAIN,
        "correct_odometer",
        async_correct_odometer,
        schema=vol.Schema(
            {
                vol.Required("config_entry_id"): str,
                vol.Required("mileage"): vol.Coerce(float),
                vol.Required("confirm"): bool,
            }
        ),
    )

    return True


async def async_setup_entry(hass, entry) -> bool:
    """Set up E-bike Tracker from a config entry."""
    from .const import DOMAIN, PLATFORMS
    from .tracker import EbikeTrackerData

    hass.data.setdefault(DOMAIN, {})

    manager = EbikeTrackerData(hass, entry)
    await manager.async_load()

    hass.data[DOMAIN][entry.entry_id] = manager
    entry.runtime_data = manager

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await manager.async_start()

    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload a config entry."""
    from .const import DOMAIN, PLATFORMS

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        manager = hass.data[DOMAIN].pop(entry.entry_id)
        await manager.async_unload()
    return unload_ok


async def _async_update_listener(hass, entry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
