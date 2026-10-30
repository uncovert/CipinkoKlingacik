# Connecting a target / SWD overview

**Firmware is not implemented and hardware bring-up is not performed.** Treat
this as wiring intent, not permission to connect an unqualified board directly
to a valuable target. First use current/energy-limited dummy loads.

Disconnect all power and remove the **JP2 ARM cap** before wiring. Check pin 1:
the two-pin headers are mechanically interchangeable and are not misplug-safe.

## A. Carrier-powered target — voltage-mux experiments

| Carrier | Target |
| --- | --- |
| J2.1 — VDD | **Isolated** MCU supply rail; not USB 5 V or an unknown power pin |
| J2.2 — GND | Target GND |
| J3.1 — RESET (optional) | nRESET if available/configured; open-drain assertion |
| J3.2 — GND | Common GND |
| J4.1 — TRIG IN (optional) | Valid **3.3 V** timing marker |
| J4.2 — GND | Marker ground |
| J1 — GLITCH | Leave disconnected initially |

J2 must not fight the target board's regulator, USB, battery or debugger power
output. Use the target schematic to isolate the intended rail. Entire development
kits often exceed the **10 mA total** load or switched-capacitance budget. Do not
remove required decoupling simply to obtain a faster dip.

## B. Independently powered target — crowbar experiments

- Leave **J2.1 disconnected**; never feed an external supply into it.
- Target uses its own reviewed current/energy-limited supply.
- J1.1 is a MOSFET **short-to-GND output**, not a power supply. Connect only to
  the specifically identified rail under test; J1.2 goes to its nearby GND with
  a very short paired connection. The carrier's fuse does not limit this current.
- Reset/trigger remain optional as above. Do not guess nRF52 DEC/DCC/VDDH pins;
  the exact chip and board power topology must be checked first.

## SWD and timing

The carrier is not currently an SWD debugger. Use an external probe directly to
target SWDIO/SWCLK/GND with an appropriate target-voltage reference; verify that
the reference is a sense input rather than another power output. Debugger signals
can back-power an otherwise unpowered target.

For startup experiments the Pico can own reset release/power timing; for an
SWD-transaction-timed experiment, the SWD controller ideally provides a hardware
marker into J4. A random USB probe may not expose one. PC/USB command ordering is
not a nanosecond timing reference. Target UART or cooperating target firmware
is not inherently required. Software coordination/PIO/abort logic must still be
implemented and tested; no device-specific protection bypass is guaranteed.

## Optional UART

Leave unpopulated if unused. A populated variant needs U8/C18/JP3–JP5/R40/R41,
three link caps and a reviewed assembly variant or hand-soldering. J5.1=GND,
J5.2=target RX, J5.3=target TX. Change all three links together with all power off;
disable UART during dips/off and count its bypass/load in the target budget.

See [DESIGN.md](DESIGN.md) for limits and [VALIDATION.md](VALIDATION.md) for gates.
