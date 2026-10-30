"""Arithmetic regression tests; these are not electrical qualification tests."""

import math
import unittest
from dataclasses import replace

from scripts.design_calculations import (
    Budget,
    average_transfer_current,
    charge_sharing,
    check_budgets,
    discharge_time,
    passive_peak_current,
    minimum_series_resistance,
    profile_budget,
    rc_settling_time,
    retention_demand_allowance,
    retention_time_estimate,
)


class DesignCalculationTests(unittest.TestCase):
    def test_default_budgets(self):
        self.assertTrue(all(check_budgets().values()), check_budgets())

    def test_peak_current_bound_includes_empty_target(self):
        self.assertAlmostEqual(passive_peak_current(3.35, 14.85), 0.2255892256)

    def test_average_is_not_initial_peak(self):
        average = average_transfer_current(1e-9, 1.5, 100e-9)
        peak = passive_peak_current(1.5, 15)
        self.assertAlmostEqual(average, 0.015)
        self.assertAlmostEqual(peak, 0.100)
        self.assertGreater(peak, average)

    def test_settling_scales_with_capacitance(self):
        small = rc_settling_time(17, 1e-9)
        large = rc_settling_time(17, 100e-9)
        self.assertAlmostEqual(large / small, 100)
        self.assertAlmostEqual(large, 5.7820355488e-6)

    def test_settling_defines_residual_error(self):
        t = rc_settling_time(17, 100e-9, 1.5, 0.05)
        self.assertAlmostEqual(1.5 * math.exp(-t / (17 * 100e-9)), 0.05)
        self.assertEqual(rc_settling_time(17, 100e-9, 1.5, 2.0), 0)

    def test_equal_capacitor_historical_endpoint(self):
        endpoint, charge = charge_sharing(1.1e-6, 1.1e-6)
        self.assertAlmostEqual(endpoint, 2.55)
        self.assertAlmostEqual(charge, 0.825e-6)

    def test_finite_reservoir_charge_is_below_conservative_bound(self):
        endpoint, charge = charge_sharing(1e-6, 47e-6, high=3.35, low=1.75)
        conservative = profile_budget(1e-6, 1)
        self.assertLess(charge, conservative["charge"])
        self.assertLess(endpoint - 1.75, conservative["rail_rise"])

    def test_supported_profile_limits(self):
        self.assertLess(profile_budget(100e-9, 4)["rail_rise"], 0.015)
        self.assertLess(profile_budget(1e-6, 1)["rail_rise"], 0.035)
        self.assertGreater(profile_budget(1e-6, 4)["rail_rise"], 0.035)

    def test_output_off_delay(self):
        t = discharge_time(10_000, 1e-6)
        self.assertAlmostEqual(t, 0.0351154544)
        self.assertLess(t, 0.050)

    def test_inadequate_series_resistor_fails_current_budget(self):
        bad = replace(Budget(), series_r=4.7)
        self.assertFalse(check_budgets(bad)[
            "passive current ceiling below 250 mA design ceiling"
        ])

    def test_small_reservoir_fails_charge_budget(self):
        bad = replace(Budget(), reservoir_min=1e-6)
        self.assertFalse(check_budgets(bad)["one 1 uF step pumps less than 35 mV"])

    def test_bad_usb_voltage_fails_driver_margin(self):
        bad = replace(Budget(), driver_vdd_min=4.50)
        self.assertFalse(check_budgets(bad)[
            "driver initial UVLO margin at least 250 mV"
        ])

    def test_revised_ti_regulator_retention_allocations(self):
        self.assertAlmostEqual(retention_demand_allowance(), 88.373737e-6)
        self.assertLess(retention_demand_allowance(), Budget().hold_demand_max)
        self.assertAlmostEqual(retention_time_estimate(), 0.141)
        bad = replace(Budget(), hold_ldo_allowance=100e-6)
        self.assertFalse(check_budgets(bad)["retention demand allowances fit current budget"])
        with self.assertRaises(ValueError):
            retention_time_estimate(replace(Budget(), hold_input_end=4.3))

    def test_selected_two_watt_limiter_needs_no_pulse_overload_credit(self):
        minimum = minimum_series_resistance()
        self.assertAlmostEqual(minimum, 14.553)
        self.assertLess(3.35 / minimum, 0.250)
        self.assertLess(3.35**2 / minimum, Budget().series_power)
        self.assertLess(Budget().series_power, 2.0)  # 1 W required actual-PCB capability vs 2 W nameplate.

    def test_invalid_inputs(self):
        for c in (0, -1, float("nan"), float("inf")):
            with self.subTest(c=c), self.assertRaises(ValueError):
                rc_settling_time(17, c)
        for pulses in (0, -1, 1.5, True):
            with self.subTest(pulses=pulses), self.assertRaises(ValueError):
                profile_budget(1e-6, pulses)
        with self.assertRaises(ValueError):
            charge_sharing(1e-6, 47e-6, high=1.8, low=3.3)


if __name__ == "__main__":
    unittest.main()
