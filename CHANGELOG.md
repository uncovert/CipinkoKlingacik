# Changelog

## 0.1.0-alpha.2 — 2026-10-30

Hardware revision **C4** distinguishes the TPS7A20 layout from incompatible C3
TLV704 packages. Updated sources, silkscreen, manifests and manufacturing/visual
filenames must be used as one set.

- Prefer eight Basic passive SKUs without changing values/packages. Replace
  low-stock TLV70436 with TI TPS7A2036P and deliberately reroute U6/C10/C11 for
  its pinout, retained-input EN and local bypass/ground returns.
- Add exact LCSC fields, grouped JLCPCB BOM/CPL exports, stock/feeder audit and
  an offline quantity-aware budget model with explicit exclusions.
- Emit LF-only CSVs to preserve manifest hashes across fresh Git checkouts.
- Resolve the old stock blockers with Littelfuse 1206L025YR and Yageo 15 Ω / 1% /
  2 W limiters; no lower-quality clones or pulse-overload assumptions. All selected
  baseline SKUs stocked in the revised snapshot. Update TCR/retention calculations,
  pinout/locality regressions and upload files. Physical qualification and supplier
  production-placement review remain open; no order or protection bypass implied.
- Move C4/C7/C9/C11 return vias clear of SMT solder openings; add a DFM guard
  including negative fixtures for all four old sites, without relaxing DRC rules.
- Correct BAT54WS datasheet, U3 pitch and selected resistor values; itemize D1
  leakage, disclose assembly-minimum/attrition fields, and retire unsupported
  historical savings totals. Bind fresh ERC and 2D review render hashes.

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
