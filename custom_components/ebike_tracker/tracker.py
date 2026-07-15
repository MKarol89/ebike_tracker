"""Runtime data and persistence for E-bike Tracker."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .calculations import (
    EnergyChange,
    OdometerDecreaseError,
    average_daily_distance,
    build_odometer_change,
    cost_for_100_km,
    distance_since_start,
    energy_delta_from_meter,
    kwh_per_100_km,
    round_value,
    start_of_day,
    start_of_month,
    start_of_week,
    sum_distance,
    sum_energy,
    wh_per_km,
)
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
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)


class EbikeTrackerData:
    """Manage one tracked e-bike."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize runtime data."""
        self.hass = hass
        self.entry = entry
        self.store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry.entry_id}",
        )
        self.data: dict[str, Any] = {}
        self._listeners: list[Callable[[], None]] = []
        self._unsub_state: list[CALLBACK_TYPE] = []
        self.current_power_w: float | None = None

    @property
    def name(self) -> str:
        """Return bike name."""
        return self.entry.data[CONF_BIKE_NAME]

    @property
    def energy_entity_id(self) -> str:
        """Return configured cumulative energy entity."""
        return self.entry.options.get(
            CONF_ENERGY_ENTITY_ID,
            self.entry.data[CONF_ENERGY_ENTITY_ID],
        )

    @property
    def power_entity_id(self) -> str | None:
        """Return configured charging power entity."""
        return self.entry.options.get(
            CONF_POWER_ENTITY_ID,
            self.entry.data.get(CONF_POWER_ENTITY_ID),
        )

    @property
    def energy_price(self) -> float:
        """Return energy price in PLN/kWh."""
        return float(
            self.entry.options.get(
                CONF_ENERGY_PRICE,
                self.entry.data[CONF_ENERGY_PRICE],
            )
        )

    @property
    def charging_power_threshold(self) -> float:
        """Return charging detection threshold in W."""
        return float(
            self.entry.options.get(
                CONF_CHARGING_POWER_THRESHOLD,
                self.entry.data.get(
                    CONF_CHARGING_POWER_THRESHOLD,
                    DEFAULT_CHARGING_POWER_THRESHOLD,
                ),
            )
        )

    @property
    def battery_capacity_wh(self) -> float | None:
        """Return optional battery capacity."""
        value = self.entry.options.get(
            CONF_BATTERY_CAPACITY_WH,
            self.entry.data.get(CONF_BATTERY_CAPACITY_WH),
        )
        return None if value in (None, "") else float(value)

    @property
    def current_odometer_km(self) -> float:
        """Return current total odometer."""
        return float(self.data["current_odometer_km"])

    @property
    def start_odometer_km(self) -> float:
        """Return odometer value when monitoring started."""
        return float(self.data["start_odometer_km"])

    @property
    def odometer_history(self) -> list[dict[str, Any]]:
        """Return persisted odometer changes."""
        return self.data["odometer_history"]

    @property
    def energy_history(self) -> list[dict[str, Any]]:
        """Return persisted energy changes."""
        return self.data["energy_history"]

    async def async_load(self) -> None:
        """Load persisted data."""
        stored = await self.store.async_load()
        if stored is None:
            initial_odometer = float(self.entry.data[CONF_ODOMETER])
            stored = {
                "start_odometer_km": initial_odometer,
                "current_odometer_km": initial_odometer,
                "last_update": None,
                "odometer_history": [],
                "energy_total_kwh": 0.0,
                "last_energy_raw_kwh": None,
                "last_energy_entity_id": self.energy_entity_id,
                "energy_history": [],
            }
            await self.store.async_save(stored)

        self.data = stored

    async def async_start(self) -> None:
        """Start tracking source entities."""
        entity_ids = [self.energy_entity_id]
        if self.power_entity_id:
            entity_ids.append(self.power_entity_id)

        self._unsub_state.append(
            async_track_state_change_event(
                self.hass,
                entity_ids,
                self._async_source_state_changed,
            )
        )

        energy_state = self.hass.states.get(self.energy_entity_id)
        await self.async_process_energy_state(energy_state)

        if self.power_entity_id:
            self.async_process_power_state(self.hass.states.get(self.power_entity_id))

    async def async_unload(self) -> None:
        """Stop tracking source entities."""
        for unsub in self._unsub_state:
            unsub()
        self._unsub_state.clear()
        self._listeners.clear()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register an entity state listener."""
        self._listeners.append(listener)

        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    @callback
    def _notify_listeners(self) -> None:
        """Notify all entity listeners."""
        for listener in list(self._listeners):
            listener()

    async def async_set_odometer(
        self,
        new_odometer_km: float,
        *,
        allow_decrease: bool = False,
    ) -> None:
        """Persist an odometer update."""
        now = dt_util.now()
        try:
            change = build_odometer_change(
                self.current_odometer_km,
                new_odometer_km,
                now,
                allow_decrease=allow_decrease,
            )
        except OdometerDecreaseError as err:
            from homeassistant.exceptions import HomeAssistantError

            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="odometer_decrease",
            ) from err

        self.data["current_odometer_km"] = float(new_odometer_km)
        if change is not None:
            self.data["last_update"] = now.isoformat()
            self.odometer_history.append(change.as_dict())

        await self.store.async_save(self.data)
        self._notify_listeners()

    async def _async_source_state_changed(self, event) -> None:
        """Process a source entity state update."""
        entity_id = event.data["entity_id"]
        new_state = event.data.get("new_state")

        if entity_id == self.energy_entity_id:
            await self.async_process_energy_state(new_state)
        elif entity_id == self.power_entity_id:
            self.async_process_power_state(new_state)

    async def async_process_energy_state(self, state: State | None) -> None:
        """Process a cumulative energy source state."""
        raw = _state_as_float(state)
        if raw is None:
            return

        if self.data.get("last_energy_entity_id") != self.energy_entity_id:
            self.data["last_energy_entity_id"] = self.energy_entity_id
            self.data["last_energy_raw_kwh"] = raw
            await self.store.async_save(self.data)
            self._notify_listeners()
            return

        previous_raw = self.data.get("last_energy_raw_kwh")
        delta = energy_delta_from_meter(previous_raw, raw)
        self.data["last_energy_raw_kwh"] = raw

        if delta > 0:
            self.data["energy_total_kwh"] = float(self.data["energy_total_kwh"]) + delta
            self.energy_history.append(EnergyChange(dt_util.now(), delta).as_dict())

        await self.store.async_save(self.data)
        self._notify_listeners()

    @callback
    def async_process_power_state(self, state: State | None) -> None:
        """Process a charging power source state."""
        self.current_power_w = _state_as_float(state)
        self._notify_listeners()

    def total_distance_km(self) -> float:
        """Return total monitored distance."""
        return distance_since_start(self.current_odometer_km, self.start_odometer_km)

    def day_distance_km(self, now: datetime | None = None) -> float:
        """Return distance recorded today."""
        now = now or dt_util.now()
        return sum_distance(self.odometer_history, start_of_day(now), now)

    def week_distance_km(self, now: datetime | None = None) -> float:
        """Return distance recorded in the current week."""
        now = now or dt_util.now()
        return sum_distance(self.odometer_history, start_of_week(now), now)

    def month_distance_km(self, now: datetime | None = None) -> float:
        """Return distance recorded in the current month."""
        now = now or dt_util.now()
        return sum_distance(self.odometer_history, start_of_month(now), now)

    def average_distance_km(self, days: int, now: datetime | None = None) -> float:
        """Return rolling daily average distance."""
        now = now or dt_util.now()
        return average_daily_distance(self.odometer_history, now, days)

    def total_energy_kwh(self) -> float:
        """Return total monitored energy."""
        return float(self.data["energy_total_kwh"])

    def week_energy_kwh(self, now: datetime | None = None) -> float:
        """Return energy recorded in the current week."""
        now = now or dt_util.now()
        return sum_energy(self.energy_history, start_of_week(now), now)

    def month_energy_kwh(self, now: datetime | None = None) -> float:
        """Return energy recorded in the current month."""
        now = now or dt_util.now()
        return sum_energy(self.energy_history, start_of_month(now), now)

    def kwh_100_km(self) -> float | None:
        """Return average consumption in kWh/100 km."""
        return kwh_per_100_km(self.total_energy_kwh(), self.total_distance_km())

    def wh_km(self) -> float | None:
        """Return average consumption in Wh/km."""
        return wh_per_km(self.total_energy_kwh(), self.total_distance_km())

    def cost_100_km(self) -> float | None:
        """Return cost of riding 100 km."""
        return cost_for_100_km(self.kwh_100_km(), self.energy_price)

    def total_cost(self) -> float:
        """Return total energy cost."""
        return self.total_energy_kwh() * self.energy_price

    def is_charging(self) -> bool | None:
        """Return whether the bike is currently charging."""
        if self.current_power_w is None:
            return None
        return self.current_power_w >= self.charging_power_threshold

    def last_update(self) -> datetime | None:
        """Return last odometer update time."""
        value = self.data.get("last_update")
        if value is None:
            return None
        return datetime.fromisoformat(value)

    def rounded(self, value: float | None, digits: int = 3) -> float | None:
        """Return rounded values for entity states."""
        return round_value(value, digits)


def _state_as_float(state: State | None) -> float | None:
    """Return state as float, ignoring unavailable values."""
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None
