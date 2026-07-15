"""Pure calculation helpers for E-bike Tracker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


class OdometerDecreaseError(ValueError):
    """Raised when an odometer update would decrease the value."""


@dataclass(frozen=True, slots=True)
class OdometerChange:
    """A persisted odometer change."""

    timestamp: datetime
    previous_km: float
    new_km: float
    delta_km: float

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "previous_km": self.previous_km,
            "new_km": self.new_km,
            "delta_km": self.delta_km,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OdometerChange:
        """Create a change from persisted data."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            previous_km=float(data["previous_km"]),
            new_km=float(data["new_km"]),
            delta_km=float(data["delta_km"]),
        )


@dataclass(frozen=True, slots=True)
class EnergyChange:
    """A persisted energy increase."""

    timestamp: datetime
    delta_kwh: float

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "delta_kwh": self.delta_kwh,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnergyChange:
        """Create a change from persisted data."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            delta_kwh=float(data["delta_kwh"]),
        )


def round_value(value: float | None, digits: int = 3) -> float | None:
    """Round numeric sensor values while preserving unknown values."""
    if value is None:
        return None
    return round(value, digits)


def build_odometer_change(
    previous_km: float,
    new_km: float,
    when: datetime,
    *,
    allow_decrease: bool = False,
) -> OdometerChange | None:
    """Build an odometer change and reject accidental decreases."""
    previous_km = float(previous_km)
    new_km = float(new_km)

    if new_km < previous_km and not allow_decrease:
        raise OdometerDecreaseError

    delta_km = new_km - previous_km
    if delta_km == 0:
        return None

    return OdometerChange(
        timestamp=when,
        previous_km=previous_km,
        new_km=new_km,
        delta_km=delta_km,
    )


def distance_since_start(current_km: float, start_km: float) -> float:
    """Return monitored distance, never below zero for consumption metrics."""
    return max(0.0, float(current_km) - float(start_km))


def sum_distance(
    changes: list[dict[str, Any]] | list[OdometerChange],
    start: datetime,
    end: datetime | None = None,
) -> float:
    """Sum odometer deltas in a period."""
    total = 0.0
    for change in _iter_odometer_changes(changes):
        if change.timestamp < start:
            continue
        if end is not None and change.timestamp >= end:
            continue
        total += change.delta_km
    return total


def average_daily_distance(
    changes: list[dict[str, Any]] | list[OdometerChange],
    now: datetime,
    days: int,
) -> float:
    """Return average daily distance over a rolling window."""
    if days <= 0:
        raise ValueError("days must be greater than zero")
    return sum_distance(changes, now - timedelta(days=days), now) / days


def energy_delta_from_meter(
    previous_raw_kwh: float | None,
    new_raw_kwh: float,
) -> float:
    """Return energy increase from a cumulative meter, preserving resets."""
    new_raw_kwh = float(new_raw_kwh)

    if previous_raw_kwh is None:
        return 0.0

    previous_raw_kwh = float(previous_raw_kwh)
    if new_raw_kwh >= previous_raw_kwh:
        return new_raw_kwh - previous_raw_kwh

    return max(0.0, new_raw_kwh)


def sum_energy(
    changes: list[dict[str, Any]] | list[EnergyChange],
    start: datetime,
    end: datetime | None = None,
) -> float:
    """Sum energy deltas in a period."""
    total = 0.0
    for change in _iter_energy_changes(changes):
        if change.timestamp < start:
            continue
        if end is not None and change.timestamp >= end:
            continue
        total += change.delta_kwh
    return total


def kwh_per_100_km(energy_kwh: float, distance_km: float) -> float | None:
    """Return kWh/100 km, or unknown when distance is zero."""
    if distance_km <= 0:
        return None
    return float(energy_kwh) / float(distance_km) * 100


def wh_per_km(energy_kwh: float, distance_km: float) -> float | None:
    """Return Wh/km, or unknown when distance is zero."""
    if distance_km <= 0:
        return None
    return float(energy_kwh) * 1000 / float(distance_km)


def cost_for_100_km(kwh_100_km: float | None, price_per_kwh: float) -> float | None:
    """Return the cost of riding 100 km."""
    if kwh_100_km is None:
        return None
    return float(kwh_100_km) * float(price_per_kwh)


def start_of_day(now: datetime) -> datetime:
    """Return the beginning of the current day."""
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def start_of_week(now: datetime) -> datetime:
    """Return the beginning of the current ISO week."""
    return start_of_day(now) - timedelta(days=now.weekday())


def start_of_month(now: datetime) -> datetime:
    """Return the beginning of the current month."""
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _iter_odometer_changes(
    changes: list[dict[str, Any]] | list[OdometerChange],
) -> list[OdometerChange]:
    return [
        item if isinstance(item, OdometerChange) else OdometerChange.from_dict(item)
        for item in changes
    ]


def _iter_energy_changes(
    changes: list[dict[str, Any]] | list[EnergyChange],
) -> list[EnergyChange]:
    return [
        item if isinstance(item, EnergyChange) else EnergyChange.from_dict(item)
        for item in changes
    ]
