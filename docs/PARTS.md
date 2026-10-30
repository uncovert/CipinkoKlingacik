# ČipinkoKlingáčik — parts and population

Companion to [DESIGN.md](DESIGN.md). **This document is not a manufacturing BOM.**
Use the [supplier upload files](JLCPCB.md), then review packages, exact suffixes,
rotations and availability with JLCPCB. A selected circuit is not proof of its
waveforms or a supplier's stock.

C4 has [per-reference part selections and footprints](../hardware/cipinkoklingacik-parts-all.csv)
and a [filtered baseline BOM](../hardware/cipinkoklingacik-bom.csv). These are engineering
selections, not purchasing/assembly approval. See the
[PCB review](../hardware/PCB_REVIEW.md) for remaining gates.

The [prototype package](../hardware/manufacturing/README.md) now includes matched
68-reference baseline SMT BOM/positions, 7 hand-fit references and a baseline-only
paste file. [JLCPCB supplier-format exports](JLCPCB.md) now have explicit LCSC codes
and a dated stock/price audit. Eight same-footprint Basic substitutions reduce
feeder fees. U6 now uses a stocked TI TPS7A2036 with deliberately revised pinout/
local routing; F1 is Littelfuse and R15/R16 are Yageo 2 W. Supplier feeder rotation,
socket mating, procurement and physical qualification are not approved by that check.

## Baseline fitted blocks

| Block | Engineering choice | Required qualification |
| --- | --- | --- |
| Controller | Standard Pico 2, two separate 1x20 sockets | Official module geometry, orientation, USB clearance |
| Auxiliary protection | Littelfuse 1206L025YR, 250 mA hold, 16 V, 1206 | 500 mA trip, R1max 2.3 Ω, 100 A fault rating; qualify inrush/drop/ambient derating; not precision limiting |
| Crowbar driver | UCC27517DBVR, SOT-23-5 | 4.90–5.25 V **at VDD**, 3.3 V control, default inhibit, actual minimum pulse |
| Crowbar FET | AO3400A, SOT-23 | Actual VGS/pulse current, ringing and repeated energy; no 30 A operating claim |
| Driver bypass/gate | C13 100 nF pin-local + C14 1 µF distributed, 2.2 Ω gate resistor, 10 kΩ G-S | Full supply/ground loop and waveform; C14 VDD route ~7.33 mm; tune resistor only after measurement |
| Driver arm | 2N7002 + removable ARM link, IN- pulled to driver VDD by 10 kΩ | Open link/reset inhibits; 5 V must not reach GPIO |
| VHIGH | AP2112K-3.3, nominal 100 µF reservoir + local ceramics | Effective total 47–125 µF, EN, stability/startup/reverse paths |
| VLOW | AP2112K-1.8, same reservoir requirement | Source only; reservoir absorbs charge, bleeder recovers it |
| Rail bleeders | Two 330 Ω, 1%, ≥0.125 W | Upstream of mux; approximately 33 mW / 9.8 mW nominal |
| Mux VCC | **TPS7A2036PDBVR**, 3.6 V; IN1/GND2/EN3/NC4/OUT5 | EN=HOLD_IN; revised layout and local input/output bypass; qualify light-load accuracy, active discharge/UVLO and retention |
| Mux supply retention | Schottky diode + 1 kΩ input charging resistor + 100 µF HOLD_IN; 1 µF VCC bypass + 100 kΩ bleed | ≥47 µF effective input C, ≤0.10 mA total demand, startup and full shutdown trace |
| Voltage selector | **NX3L1T3157GMZ**, XSON6/SOT886 | GMZ selected instead of obsolete ,115/,132 ordering codes; verify sourcing, BBM, current/drop and actual timing |
| Supply-path current bound | **Two Yageo RC2512FK-7W15RL, 15 Ω, 1%, 2 W**, one per mux input | ≥14.85 Ω at 25°C; ~0.756 W bound, ~0.771 W including TCR over −40..125°C; no pulse-overload credit; qualify ≥1 W actual-PCB capability/derating; never bypass |
| Target disconnect | Two **Si2377EDS-T1-GE3**, common-source/common-gate, + 2N7002 pull-down | Opposed body diodes; 0.165 Ω max each at VGS=-1.5 V, TJ=25 °C; ≤0.8 Ω combined qualified-temperature budget |
| Disconnect timing | FETs held on during mux pulses; 5 ms wait after TARGET_ON | Internal gate resistance/microsecond switching are not suitable for the fast-selector role; check dynamic source coupling |
| Target discharge | **10 kΩ** permanent output bleeder | ≥50 ms off interval for ≤1 µF; actual leakage/back-power measurement |
| Reset | 2N7002, gate pulls/series resistor | Active-high assert; optional target-referenced pull-up |
| Trigger | SN74LVC1G17, 100 nF bypass, 1 kΩ input series, 100 kΩ pull-down | 3.3 V inputs only, bandwidth and calibrated delay |
| Gate/control defaults | 10 kΩ pulls and 100 Ω series where specified in DESIGN.md; regulator EN series 1 kΩ | Account individually in the eventual BOM; no floating enables |
| Measurement | DNP WSK2512R1000FEA, 0.1 Ω, 1%, four-terminal; fitted R39=0 Ω 1206 bypass | Remove R39 before fitting R20; separate sense2/3 to TP7/TP8; 1 mV at 10 mA; full path must still qualify within 17 Ω |
| Pulse connection | C4 fits J1, a 2-pin GLITCH/GND header; no SMA footprint | Clearly marked cable, pin 1/net check; no mechanical keying or nanosecond-current rating implied |

The earlier TLV704 pinout is **not compatible** with the revised U6 routing.
U6 now shares the IN1/GND2/EN3/NC4/OUT5 assignment with AP2112, but its voltage
and EN wiring are different. Do not substitute by a generic SOT-23 label.
NX3L1T3157GM is **not** the original SN74LVC1G3157 SOT-23 footprint.

## Optional / DNP

| Option | Choice / restriction |
| --- | --- |
| UART | SN74AXC4T774PWR, TSSOP16; VCCA=Pico 3V3, VCCB=TARGET_VDD; independent DIRs and OE high=disable |
| UART population | U8/C18/JP3–JP5 plus R40=4.7 kΩ UVCCB bleeder and R41=100 kΩ explicit B2 default; account for IC internal 71 kΩ typical data pulls and supply current; remove/refit all three links together with all power off; target bypass counts toward switched C with OE disabled |
| Fast-profile UART | Normally unfitted or all target-side links open; ≤1 µF one-dip profile for populated UART/target decoupling |
| Reset pull-up | 10 kΩ to TARGET_VDD only; DNP for independently powered target |
| Tuning capacitance | **No dedicated C4 footprint**; external dummy-load capacitance counts toward total C |
| Pulse-node TVS | **No C4 footprint**; a future/external protection option needs capacitance/clamp/undershoot review |
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

See [JLCPCB upload/sourcing guide](JLCPCB.md) for upload files, SKU mapping,
savings and cost exclusions. **All baseline SKUs are stocked in the revised
snapshot**; verify again including attrition at checkout. Use the exact 2 W / 1%
limiter code, not a 1 W / 5% lookalike, and never bypass protection. Pico/connectors
remain hand-fit. Budget/format tests are not procurement or fabrication approval.
