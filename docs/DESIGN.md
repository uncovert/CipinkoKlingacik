# ČipinkoKlingáčik — electrical design (C3)

Revision: 2026-10-28, C3 reviewed prototype. **Design files, not tested hardware.**

This is a supervised, low-cost bench instrument for expendable, authorized
development targets. Keep the socketed Pico 2, separate crowbar, voltage selector,
reset and trigger. Do not turn it into an industrial fault-tolerant instrument.
Reviewed design decisions and remaining qualification gates are summarized in
[`REVIEW.md`](REVIEW.md).

The complete C3 KiCad schematic and its PDF are in
[`hardware/README.md`](../hardware/README.md), with assigned local footprints,
exact-part selections and exported-netlist tests. The 100 × 85 mm two-layer
carrier is fully routed and passes strict ERC/DRC/parity with zero unconnected
items; generic prototype Gerber/drill/stencil/assembly data are exported.
See its [PCB review](../hardware/PCB_REVIEW.md) for routing/return evidence and
remaining supplier/physical qualification gates. There is no hardware validation.

## 1. What this revision actually supports

| Function | Initial qualification envelope — not a measured rating |
| --- | --- |
| Controller | Standard non-wireless Pico 2; 150 MHz, PIO clkdiv=1 |
| Target sources | 3.3 V and 1.8 V upstream of the selector |
| Target load | Up to **10 mA total downstream load**, including pull-ups/bleeder/interfaces |
| Fast mux profile | Total switched C ≤100 nF; up to 4 dips per burst |
| UART/large-C profile | Total switched C ≤1 µF; 1 dip per burst |
| Burst interval | ≥20 ms, measured between burst starts; finite bursts only |
| Mux low-command width | 0.1–100 µs exploratory range; settled plateau requires the RC time below |
| Crowbar command | Initially 0.1–2 µs, ≤4 pulses/burst, ≥20 ms between bursts |
| Crowbar terminal | Separate GLITCH/GND; 0–3.3 V intended domain, not a 30 V supply output |
| Environment | Supervised room-temperature bench use; no hot-plug or arbitrary external voltage support |

The earlier provisional 50 mA target rating was never established. The default
15 Ω resistor deliberately trades load regulation and transition speed for a
bounded switch current. **A 50 mA low-impedance supply or a settled 100 ns dip
into 100 nF is not provided by this circuit.** If the actual target needs either,
redesign the power stage; do not just short out the resistor.

"1.8 V selected" identifies the source, not a calibrated voltage at the MCU.
For a 17 Ω total path and 10 mA constant load, the DC drop is 170 mV:
approximately 3.13 V / 1.63 V from nominal sources. Actual target current changes
during a dip; measure the pin voltage. A low-voltage dip may intentionally leave
the target's normal operating range. Normal-rail operation must still meet that
exact target's specified supply range.

## 2. Architecture and net ownership

```text
Pico USB VBUS ------------------------------> Pico powerchain (unchanged)
     |
     +-- F_AUX (250 mA hold PTC) --> AUX_5V
                                      |
                                      +--> gate driver --> gate --> crowbar FET
                                      |                           drain --> GLITCH
                                      |                           source --> local GND
                                      |
                                      +--> AP2112-3.3 --> VHIGH reservoir + bleed
                                      +--> AP2112-1.8 --> VLOW reservoir + bleed
                                      |
                                      +-- diode -- 1 kΩ --> HOLD_IN capacitor
                                                           |
                                                        TLV704-3.6 --> MUX_VCC

VHIGH --> 15 Ω --> Y0  NX3L1T3157
VLOW  --> 15 Ω --> Y1  VCC = MUX_VCC, not Pico 3V3 or VLOW
                      Z --> back-to-back P-FET disconnect -->
                            optional shunt/bypass --> TARGET_VDD connector
                                                        |
                                                       10 kΩ
                                                        |
                                                       GND
```

Only the connector and optional target-side interfaces use TARGET_VDD.
GLITCH is not wired to TARGET_VDD. No controller gate-current return through
the Pico socket. No default bulk or ceramic capacitor on TARGET_VDD except
those explicitly counted for a fitted UART option or target.

### External target power: separate wiring, not a second onboard supply path

For an externally powered crowbar experiment, **leave the board's TARGET_VDD
wire unplugged** and power the target from its own supply. Connect GLITCH/GND,
appropriate trigger and open-drain reset only. UART stays unplugged unless its
target reference is separately reviewed. There is no onboard EXT_VDD connector,
input/output source selector or externally connected discharge transistor in
this revision. Never feed an external supply into TARGET_VDD.

This retains externally powered crowbar experiments without requiring mode
sensing, source arbitration or discharge interlocks. It does not provide mux
dips or board-controlled power cycling of an independently powered target.

## 3. USB power and sequencing

Use a known-good USB source/cable, preferably a powered hub during development.
Pico VBUS is usable as a power takeoff; its input label does not prohibit this.
There is no Pico-side VBUS fuse to rely on. F_AUX protects the added carrier
branch against gross faults, **not** as an accurate 250 mA current regulator or
a nanosecond switch-current limiter. It does not protect faults on the Pico.

Normal auxiliary budget: 10 mA target + approximately 10 mA VHIGH bleed +
5.5 mA VLOW bleed + driver/control/recharge allowance: **≤60 mA average**.
Reserve 150 mA for the Pico pending measurement. Verify total startup, normal
and fault demand against the actual USB source; do not assume an unconfigured
USB port grants 500 mA. Enable target rails only after USB configuration on a
bus-powered host. No external VSYS-only operating mode is qualified.

### Gate-driver supply

Retain **UCC27517DBVR**, with pin-local C13=100 nF and distributed C14=1 µF
additional ceramic bypass (about 7.33 mm VDD trace). Do not add a
boost converter just for universal cable support. Qualify **4.90–5.25 V at the
driver VDD pin** under the intended load, including F_AUX/cable drop. The UVLO
start maximum is 4.65 V over temperature; this leaves ≥250 mV initial margin.
If that condition is not met, do not arm: change the cable/source, or select a
different driver and requalify. USB 5 V by name alone is not a guarantee.
An ordinary 5 V −5% source is already 4.75 V before cable/PTC drop; the
250 mV margin exists only after the **4.90 V at-pin acceptance** is met.

### Mux supply and rail preparation

MUX_VCC is **TLV70436DBVR**, nominal 3.6 V, bypassed with 1 µF effective ≥0.47 µF.
Its input is isolated from AUX_5V by a Schottky diode and charged through 1 kΩ.
HOLD_IN has 100 µF nominal, **≥47 µF effective at input bias**, plus local ceramic
bypass. Add a 100 kΩ MUX_VCC bleeder. This supply powers the mux only.

Use the ordering code's actual accuracy/dropout and capacitor leakage in the
final check: budget MUX_VCC at 3.50–3.70 V, above VHIGH ≤3.35 V and below the
mux's 4.3 V operating maximum. Budget ≤0.10 mA total retention-branch demand,
including regulator, mux, bleeder and capacitor leakage; verify it on the bench.
For illustration, HOLD_IN from 4.2 V to 3.7 V with 47 µF and 0.10 mA lasts
235 ms. **This is a sequencing estimate, not a guaranteed brownout waveform.**

Both AP2112 EN pins share RAILS_EN (GP10), each with a 10 kΩ pull-down and 1 kΩ
GPIO series resistor. Their input bypass capacitors meet their datasheets.
At boot leave RAILS_EN=0, TARGET_ON=0, UART disabled and crowbar disarmed.
After USB configuration wait at least **1 s** for MUX_VCC preparation, enable the
target regulators, then wait **50 ms** before target connection. Test pads on
AUX_5V, MUX_VCC, VHIGH, VLOW and TARGET_VDD allow scope/DMM qualification.

Keep the rail regulators enabled during ordinary target power cycles; GP4
controls the downstream disconnect, not reservoir charging. On deliberate board
shutdown: disconnect target, disable interfaces/crowbar, then disable RAILS_EN.
On USB loss the retained mux supply must outlast the analog rails. Check the
**whole power-down trace**, including AP2112 reverse paths and Pico GPIO states;
release is blocked if an analog pin rises above MUX_VCC or a part rating is
exceeded. Do not assume an LDO blocks reverse current. The isolated retention
branch must not feed the main 5 V branch through an LDO reverse path.

**AP2112 auto-discharge:** with EN low and valid input power, the specified
part connects its output to ground through an approximately **60 Ω typical**
internal discharge path. A nominal 100 µF reservoir initially at 3.3 V stores
545 µJ and initially draws about 55 mA through that path. This is not a
guaranteed rating for this reservoir. If TARGET_ON is still asserted, the target
is also connected to the selected discharge path through the mux/15 Ω resistor.
The target and reservoir initially at equal voltage do **not** produce two
additive initial currents; their coupled discharge must be measured. Disconnect
the target **before** disabling RAILS_EN; the passive-only target-off statement
applies with the disconnect open. Capture GP4, RAILS_EN, both rails, TARGET_VDD
and MUX_VCC during deliberate shutdown and USB loss. USB-loss behavior is not
guaranteed by the EN-low/valid-input discharge specification.

## 4. Voltage-selector circuit and current budget

Use NX3L1T3157GMZ (SOT886/XSON6; not obsolete ,115/,132 ordering codes).
Connect Y0 to VHIGH **through R_HIGH**, Y1 to VLOW **through R_LOW**,
Z=output, VCC=MUX_VCC, GND=local ground.
**MUX_LOW=0 selects VHIGH; MUX_LOW=1 selects VLOW.** GP5 drives S through 100 Ω;
fit 10 kΩ S-to-GND pull-down and 100 nF local VCC bypass.

Each mux input has a **15 Ω, 1%, 1 W, pulse-rated resistor**: R_HIGH between
the VHIGH reservoir and Y0, R_LOW between the VLOW reservoir and Y1. Only one is
in the selected supply path. Neither is bridged in the default build. Putting
them at the inputs also includes external Z/disconnect-node capacitance in the
source-current bound; an output resistor alone would leave those nodes ahead
of the limiter. No direct rail/mux output power connector bypasses these parts.
They limit startup, recharge and short current, not just falling-edge current:

```text
worst first-order current ceiling = 3.35 V / (15 Ω × 0.99) = 226 mA
worst high-branch short dissipation = 3.35² / 14.85 = 0.756 W
normal 10 mA path dissipation       ≈ 1.5 mW in the selected resistor
```

These are passive/reservoir-fed upper bounds, **not a prediction of sustained
LDO current**. At nominal 1.8 V the low-branch bound is 121 mA / 0.218 W in
R16. The AP2112 specifies **50 mA typical short current at VOUT=0 V**, not a
complete guaranteed foldback curve for a short downstream of 15 Ω. A single
zero-volt test point cannot predict the actual LDO/resistor equilibrium. Measure
both rails' fault current, foldback and temperatures with a current-limited
source. F1's 250 mA hold does not ensure clearing these branch faults; neither
the resistor nameplate nor the LDO thermal shutdown establishes a safe sustained
fault rating for this PCB.

This is below the mux's **350 mA continuous absolute maximum**, rather than
designing to its 500 mA pulsed absolute maximum (specified at 1 ms, <10% duty).
Actual permissible operation still needs current, temperature and ringing
measurements. The resistor bounds the intended passive circuit with source
voltage ≤3.35 V; local parasitic charge sharing/control injection, ringing,
external injection and rail faults are not covered by that DC bound. Do not
place bypass capacitors on Y0/Y1/Z after the limiting resistors. The 500 mA
figure is not a recommended pulse rating.

The datasheet also limits switch drop to 0.4 V for current entering Yn.
At 226 mA and a 0.9 Ω Ron budget the drop is about 0.203 V. Ron is specified
under particular supply/current test conditions; confirm the complete operating
range rather than extrapolating the headline 0.5 Ω typical value. During a
dip current enters Z and leaves Y1; during recharge it enters Y0.

Budget **17 Ω maximum total path resistance** including the selected 15 Ω
resistor, mux, disconnect, shunt bypass and wiring. If measurement exceeds that budget,
update the timing/load qualification; do not claim a tested 17 Ω value.

Approximate no-load settling to within 50 mV of a fixed final source, with R=17 Ω:

| Total switched C | RC settling alone | Plus illustrative 50 ns switch allowance |
| ---: | ---: | ---: |
| 1 nF | 58 ns | 108 ns |
| 10 nF | 578 ns | 628 ns |
| 100 nF | 5.78 µs | 5.83 µs |
| 1 µF | 57.8 µs | 57.9 µs |

The allowance is not a guaranteed command-to-plateau specification: the mux
datasheet has tens-of-ns select timing, BBM, specific test loads and unequal
turn-on/off delays. Reservoir motion, load changes and cable inductance are
additional errors. A 100 ns command into a larger C can still produce a partial
dip; it does not establish a 1.8 V plateau. Do not remove necessary target
decoupling merely to make a calculation look faster.

## 5. Reservoirs and low-rail absorption

Each target regulator has **100 µF nominal reservoir + required local ceramic**.
C4/C7 select polarized EEE-FK1C101P (100 µF, 16 V, ±20%, 6.3×5.8 mm), with
C5/C8 as their 1 µF output ceramics. C9 is the same 100 µF part on HOLD_IN;
C1 is instead the auxiliary-input **10 µF ceramic**. Reservoir impedance/ESR/ESL adds fast excursions to the accumulated
charge estimates below; those estimates are not bounds on instantaneous rail
overshoot. Confirm the actual assembled waveforms.
Select actual parts for **47–125 µF total effective capacitance** on each rail,
including tolerance, bias and temperature, and verify regulator startup/stability.
Fit **330 Ω, 1%, ≥0.125 W** bleeders on both VHIGH and VLOW. These are upstream
of the input resistors, not capacitors fitted at Y0/Y1/Z or TARGET_VDD.

While enabled and regulating, the AP2112 is a source, not a specified active
sink for dip charge (its **shutdown discharge** is described in §3). The low reservoir absorbs
the fast charge, and the bleeder removes excess charge between events. With
ΔV=1.5 V and C_LOW≥47 µF:

- Four 100 nF transitions inject at most approximately 0.6 µC, giving ≤12.8 mV
  rise if none has recovered. Budget **15 mV** using a 1.6 V source difference.
- One 1 µF transition gives approximately 31.9 mV; budget **35 mV** at ΔV=1.6 V.
- VLOW bleed is about 5.45 mA / 9.8 mW; VHIGH bleed about 10 mA / 33 mW.
- In the ≤1 µF / one-pulse / 20 ms profile the average injected current is
  ≤80 µA. It is far below the bleeder current. Recovery of excess charge is
  roughly Q/I_bleed while the regulator stops sourcing, **not** automatically
  a 330 Ω × reservoir exponential back to 1.8 V.

These are conservative capacitor-charge budgets neglecting helpful target load,
not bounds on all regulator load-release overshoot or its absolute accuracy.
Finite charge sharing is Q=C_TARGET*C_LOW/(C_TARGET+C_LOW)*ΔV. The 20 ms spacing
also allows high-rail recharge, but test complete trains and regulator foldback.
More C/pulses/rate needs recalculation, not a firmware-only limit increase.

## 6. Target on/off: no active-discharge interlock required

Use **two P-channel MOSFETs with common sources and common gates**, with their
drains respectively at MUX_Z and the shunt/bypass input. Opposed body diodes
block both directions when off. Use **Si2377EDS-T1-GE3**, SOT-23: its manufacturer
datasheet specifies 0.165 Ω maximum per FET at VGS=-1.5 V, ID=-0.5 A, TJ=25 °C.
A 2.5 V-only gate-drive specification is not enough. Budget ≤0.8 Ω combined
resistance over the qualified temperature range within the 17 Ω total; the
25 °C specification alone does not guarantee that temperature budget.

Tie their gates to common source through 10 kΩ. A 2N7002 (source=GND) pulls the
gates down through 100 Ω when **GP4 TARGET_ON=1**. Its gate has 100 Ω series
and 10 kΩ to GND. Default is disconnected. This is a slow power-cycle element,
held fully on throughout a mux pulse; its turn-on time is not the glitch edge.
Allow **5 ms after TARGET_ON** before pulses/communications. This FET has a
deliberately slow internal gate resistance and microsecond switching tables;
do not use it as the fast selector. Source/gate capacitive coupling can still
change its transient conduction when the selected voltage moves: check actual
gate/source waveforms, added capacitance and off-state leakage on hardware.

TARGET_VDD has a permanent **10 kΩ** bleeder, not a discharge FET. With total
C≤1 µF, ideal decay from 3.35 V to 0.1 V takes 35.2 ms; allow **50 ms minimum
off time** and verify actual off voltage/leakage at the target. At ≤100 nF the
same estimate is 3.52 ms. A 50 ms delay is a qualified operating delay, not an
onboard voltage measurement. Increase it if measured behavior requires it.

Disconnect UART and all injecting debugger/application signals before off.
No guarantee of power-off while another device powers the target. Passive
discharge loses the original ambition of very fast automated power cycling,
but removes a live-source short hazard and an entire control/interlock circuit.

## 7. Crowbar circuit

- UCC27517 IN+ = GP2 through 100 Ω; 10 kΩ IN+-to-GND pull-down.
- IN- = 10 kΩ pull-up to driver VDD (**high inhibits**). Do not connect this
  5 V pull-up directly to a Pico GPIO.
- GP8 drives a 2N7002 gate through 100 Ω, with 10 kΩ gate-to-GND. Its source is
  GND; drain pulls IN- low through a removable **ARM link**. GP8=1 and link
  fitted enables the driver. An open link or reset/high-Z GP8 inhibits it.
- Driver OUT → 2.2 Ω tuning resistor → AO3400A gate; 10 kΩ gate-to-source.
  FET source and driver ground meet locally; drain goes only to GLITCH.
- Keep C13 100 nF pin-local; C14 1 µF is distributed additional bypass, not
  adjacent bulk. Include both supply/ground paths in waveform checks. Do not infer low-voltage edge
  speed or drain-current capability from the driver's advertised 4 A at 12 V
  or the FET's 30 A absolute-maximum headline.

Default pulls and an arm link give safe boot/reset handling, **not a hardware
maximum pulse width**. PIO must preload parameters before asserting GP2, never
perform a blocking FIFO/IRQ/trigger wait while high, and finish low. Stopping a
PIO machine or halting its clock while high can still hold the crowbar on.
Firmware abort must clear GP8 and force GP2 low, not just stop the machine.

No mandatory one-shot: PIO owns timing. A stuck-on pulse can damage the target;
this residual risk is accepted only for supervised expendable-target work.
Remove ARM while changing connections/firmware. A non-retriggerable timeout or
latched watchdog is a later option for unattended/valuable-target operation;
a retriggerable one-shot alone does not bound pulse trains or total energy.

Qualify first with a current/energy-limited RC dummy load (start ≤1 A peak and
≤100 nF at ≤3.3 V). These are **initial test conditions**, not automatic limits
the board enforces. Measure current, VGS relative to the FET source, rail
undershoot/overshoot and heating. A live target regulator can replenish energy
after its capacitor empties. A separate externally powered crowbar target must
have its own reviewed source/energy budget; F_AUX does not limit that current.

Use a short GLITCH/GND pair or SMA with a short target connection. Populate
one connection path, not a long SMA/header stub. Header continuous ratings do
not directly specify nanosecond pulse capability. Both connector choices need
actual loop-inductance and pulse-energy checks; SMA is not automatically a
better current contact. No default TVS/capacitor on GLITCH: room-temperature ESD
handling and non-hot-plug operation are the baseline. Optional protection must
earn its capacitance and clamp behavior in measurements.

## 8. Target signals

### Reset and trigger (baseline fitted)

Reset: 2N7002 source=GND, drain=target reset, gate=GP6 via 100 Ω with 10 kΩ
gate-to-GND. **RESET_ASSERT=1 pulls reset low.** Optional 10 kΩ reset pull-up
to TARGET_VDD, DNP when using a separately powered target; use the target's own
pull-up there. This is not a push-pull 3.3 V signal into the target.

Trigger: SN74LVC1G17 at Pico 3V3, 100 nF bypass; input via 1 kΩ with 100 kΩ
pull-down, output to GP3. Qualify only valid **3.3 V logic** and pulse widths
long enough for conditioning and PIO sampling. Include resistor/input/cable RC
and threshold uncertainty in delay calibration. It is a target-to-controller
input, not a fixed-3.3 V target pull-up. No universal 1.8 V trigger claim.

### UART (optional population, real level translation)

SN74AXC4T774PWR (TSSOP16): VCCA=Pico 3V3, VCCB=TARGET_VDD through a removable
reference link, 100 nF on each supply. DIR1=VCCA (GP0/A1 → B1/target RX),
DIR2=GND (target TX/B2 → A2/GP1). DIR3/DIR4=GND and unused B3/B4 inputs=GND;
unused A3/A4 outputs NC. OE is **high to disable**, with **R6 and R34 each 10 kΩ
to VCCA (5 kΩ effective)**, controlled by GP9; the enabled-low GPIO sinks about
0.66 mA. These are intentional controller-side and translator-side default
pulls, not a single 10 kΩ load. Add removable TX/RX links. It provides electrical isolation
when disabled/powered off, not galvanic isolation. No separate digital isolator.

Disable OE before dips or power cycles, and enable only after normal voltage
has returned. Do not communicate during the dip. Validate Ioff/sequencing with
both boards powered independently, and disconnect SWD/SWIM/application sources
that can inject current. A target can also be back-powered through its TX/debug
wiring elsewhere; this translator cannot fix the whole target board.

**The target-side 100 nF bypass is itself switched capacitance even with OE
disabled.** The ≤100 nF fast profile therefore normally leaves the UART option
unfitted or all three target-side links removed. For UART-equipped targets use
the ≤1 µF / one-pulse profile and include every capacitor. Do not remove the
translator's required bypass to obtain a nominally faster dip.

Populate **R40=4.7 kΩ, 1%, UVCCB-to-GND** and **R41=100 kΩ B2-to-GND** with
the UART option (both baseline DNP). AXC4T774 ICCB includes up to **12 µA sourced
out** at VCCA=3.6 V/VCCB=0 V. With R40 maximum 4.747 kΩ, that near-zero sizing
budget gives about **57 mV**, below the 100 mV isolation threshold; 100 kΩ had
insufficient sink margin. The single off-supply test point is not a complete
current-versus-voltage curve, so actual UVCCB decay/endpoint remains a bench
acceptance gate. R40/C18's nominal time constant is 0.47 ms; under a constant
12 µA source-current approximation, R+1%/C+10% take about 2.3 ms from 3.35 V to
0.1 V. This is a sizing estimate, **not a guaranteed delay or unpowered state**.

R40 draws about **0.70 mA at 3.3 V / 0.38 mA at 1.8 V**, up to about 0.72 mA
at 3.35 V with R−1%. R41 alone adds 33 µA at 3.3 V; the IC already has **71 kΩ
typical static pull-downs** on data I/Os (datasheet §7.3.9), allowing floating
data inputs. R41 is a retained explicit external default, not essential to cure
an otherwise undefined input; it and the internal B2 pull-down together draw
about **80 µA typical** when target TX is high. The internal resistance has no
minimum here, so that is not a worst-case load rating. Other data-port pulls
and translator supply current also count. Measure and subtract **all** interface
and bleeder loads from the **10 mA total** before allocating target MCU current.
Neither resistor is an isolation switch or a cure for
live-signal injection. **Remove/refit JP3, JP4 and JP5 together, only with board
and target power off and ARM removed. Never operate with JP3 open and either
signal link fitted.** All-links-open is the supported fast-profile state;
partial-link powered tests are qualification-only on current-limited dummy
hardware, not supported operation. Wait and verify UVCCB below 0.1 V before
claiming the translator's specified VCC-isolation state.

## 9. Timing, pin allocation and minimal control states

| GPIO | Function | Hardware/default intent |
| --- | --- | --- |
| GP0 / GP1 | Optional UART TX/RX | Target links open until interface fitted |
| GP2 | CROWBAR_PULSE | 10 kΩ pull-down; low |
| GP3 | Conditioned trigger input | Input |
| GP4 | TARGET_ON | 10 kΩ pull-down; disconnected |
| GP5 | MUX_LOW (0=3.3 V source, 1=1.8 V source) | 10 kΩ pull-down; high source |
| GP6 | RESET_ASSERT | 10 kΩ pull-down; released |
| GP7 | ARM-status LED | Off, 1 kΩ series resistor; indicates software state only |
| GP8 | DRIVER_ARM | 10 kΩ pull-down; inhibit unless ARM link fitted |
| GP9 | UART_DISABLE | OE pulled high; disabled |
| GP10 | RAILS_EN | Both regulator EN pins pulled low |

No ADC channels or mode-sense signals are required. Pico 2 exposes ADC GP26–28;
**GP29 is used internally for VSYS/3**, not a fourth free carrier input.
Test-pad/DMM/scope qualification substitutes for automatic rail monitoring in
this supervised build. Firmware delays are valid only for the qualified setup.

PIO instruction granularity at 150 MHz is 6.667 ns, not an analog pulse-width
guarantee. Keep asynchronous input synchronizers: two cycles plus sampling-phase
uncertainty, with further instruction/IO/driver delay. Preload the entire bounded
sequence. No host sleeps or MicroPython scheduling inside a pulse train.

| State | Driver | Target | UART |
| --- | --- | --- | --- |
| Boot/configuration | Inhibited; GP2 low | Off; rails disabled | Disabled |
| Prepare | Inhibited | Wait 1 s mux supply, then enable rails and wait 50 ms | Disabled |
| Powered idle | Inhibited | Normal source, disconnect on | Enable only for fitted/qualified option |
| Mux burst | Inhibited | On, GP5 pulsed then returned low | Disabled |
| Crowbar burst | GP8 enabled only for finite sequence | Explicit internal or independently powered setup | Disabled |
| Target off | GP8 low, GP2 low | Disconnect off; wait ≥50 ms, rail reservoirs may stay enabled | Disabled |
| Abort | Clear GP8 and GP2 first | Return GP5 low, disconnect target | Disabled |

There is no implemented firmware in this repository yet. USB loss and firmware
exceptions must request abort, but they are not independent asynchronous
hardware protection against a stalled PIO/clock or a driven-high GPIO.

## 10. Layout, measurement and remaining release work

- Use official Pico 2 two-1x20 socket geometry, orientation and USB clearance;
  pin 33 AGND is not the crowbar return.
- Keep the **local** driver bypass/gate/source loop on the carrier. The separate
  crowbar power loop includes the target capacitor, cable and target ground;
  minimize that whole loop, not just carrier trace length.
- Start with two layers and a continuous ground reference. Keep heavy pulse
  returns out of controller/trigger sense paths without creating a split-plane
  return discontinuity. Grounds are deliberately common, not galvanically isolated.
- Optional Kelvin shunt footprint defaults to a 0 Ω bypass. A fitted value adds
  to the 17 Ω budget. Use true-GND probe pads and differential shunt measurement;
  never attach a grounded scope clip to the live high side.
  **C3 implementation:** R39 is the fitted 0 Ω 1206 bypass. Optional R20 is a
  four-terminal WSK2512R1000FEA, 0.1 Ω; force pads 1/4 and sense pads 2/3 are
  distinct PCB nets, with sense-only traces to TP7/TP8. Remove R39 before fitting
  R20, and requalify the complete path/measurement. **R20 needs hand-soldering
  or a separately reviewed stencil/BOM/CPL variant**; baseline paste omits it.
  At 10 mA the sense signal is only 1 mV. TP7/TP8 are **13.0 mm** apart and
  their traces are not a tight differential pair; this option is for calibrated
  DC/low-bandwidth current checks initially, **not a validated fast-pulse current
  probe**. Probe-loop pickup, shunt inductance and bandwidth need measurement.
  The old JP1 header and two-terminal 10 Ω option are retired.
- Reviewed C3 bypass trace lengths: U4/C5 and U5/C8 about 3.86 mm each;
  U6 input/C10 about 2.96 mm; U6 output/C11 about 3.83 mm; U2 VDD/C13 about
  2.15 mm. Ground is connected through local copper/stitches; trace lengths are
  not full current-loop lengths or stability measurements. C12 bypasses the mux
  separately; C14 is additional distributed driver bulk bypass, not pin-local.
- Baseline target force routing Q3→R39→J2 remains about **48.6 mm / 3 layer
  transitions**, versus 7.7 mm direct. This is an accepted prototype layout
  compromise with 15 Ω damping, **not** a measured inductance/ringing clearance.
  Qualify the whole signal/ground/cable loop at 1 nF, 10 nF and 100 nF before
  claiming fast-corner performance. Re-route if measurements or target needs
  require it; a guessed nH/mm is not acceptance evidence.
- J1/J2 and other two-pin headers are mechanically interchangeable. Silkscreen
  now identifies GLITCH/NOT VDD, target VDD/GND, reset, trigger input and UART
  pin functions, but **does not provide keying**. Use separately marked/color
  coded cables, inspect pin 1/net mapping with power removed, and never move a
  two-pin shunt onto J1/J2. A keyed/different GLITCH connector is required before
  claiming misplug protection; it is not a baseline supervised-prototype claim.
- Use scope probes without 50 Ω DC termination across a low-voltage rail unless
  that load is explicitly budgeted. Probe capacitance and ground inductance count.
- Required before fabrication: exact orderable parts/footprints (especially mux
  and disconnect FETs), schematic/netlist, transient/power-down review, ERC/DRC,
  assembly BOM/CPL and a real quote. Reservoir stability/startup, mux-VCC hold-up
  and current/thermal limits remain **hardware qualification**, not proven claims.
- A useful fault on nRF52/STM8L depends on the exact chip/revision/board. This
  instrument does not promise a security bypass, calibrated glitch amplitude or
  unattended fail-safe behavior.
