"""Concept C first-order budgets, not a circuit simulation or part approval.

SI units throughout. Current ceilings assume passive, non-inductive paths and
bounded source voltages; they do not cover external injection or ringing.
Run from the project root: python3 scripts/design_calculations.py
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Budget:
    high_max: float = 3.35
    step_max: float = 1.60
    series_r: float = 15.0
    series_tolerance: float = 0.01
    series_tcr_max: float = 200e-6  # Selected Yageo 2 W series, per degree C.
    series_power: float = 1.0  # Required qualified PCB capability; selected part is 2 W nameplate.
    path_r_max: float = 17.0
    mux_r_budget: float = 0.9  # Verify at actual VCC/current; not a universal spec.
    mux_cont_abs_max: float = 0.350  # Stress limit, NOT a recommended current.
    mux_directional_drop_max: float = 0.4
    load_max: float = 0.010  # Includes all downstream bleeders/interfaces.
    reservoir_min: float = 47e-6  # Effective capacitance, not package marking.
    rail_bleed_r: float = 330.0
    output_bleed_r: float = 10_000.0
    burst_interval: float = 0.020
    off_interval: float = 0.050
    off_threshold: float = 0.1
    driver_vdd_min: float = 4.90
    driver_uvlo_start_max: float = 4.65
    hold_c_min: float = 47e-6
    hold_input_start: float = 4.2
    hold_input_end: float = 3.9  # TPS7A20 VOUT+0.3 V headroom; still verify at light load.
    hold_demand_max: float = 100e-6  # Includes regulator and capacitor leakage.
    hold_ldo_allowance: float = 25e-6  # Engineering allocation at light load, NOT a guaranteed IGND limit.
    hold_mux_allowance: float = 8e-6  # Static ICC + control-level allowance; no continuous toggling.
    hold_cap_leakage_allowance: float = 16e-6
    hold_diode_leakage_allowance: float = 2e-6  # BAT54WS at 25 C; verify total on the bench.
    hold_bleed_r: float = 100_000.0
    hold_output_max: float = 3.7


def _positive(**values):
    for name, value in values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")


def passive_peak_current(voltage_step, resistance):
    """Initial resistive current; capacitance changes duration, not this value."""
    _positive(voltage_step=voltage_step, resistance=resistance)
    return voltage_step / resistance


def minimum_series_resistance(budget=Budget(), temperature_min=-40.0, temperature_max=125.0):
    """Conservative tolerance/TCR sizing over component temperature, not a thermal model."""
    span = max(abs(temperature_min - 25), abs(temperature_max - 25))
    minimum = budget.series_r * (1 - budget.series_tolerance) * (1 - budget.series_tcr_max * span)
    _positive(minimum_resistance=minimum)
    return minimum


def average_transfer_current(capacitance, voltage_step, transition_time):
    """Required average for the full stated change, not a peak prediction."""
    _positive(capacitance=capacitance, voltage_step=voltage_step,
              transition_time=transition_time)
    return capacitance * voltage_step / transition_time


def rc_settling_time(resistance, capacitance, voltage_step=1.5, error=0.05):
    """Constant-source/load RC residual error; excludes reservoir/control delay."""
    _positive(resistance=resistance, capacitance=capacitance,
              voltage_step=voltage_step, error=error)
    return resistance * capacitance * max(0.0, math.log(voltage_step / error))


def charge_sharing(target_c, reservoir_c, high=3.3, low=1.8):
    """No-load, no-regulator two-capacitor endpoint and transferred charge."""
    _positive(target_c=target_c, reservoir_c=reservoir_c, high=high, low=low)
    if high < low:
        raise ValueError("high must be at least low")
    charge = target_c * reservoir_c / (target_c + reservoir_c) * (high - low)
    endpoint = low + charge / reservoir_c
    return endpoint, charge


def discharge_time(resistance, capacitance, initial=3.35, threshold=0.1):
    """Ideal passive discharge, with NO back-power or switch leakage."""
    _positive(resistance=resistance, capacitance=capacitance,
              initial=initial, threshold=threshold)
    return resistance * capacitance * max(0.0, math.log(initial / threshold))


def retention_demand_allowance(budget=Budget()):
    """Sizing allocations, not measured demand or a composite datasheet guarantee."""
    return (budget.hold_ldo_allowance + budget.hold_mux_allowance
            + budget.hold_cap_leakage_allowance
            + budget.hold_diode_leakage_allowance
            + budget.hold_output_max / (budget.hold_bleed_r * 0.99))


def retention_time_estimate(budget=Budget()):
    """Constant-current reservoir estimate to the assumed useful input endpoint."""
    _positive(capacitance=budget.hold_c_min, demand=budget.hold_demand_max,
              start=budget.hold_input_start, end=budget.hold_input_end)
    if budget.hold_input_start <= budget.hold_input_end:
        raise ValueError("Hold input must start above the useful endpoint")
    return budget.hold_c_min * (budget.hold_input_start - budget.hold_input_end) / budget.hold_demand_max


def profile_budget(capacitance, pulses, budget=Budget()):
    """Upper charge bound ignores beneficial target load and inter-pulse bleed."""
    _positive(capacitance=capacitance)
    if not isinstance(pulses, int) or isinstance(pulses, bool) or pulses < 1:
        raise ValueError("pulses must be a positive integer")
    charge = pulses * capacitance * budget.step_max
    bleed_current = 1.8 / budget.rail_bleed_r
    return {
        "charge": charge,
        "rail_rise": charge / budget.reservoir_min,
        "average_injected": charge / budget.burst_interval,
        "bleed_current": bleed_current,
        # While elevated the source-only LDO stops sourcing. Not an RC decay.
        "excess_recovery_estimate": charge / bleed_current,
    }


def check_budgets(budget=Budget()):
    """Check design assumptions against the explicit arithmetic envelopes."""
    minimum_r = budget.series_r * (1 - budget.series_tolerance)
    peak = passive_peak_current(budget.high_max, minimum_r)
    temperature_r = minimum_series_resistance(budget)
    fast = profile_budget(100e-9, 4, budget)
    slow = profile_budget(1e-6, 1, budget)
    checks = {
        "passive current ceiling below 250 mA design ceiling": peak < 0.250,
        "design ceiling below mux continuous absolute maximum": (
            0.250 < budget.mux_cont_abs_max
        ),
        "mux directional drop budget below 0.4 V": (
            peak * budget.mux_r_budget < budget.mux_directional_drop_max
        ),
        "series short power below nominal resistor rating": (
            budget.high_max**2 / minimum_r < budget.series_power
        ),
        "temperature-envelope current ceiling below 250 mA": budget.high_max / temperature_r < 0.250,
        "temperature-envelope power below required PCB capability": budget.high_max**2 / temperature_r < budget.series_power,
        "four 100 nF steps pump less than 15 mV": fast["rail_rise"] < 0.015,
        "one 1 uF step pumps less than 35 mV": slow["rail_rise"] < 0.035,
        "slow-profile average injection below bleeder current": (
            slow["average_injected"] < slow["bleed_current"]
        ),
        "1 uF ideal discharge fits 50 ms off interval": (
            discharge_time(budget.output_bleed_r, 1e-6, budget.high_max,
                           budget.off_threshold) < budget.off_interval
        ),
        "driver initial UVLO margin at least 250 mV": (
            budget.driver_vdd_min - budget.driver_uvlo_start_max >= 0.25
        ),
        "retention demand allowances fit current budget": (
            retention_demand_allowance(budget) <= budget.hold_demand_max
        ),
        "assumed useful retention at least 100 ms": retention_time_estimate(budget) >= 0.100,
    }
    return checks


def main():
    b = Budget()
    r_min = b.series_r * (1 - b.series_tolerance)
    peak = passive_peak_current(b.high_max, r_min)
    print("Concept C estimates only; NO hardware qualification is implied.")
    print(f"Cold start/short resistive ceiling: {peak * 1e3:.1f} mA")
    print(f"15 ohm resistor short dissipation: {b.high_max**2 / r_min:.3f} W")
    print(f"With tolerance/TCR over -40..125 C component temperature: {b.high_max / minimum_series_resistance(b) * 1e3:.1f} mA / {b.high_max**2 / minimum_series_resistance(b):.3f} W")
    print(f"10 mA DC path drop at 17 ohms: {b.load_max * b.path_r_max:.3f} V")
    print("RC settling to 50 mV residual from a 1.5 V step (no control delay):")
    for c in (1e-9, 10e-9, 100e-9, 1e-6):
        t = rc_settling_time(b.path_r_max, c)
        print(f"  {c * 1e9:7.0f} nF: {t * 1e6:7.3f} us")
    print("C reduction does NOT reduce initial resistive current.")
    for name, c, pulses in (("fast", 100e-9, 4), ("UART/large-C", 1e-6, 1)):
        p = profile_budget(c, pulses, b)
        print(f"{name}: Q <= {p['charge'] * 1e6:.3f} uC, "
              f"VLOW rise <= {p['rail_rise'] * 1e3:.2f} mV, "
              f"average injection {p['average_injected'] * 1e6:.1f} uA")
        print(f"  Excess-charge/bleed recovery scale: "
              f"{p['excess_recovery_estimate'] * 1e3:.3f} ms")
    print(f"1 uF ideal output decay to 0.1 V: "
          f"{discharge_time(b.output_bleed_r, 1e-6) * 1e3:.2f} ms")
    hold_estimate = retention_time_estimate(b)
    print(f"Static retention current allocation: {retention_demand_allowance(b) * 1e6:.1f} uA (not a measured/specification guarantee)")
    print(f"Assumed useful mux-supply hold estimate: {hold_estimate * 1e3:.1f} ms")
    print("Hold-up, LDO dropout/reverse paths, ringing and thermal require measurements.")
    checks = check_budgets(b)
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
