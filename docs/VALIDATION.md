# ČipinkoKlingáčik — qualification checklist

**All hardware boxes remain open.** Arithmetic passing is not a hardware test.
Use [DESIGN.md](DESIGN.md), not the superseded audit's generic requirements.

## A. Required before board ordering

C4 static evidence: full schematic, local footprints and exact-part selections;
**ERC 0/0, strict full PCB DRC 0 violations / 0 unconnected / 0 parity issues**;
completed routing/return-stitch review; prototype exports and regression tests.
These do **not** close the combined sourcing/layout/bench gates below. See
[hardware/PCB_REVIEW.md](../hardware/PCB_REVIEW.md).

**Independent review:** [REVIEW.md](REVIEW.md) records the verified corrections
and accepted prototype limits. No physical test has been closed by a design-file
review or the corrected design files.

Completed static-file checks (not bench qualification):

- [x] Capture every physical pin, supply/default/unused input; verify exported connectivity.
- [x] Match physical symbols/footprint pads, native DNP and complete board inventory.
- [x] Complete routing; strict ERC, full DRC/parity, no project exclusions.
- [x] Review critical via-free paths, dual ground pours and local return stitching.
- [x] Export/hash bare-board Gerbers and separate PTH/NPTH drills; check outline/drill inventory.
- [x] Match baseline SMT BOM/positions and omit DNP paste in a separate baseline stencil.

- [ ] Record the intended target's normal supply/current range and total C.
      Include cables, probe, disconnect parasitics and fitted UART bypass.
- [ ] Confirm that 10 mA and the 15 Ω/17 Ω path budgets suit the actual target.
      A 50 mA low-drop target requires a different power stage, not a bypass link.
- [ ] Check NX3L1T3157GMZ sourced package, current/drop conditions, BBM,
      select timing and input voltage in all planned power states.
- [ ] Verify sourced Si2377EDS-T1-GE3 disconnects, low-VGS/temperature resistance,
      opposed body diodes and gate control; include the 5 ms connection delay and
      dynamic gate/source coupling. A datasheet match is not assembly approval.
- [ ] Review MUX_VCC 3.6 V supply, diode polarity, retention leakage/capacitance,
      regulator dropout and startup; analog rails must remain within mux limits.
- [ ] Check reservoir effective C (47–125 µF each), AP2112 stability, foldback,
      startup, EN wiring, reverse paths and shared-input power-down behavior.
- [ ] Check exact Yageo 15 Ω / 1% / **2 W** limiter SKU, minimum resistance/TCR,
      ≥1 W actual-PCB thermal capability and derating, with no pulse-overload
      credit. Confirm the 25°C ~226 mA and TCR-envelope ~230 mA bounds remain
      below actual permitted switch operation.
- [ ] Check USB auxiliary fuse drop/current/hold/trip behavior, total demand and
      target-rail enable after USB configuration; fuse is not a precision limiter.
- [x] Draw schematic/netlist and unique-reference BOM; explicitly wire every
      supply, enable, default pull, unused input and bypass capacitor.
- [ ] Verify revised TPS7A2036 **IN1/GND2/EN3/NC4/OUT5**, EN=HOLD_IN,
      C10/C11 input/output bypass and ground returns; **do not fit the old TLV704**.
      Check XSON6 mux footprint, Pico 2 sockets, USB and PCB/connector mechanics.
- [ ] Review local gate loop, whole target/cable fault loop, continuous ground
      reference, Kelvin pads and absence of long pulse-node branches.
      C4 Kelvin option: R20=0.1 Ω four-terminal, R39 removed when R20 fitted;
      differential measurement at TP7/TP8. Never ground either high-side sense pad.
- [x] Run ERC/DRC/parity; all PCB DRC checks enabled, no exclusions. The four
      standard ignored ERC checks are explicitly listed in hardware/README.md.
- [ ] Approve exact sourced parts/rotations against the matched generic assembly
      BOM/positions, obtain a live quote. Order only as an engineering prototype.
- [ ] Use separately marked GLITCH/TARGET cables; inspect net/pin mappings before
      powering. Silkscreen is not connector keying; interchangeable two-pin
      headers remain an accepted supervised-prototype misplug risk.

## B. Required dummy-load bring-up

Disconnect power and remove ARM before rewiring. Use suitable current-limited
bench equipment, short low-inductance probing and an adequately fast scope.
Do not ground a live high-side shunt terminal or accidentally use 50 Ω scope
termination as a rail load. Do not lift a scope protective-earth connection.

- [ ] Inspect shorts, component identities, diode/FET orientation and assembly.
- [ ] At boot/reset, verify GP2 low, driver inhibited, target disconnected, UART
      disabled and target rails initially disabled.
- [ ] Measure **4.90–5.25 V at driver VDD** under operating load. Reject unsuitable
      source/cable; the part's nominal 5 V label is insufficient.
- [ ] Verify MUX_VCC 3.50–3.70 V, retention demand ≤0.10 mA, startup within the
      1 s preparation interval; regulators settled within the later 50 ms delay.
- [ ] Scope USB removal, brownout, reset and deliberate shutdown: MUX_VCC must
      outlast VHIGH/VLOW, with analog signals within mux ratings throughout.
      Check LDO reverse current and no retention-branch feed into the host branch.
      Capture GP4, RAILS_EN and both rail reservoirs with TARGET_VDD; include the
      AP2112 EN-low discharge path (60 Ω typical with valid input power), not
      just R21. Disconnect target before deliberate regulator shutdown.
      Include TPS7A20 P-version active discharge at EN-low/UVLO; it is not reverse
      blocking. Verify the 4.2→3.9 V / 141 ms retention estimate against actual
      leakage/current/light-load output tolerance, not only datasheet typicals.
- [ ] Measure total USB startup/normal/fault demand; record source capability and
      fuse behavior. Include reservoir charging and actual Pico demand.
- [ ] With measured C=1 nF, 10 nF, 100 nF, and 1 µF, measure both transition
      directions, select-to-voltage delay, actual depth, plateau, ringing and
      current. Compare with real switch conditions, not absolute maxima alone.
      Include the accepted 48.6 mm / three-via target force path and the actual
      cable/return loop; no guessed trace inductance closes this measurement.
- [ ] Verify total on-path resistance ≤17 Ω and normal-rail tolerance at ≤10 mA
      total target load, including the 10 kΩ output bleed and interfaces.
- [ ] Run ≤100 nF/4-dip and ≤1 µF/1-dip bursts, ≥20 ms apart; measure pumping,
      droop/recovery and temperature. Accumulated-charge pumping budget:
      ≤15 mV / ≤35 mV respectively. Record fast ESR/ESL/load-release excursions
      separately; these figures are not instantaneous-overshoot guarantees.
- [ ] Verify target off falls below 0.1 V within 50 ms at ≤1 µF in **both mux
      selections**, with no injecting target signals; measure leakage, don't infer
      power-off from a control bit. Increase qualified off delay if necessary.
- [ ] Exercise reset and valid 3.3 V trigger; measure thresholds, minimum accepted
      trigger width, latency/jitter and PIO synchronization effects.
- [ ] On an energy-limited crowbar dummy load, verify gate VGS, pulse current,
      actual pulse width/edges, ringing, reset/UVLO behavior and repeated heating.
      Probe VGS relative to Q1 source and U2 OUT/VDD/GND with short connections;
      include the bypass/ground return, not only the short OUT/gate branches.
- [ ] At current-limited target short on **each rail**, measure actual fault
      current, AP2112 foldback/thermal behavior, R15/R16/U4/U5/F1 temperatures
      and time response. 226 mA/0.756 W is a high-branch passive/reservoir bound,
      not a guaranteed sustained LDO-fed current. The 1.8 V passive bound is
      about 121 mA; the 50 mA VOUT=0 V datasheet point is not a guaranteed foldback curve.
- [ ] Check U4/U5/U6 startup, load steps and stability with actual bypass/reservoir
      parts; geometric bypass locality does not establish loop stability.
- [ ] If R20 fitted, remove R39, hand-solder or use a reviewed stencil/CPL variant,
      and calibrate DC/low-bandwidth differential TP7/TP8 measurement against a
      known current source. No fast-pulse accuracy is claimed for the spaced pads.
- [ ] Verify open ARM link inhibits even if GP8 is asserted; GP8 reset/high-Z must
      also inhibit. Scope the unpowered/powered driver startup states.
- [ ] Inspect/test PIO: no blocking operation after asserting GP2; FIFO starvation
      may occur only in a low state. Sequence ends low. Abort clears GP8 and GP2,
      not merely the state-machine enable. USB software abort is exercised.

**Do not expect a halt/stuck-high test to prove an independent hardware cutoff:**
none is fitted. Test that case only on a dummy load safe for continuous on-time;
record that it can remain on, and retain the supervised-use restriction. Add a
separately reviewed cutoff before claiming unattended fail-safe operation.

## C. Optional UART and actual-target acceptance

- [ ] If UART fitted: verify DIR/OE, 1.8/3.3/off operation, opposite supply orders,
      disabled-output behavior and Ioff. Disable before dip/off; enable after
      recovery. Count the target-side 100 nF capacitor even with OE disabled.
      Fit R40=4.7 kΩ and R41=100 kΩ; measure UVCCB decay/endpoint below 0.1 V
      with all target
      links open, and check B2 default when the link/cable is absent.
      Partial-link powered/back-power tests use current-limited dummy hardware
      only; they are not supported operating states or a reason to hot-unplug.
      Include R40 (~0.7 mA at 3.3 V), R41 plus the IC's 71 kΩ typical data pulls,
      and translator supply current in the measured 10 mA total-target budget.
- [ ] Verify back-powering/off voltage with the **actual** debugger and application
      wiring. Disconnect injecting signals; onboard translation is not universal
      isolation of the rest of the target board.
- [ ] For the fast profile, remove **all three** UART target VCC/TX/RX links
      together with board/target power off and ARM removed, or leave unfitted;
      record total remaining C. For populated UART use the ≤1 µF profile or
      recalculate/requalify an explicitly different load.
- [ ] For an independently powered crowbar target, verify TARGET_VDD wire absent,
      onboard reset pull-up absent, safe ground reference and its own source/
      capacitor energy limit. Board power-cycle/mux commands do not control it.
- [ ] Only then connect an expendable authorized target; record exact MCU part,
      revision, wiring, firmware and measured waveforms. No family-wide security
      bypass, calibrated amplitude or successful attack is implied by these tests.

## Not baseline release gates

Industrial ESD/OVP/reverse-polarity qualification, arbitrary hot-plugging,
VSYS-only operation, automatic rail monitoring, external-source arbitration,
unattended stuck-on protection and useful SCA bandwidth are not v1 promises.
If added later, they need their own requirements and validation.

Retain schematic/BOM/PCB revisions, actual parts, source voltage/current, effective
C/load, probe connections/bandwidth/sample rate, firmware clock/PIO program,
waveforms, thermal readings and explicit pass/fail limits. None of the above
hardware tests has been performed by this documentation change.
