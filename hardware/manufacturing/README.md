# ČipinkoKlingáčik C4 — prototype manufacturing data

**Supplier review / engineering prototypes only.** No quote, sourcing/rotation,
socket/USB mating, soldering process or physical performance has been approved.
Manifest retains `fabrication_release: false` and hardware qualification
`NOT PERFORMED`. Nothing here places an order.

| Output | Purpose |
| --- | --- |
| [Bare-board ZIP](cipinkoklingacik-C4-bare-pcb.zip) | Gerbers, separate PTH/NPTH drills/maps and applicable licence/notices |
| `gerbers/` | Unpacked copper, masks, silks, outline, drill files/maps and Gerber job |
| `stencil/cipinkoklingacik-F_Paste.gtp` | **Baseline-only** top paste; no DNP apertures |
| `assembly/baseline-smt-bom.csv` / `baseline-smt-pos.csv` | Matching **68 fitted SMT** references, exact candidate MPNs |
| `assembly/baseline-hand-fit.csv` | **Seven** hand-fit references: U1, J1–J5, JP2 |
| `assembly/jlcpcb-bom.csv` / `assembly/jlcpcb-cpl.csv` | JLCPCB upload formats: **24 grouped SKUs / 68 SMT placements**, explicit LCSC codes |
| `assembly/jlcpcb-sourcing.csv` / `assembly/jlcpcb-cost-estimate.json` | Dated stock/feeder audit and budget model, NOT a checkout quote |
| `assembly/accessories-candidates.csv` | Module headers/sockets, loose ARM cap, optional three UART caps, user-supplied M2.5 hardware |
| `drill-report.txt` | 134 × 0.3 mm vias + 59 × 1 mm plated holes; four × 2.7 mm NPTH |
| `manifest.json` | Source/report SHA-256, population and all artifact hashes/sizes |

**Uploading to JLCPCB?** Follow [the supplier guide](../../docs/JLCPCB.md): upload
the bare-board ZIP, `assembly/jlcpcb-bom.csv` and `assembly/jlcpcb-cpl.csv`.
The revised TI U6/Littelfuse F1/Yageo 2 W R15/R16 selections eliminate the previous
stock blockers. All selected SKUs are stocked in the new audit; checkout stock,
attrition and production-placement review remain mandatory. **U6 pinout/local
routing and C10/C11 positions changed**; never mix this package with earlier
TLV704 Gerbers/BOM/CPL. Original baseline CSVs remain
engineering/reference exports, not the supplier-column formats.

## Assembly rules

- **Fit R39=0 Ω**. Leave **U8, C18, JP3–JP5, R20, R31, R40, R41 DNP**. Their
  copper/mask lands stay present. The eight probe pads are PCB features, not posts.
- **JP2 ARM ships open**; supply its cap loose, not on the board.
- Optional R20 is WSK2512R1000FEA, 0.1 Ω four-terminal. **Remove R39 first**;
  hand-solder or create a reviewed stencil/BOM/placement variant. Baseline paste
  has no R20 apertures. Use differential, initially DC/low-bandwidth measurement.
- Optional UART also needs a reviewed variant/hand-soldering: U8/C18/JP3–JP5,
  **R40=4.7 kΩ**, **R41=100 kΩ** and three link caps. Change all links together,
  board/target power off and ARM removed.
- Hand-fit module headers, sockets, Pico 2 and connectors after checking pin 1,
  package identity, polarity, mating height, lead/drill fit and USB access.
  No unreviewed substitutions, particularly U3 XSON6, revised TPS7A20 U6 pinout
  (IN1/GND2/EN3/NC4/OUT5; EN=HOLD_IN), exact 2 W limiters or Q2/Q3.
- Four M2.5 screws/standoffs remain user-supplied pending stack/head/length/material
  approval. No mounting hardware is silently included in SMT placement.

## Coordinate / fabrication conventions

- Outline **100 × 85 mm**, upper-left `(0,0)` in board coordinates. Intended
  two-layer 1.6 mm FR4, nominal 1 oz copper; actual stackup/process unapproved.
- Generic KiCad placement: **millimetres, X right, Y up**; negative `PosY` is
  intentional. All SMT is `top`. Supplier feeder/reel rotation, pick origins and
  any coordinate conversion must be approved before machine assembly.
- Minimum design geometry 0.20 mm, vias 0.6/0.3 mm; confirm process capability,
  finished hole/plating interpretation, mask registration and XSON6 assembly.
- Socket/SMT ground pads are solid-connected; five THT connector ground pads
  retain thermals. Account for thermal mass in the reviewed soldering profile.
- C4/C7/C9/C11 GND vias are outside SMT solder openings (minimum annulus gap
  0.125 mm at C11, baseline guard ≥0.10 mm). Vias are tented, not filled/capped;
  no via-in-pad process is assumed. Do not substitute old C3 fabrication data.
- J1.1=crowbar, J2.1=target VDD, J3.1=reset, J4.1=3.3 V trigger input; their
  pin 2 is GND. J5.1=GND, .2=target RX, .3=target TX. Labels are not keying;
  never put a jumper cap across J1/J2. Check all cable/net mappings before power.

## Re-export

```sh
.venv/bin/python scripts/export_prototype.py
python3 -m unittest discover -s tests -v
```

See [BUILD.md](../../docs/BUILD.md) for dependencies and editing sequence.
Archive/population/coordinate/drill/stencil/hash checks are automated, not physical
qualification. Before ARM, measure **4.90–5.25 V at driver VDD** and complete
[VALIDATION.md](../../docs/VALIDATION.md). Do not mix artifacts from different manifests.
