"""Unit tests for E-bike Tracker calculations."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from math import isclose

from custom_components.ebike_tracker.calculations import (
    EnergyChange,
    OdometerDecreaseError,
    average_daily_distance,
    build_odometer_change,
    cost_for_100_km,
    distance_since_start,
    energy_delta_from_meter,
    kwh_per_100_km,
    start_of_month,
    start_of_week,
    sum_distance,
    sum_energy,
    wh_per_km,
)


class CalculationTests(unittest.TestCase):
    """Unit tests for pure e-bike calculations."""

    def test_odometer_change_records_previous_new_and_delta(self) -> None:
        """Odometer updates include all details needed for persistence."""
        now = datetime(2026, 7, 15, 12, tzinfo=UTC)

        change = build_odometer_change(1000, 1024.5, now)

        self.assertIsNotNone(change)
        assert change is not None
        self.assertEqual(change.previous_km, 1000)
        self.assertEqual(change.new_km, 1024.5)
        self.assertEqual(change.delta_km, 24.5)
        self.assertEqual(
            change.as_dict(),
            {
                "timestamp": "2026-07-15T12:00:00+00:00",
                "previous_km": 1000.0,
                "new_km": 1024.5,
                "delta_km": 24.5,
            },
        )

    def test_odometer_rejects_accidental_decrease(self) -> None:
        """Backward updates require the explicit correction path."""
        now = datetime(2026, 7, 15, 12, tzinfo=UTC)

        with self.assertRaises(OdometerDecreaseError):
            build_odometer_change(1000, 999, now)

    def test_odometer_correction_can_decrease_when_allowed(self) -> None:
        """Confirmed correction can persist a negative delta."""
        now = datetime(2026, 7, 15, 12, tzinfo=UTC)

        change = build_odometer_change(1000, 995, now, allow_decrease=True)

        self.assertIsNotNone(change)
        assert change is not None
        self.assertEqual(change.delta_km, -5)

    def test_distance_periods_and_rolling_average(self) -> None:
        """Distance helpers sum persisted changes in requested windows."""
        now = datetime(2026, 7, 15, 12, tzinfo=UTC)
        changes = [
            build_odometer_change(100, 110, now - timedelta(days=8)).as_dict(),
            build_odometer_change(110, 130, now - timedelta(days=2)).as_dict(),
            build_odometer_change(130, 145, now - timedelta(hours=2)).as_dict(),
        ]

        self.assertEqual(sum_distance(changes, now - timedelta(days=7), now), 35)
        self.assertEqual(average_daily_distance(changes, now, 7), 5)

    def test_week_and_month_energy(self) -> None:
        """Energy period helpers use ISO weeks and calendar months."""
        now = datetime(2026, 7, 15, 12, tzinfo=UTC)
        energy = [
            EnergyChange(datetime(2026, 6, 30, 12, tzinfo=UTC), 1.2).as_dict(),
            EnergyChange(datetime(2026, 7, 13, 9, tzinfo=UTC), 0.6).as_dict(),
            EnergyChange(datetime(2026, 7, 15, 9, tzinfo=UTC), 0.9).as_dict(),
        ]

        self.assertTrue(isclose(sum_energy(energy, start_of_week(now), now), 1.5))
        self.assertTrue(isclose(sum_energy(energy, start_of_month(now), now), 1.5))

    def test_energy_delta_handles_initial_state_increment_and_reset(self) -> None:
        """A lower cumulative meter reading is treated as a reset, not data loss."""
        self.assertEqual(energy_delta_from_meter(None, 10.0), 0)
        self.assertEqual(energy_delta_from_meter(10.0, 12.5), 2.5)
        self.assertEqual(energy_delta_from_meter(12.5, 0.7), 0.7)

    def test_consumption_is_unknown_when_distance_is_zero(self) -> None:
        """Consumption is not calculated before any monitored distance exists."""
        self.assertEqual(distance_since_start(1000, 1000), 0)
        self.assertIsNone(kwh_per_100_km(2.0, 0))
        self.assertIsNone(wh_per_km(2.0, 0))
        self.assertIsNone(cost_for_100_km(None, 1.25))

    def test_consumption_and_cost_calculations(self) -> None:
        """Energy usage and cost use monitored distance since setup."""
        distance = distance_since_start(1075, 1000)
        kwh_100 = kwh_per_100_km(1.5, distance)

        self.assertEqual(distance, 75)
        self.assertTrue(kwh_100 is not None and isclose(kwh_100, 2.0))
        self.assertTrue(isclose(wh_per_km(1.5, distance), 20))
        self.assertTrue(
            kwh_100 is not None
            and isclose(cost_for_100_km(kwh_100, 1.2), 2.4)
        )


if __name__ == "__main__":
    unittest.main()
