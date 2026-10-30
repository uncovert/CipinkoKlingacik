# ČipinkoKlingáčik — parts and population

Companion to [DESIGN.md](DESIGN.md). **Engineering selections, not an uploadable
manufacturing BOM.** All packages, exact suffixes, assembly-library parts and
availability still need checking against the final schematic. A selected circuit
is not proof of its waveforms or a supplier's stock.

C3 has [per-reference part selections and footprints](../hardware/cipinkoklingacik-parts-all.csv)
and a [filtered baseline BOM](../hardware/cipinkoklingacik-bom.csv). These are engineering
selections, not purchasing/assembly approval. See the
[PCB review](../hardware/PCB_REVIEW.md) for remaining gates.

The [prototype package](../hardware/manufacturing/README.md) now includes matched
68-reference baseline SMT BOM/positions, 7 hand-fit references and a baseline-only
paste file. Generic placement parity is checked; supplier SKU/feeder rotation,
socket mating, pricing and physical qualification are not approved by that check.

## Baseline fitted blocks

| Block | Engineering choice | Required qualification |
| --- | --- | --- |
| Controller | Standard Pico 2, two separate 1x20 sockets | Official module geometry, orientation, USB clearance |
| Auxiliary protection | Bourns MF-NSMF025X-2, 250 mA hold, 16 V, 1206 | Hold/trip curves, room-temperature drop, USB demand; not precision current limiting |
| Crowbar driver | UCC27517DBVR, SOT-23-5 | 4.90–5.25 V **at VDD**, 3.3 V control, default inhibit, actual minimum pulse |
| Crowbar FET | AO3400A, SOT-23 | Actual VGS/pulse current, ringing and repeated energy; no 30 A operating claim |
| Driver bypass/gate | C13 100 nF pin-local + C14 1 µF distributed, 2.2 Ω gate resistor, 10 kΩ G-S | Full supply/ground loop and waveform; C14 VDD route ~7.33 mm; tune resistor only after measurement |
| Driver arm | 2N7002 + removable ARM link, IN- pulled to driver VDD by 10 kΩ | Open link/reset inhibits; 5 V must not reach GPIO |
| VHIGH | AP2112K-3.3, nominal 100 µF reservoir + local ceramics | Effective total 47–125 µF, EN, stability/startup/reverse paths |
| VLOW | AP2112K-1.8, same reservoir requirement | Source only; reservoir absorbs charge, bleeder recovers it |
| Rail bleeders | Two 330 Ω, 1%, ≥0.125 W | Upstream of mux; approximately 33 mW / 9.8 mW nominal |
| Mux VCC | **TLV70436DBVR**, 3.6 V | Actual accuracy/dropout at light load; nominal label is not a sequencing guarantee |
| Mux supply retention | Schottky diode + 1 kΩ input charging resistor + 100 µF HOLD_IN; 1 µF VCC bypass + 100 kΩ bleed | ≥47 µF effective input C, ≤0.10 mA total demand, startup and full shutdown trace |
| Voltage selector | **NX3L1T3157GMZ**, XSON6/SOT886 | GMZ selected instead of obsolete ,115/,132 ordering codes; verify sourcing, BBM, current/drop and actual timing |
| Supply-path current bound | **Two 15 Ω, 1%, 1 W pulse-rated resistors**, one per mux input | ≥14.85 Ω each; high branch passive/reservoir bound ~0.756 W, not sustained LDO-fed rating; qualify temperature/foldback; never bypass |
| Target disconnect | Two **Si2377EDS-T1-GE3**, common-source/common-gate, + 2N7002 pull-down | Opposed body diodes; 0.165 Ω max each at VGS=-1.5 V, TJ=25 °C; ≤0.8 Ω combined qualified-temperature budget |
| Disconnect timing | FETs held on during mux pulses; 5 ms wait after TARGET_ON | Internal gate resistance/microsecond switching are not suitable for the fast-selector role; check dynamic source coupling |
| Target discharge | **10 kΩ** permanent output bleeder | ≥50 ms off interval for ≤1 µF; actual leakage/back-power measurement |
| Reset | 2N7002, gate pulls/series resistor | Active-high assert; optional target-referenced pull-up |
| Trigger | SN74LVC1G17, 100 nF bypass, 1 kΩ input series, 100 kΩ pull-down | 3.3 V inputs only, bandwidth and calibrated delay |
| Gate/control defaults | 10 kΩ pulls and 100 Ω series where specified in DESIGN.md; regulator EN series 1 kΩ | Account individually in the eventual BOM; no floating enables |
| Measurement | DNP WSK2512R1000FEA, 0.1 Ω, 1%, four-terminal; fitted R39=0 Ω 1206 bypass | Remove R39 before fitting R20; separate sense2/3 to TP7/TP8; 1 mV at 10 mA; full path must still qualify within 17 Ω |
| Pulse connection | C3 fits J1, a 2-pin GLITCH/GND header; no SMA footprint | Clearly marked cable, pin 1/net check; no mechanical keying or nanosecond-current rating implied |

AP2112 and TLV704 SOT-package pin assignments are different. Do not interchange
symbols/footprints based on a generic "SOT-23 regulator" label. NX3L1T3157GM is
**not** the original SN74LVC1G3157 SOT-23 footprint.

## Optional / DNP

| Option | Choice / restriction |
| --- | --- |
| UART | SN74AXC4T774PWR, TSSOP16; VCCA=Pico 3V3, VCCB=TARGET_VDD; independent DIRs and OE high=disable |
| UART population | U8/C18/JP3–JP5 plus R40=4.7 kΩ UVCCB bleeder and R41=100 kΩ explicit B2 default; account for IC internal 71 kΩ typical data pulls and supply current; remove/refit all three links together with all power off; target bypass counts toward switched C with OE disabled |
| Fast-profile UART | Normally unfitted or all target-side links open; ≤1 µF one-dip profile for populated UART/target decoupling |
| Reset pull-up | 10 kΩ to TARGET_VDD only; DNP for independently powered target |
| Tuning capacitance | **No dedicated C3 footprint**; external dummy-load capacitance counts toward total C |
| Pulse-node TVS | **No C3 footprint**; a future/external protection option needs capacitance/clamp/undershoot review |
| Scope/SCA gain chain | External equipment, not an onboard deliverable |

## Intentionally not fitted

- No onboard EXT_VDD input or source selector; external crowbar targets leave
  the TARGET_VDD wire disconnected.
- No active output discharge FET, mode-sense circuit or discharge interlock.
- No mandatory voltage-monitor ADC/comparator, independent reference, boost
  converter, galvanic isolator, hardware one-shot or industrial ESD qualification.
- No SN74LVC1G3157 power mux or SY6280 in the output pulse path.

These omissions are scope decisions, not claims that the associated abuse or
failure modes are protected. In particular, PIO stuck high is a residual risk.

## Manufacturing and cost

Generate unique references and exact resistor/capacitor counts from the schematic,
then match BOM/CPL/footprints. Check actual JLCPCB SKU and rotations, including
small mux packaging. No unreviewed substitutions. Pico and large connectors may
be hand-fitted. No price or fabrication readiness is asserted until there is a
real quote and electrical/layout review.
