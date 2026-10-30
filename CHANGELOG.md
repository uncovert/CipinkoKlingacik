# Changelog

## 0.1.0-alpha.1 — 2026-10-30

Initial public-release preparation of **ČipinkoKlingáčik**, hardware revision C3.

- Fully routed Pico 2 carrier, separate crowbar/mux/reset/trigger functions,
  bounded mux current, retained mux supply and optional UART/Kelvin provisions.
- Strict ERC/DRC/parity and regression/export checks; baseline assembly data,
  Gerber/drill/stencil package and illustrative CAD views.
- Repeated independent review and verified corrections, including local bypass
  routing, UART off-supply bleeder and fully enabled PCB DRC checks.
- Rebranded source files/libraries/artwork; preserved electrical geometry,
  component UUIDs and connectivity. Removed obsolete concepts, intermediate
  routing/repair tools and downloaded research documents from the release tree.
- CERN-OHL-P-2.0 hardware / MIT original software and prose; upstream KiCad notices retained.

**Not implemented/qualified:** firmware, SWD controller/synchronization,
supplier/rotation/mechanical approval, prototypes or physical measurements.
This alpha is not a production release, a hardware certification or a demonstrated attack.
