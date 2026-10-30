# ČipinkoKlingáčik hardware — C4

**Engineering-prototype design files, not qualified hardware.** Open
[`cipinkoklingacik.kicad_pro`](cipinkoklingacik.kicad_pro) in **KiCad 10**.
The A2 schematic uses named connections and project-local pinned libraries.
No library download is needed to inspect its connectivity.

## Authoritative sources and exports

| Files | Purpose |
| --- | --- |
| `cipinkoklingacik.kicad_pcb` | Authoritative, fully routed PCB; edit in PCB Editor |
| `cipinkoklingacik.kicad_sch` / `.kicad_sym` | Generator-owned schematic/symbols |
| `cipinkoklingacik.kicad_pro`, `fp-lib-table`, `sym-lib-table` | Project/rules/library mapping |
| `CipinkoKlingacik.pretty/`, `vendor/` | Pinned footprints/primitives, provenance and licences |
| [Schematic PDF](cipinkoklingacik.pdf) / [preview](cipinkoklingacik-schematic.png) | Review drawings |
| [Full DRC](cipinkoklingacik-drc.json), [ERC](cipinkoklingacik-erc.rpt), [status](cipinkoklingacik-pcb-status.json) | Static check evidence and source hashes |
| [Connectivity](cipinkoklingacik-connectivity.json), `cipinkoklingacik.net` | Intended contract and actual KiCad export |
| [Baseline BOM](cipinkoklingacik-bom.csv), [all parts](cipinkoklingacik-parts-all.csv) | Exact candidate parts and native DNP state |
| [Manufacturing](manufacturing/README.md) | Baseline Gerber/drill/stencil/BOM/placement package |
| [Visuals](visuals/README.md) | Illustrative assembled/top/bottom/service views |

The board has **92 schematic footprints + four mechanical footprints**.
Baseline population: **68 SMT + seven hand-fit references**, eight bare probe
pads, and nine DNP references: **U8, C18, JP3–JP5, R20, R31, R40, R41**.
R39=0 Ω is fitted. JP2 ARM has **no cap fitted**. Module headers/sockets and loose
caps are separate accessories, not additional SMT rows.

## Source ownership / maintenance

- **PCB:** authoritative and not generator-owned. There is no board-regeneration
  script in this release. Preserve intentional edits; see [BUILD.md](../docs/BUILD.md).
- **Schematic:** edit `scripts/generate_kicad_schematic.py` and
  `scripts/hardware_parts.py`; normal regeneration overwrites schematic, local
  symbols, library tables, connectivity and BOMs. This is not a round-trip editor.
- Stable UUIDs are deliberately retained across the project rename. The legacy
  UUID seed is an internal identifier, not an old project output or PCB generator.
- Footprint upgrades are explicit operations; normal regeneration never updates
  pinned library geometry. Follow [vendor/README.md](vendor/README.md).
- After a PCB edit: run strict checks, refresh return review, rerun strict
  checks, regenerate renders and prototype exports, then run all tests.

## Check interpretation

KiCad 10.0.7 evidence: **ERC 0 errors / 0 warnings**; **PCB DRC 0 violations /
0 unconnected / 0 schematic parity issues**; no ignored PCB checks or exclusions.
The regression suite rejects new ignores and pins the reviewed severity settings.

ERC retains four disclosed standard ignores: single-use global labels, four-way
wire junctions, SPICE-model issues and footprint-filter mismatch. This local-label,
single-sheet, no-SPICE custom-symbol capture does not use global labels or
footprint filters; PCB footprint-filter checking is enabled. Static checks are
not electrical, thermal, assembly or firmware qualification.

## Important net aliases

| Alias | Meaning |
| --- | --- |
| `GL` | Separate crowbar drain — **not** target supply |
| `TVDD` / `T_PRE` | Target supply / pre-shunt supply |
| `VH` / `VL` | High/low upstream reservoirs |
| `MVCC` / `HOLD` | Retained mux supply / its held input |
| `MY0` / `MY1` / `MZ` | Mux input/output nodes |
| `MUX_CMD` / `MUX_S` | GP5 command / mux select |
| `CB_PULSE` / `ARM_EN` | GP2 pulse / GP8 driver arm |
| `TGT_ON` / `REN` | GP4 disconnect / GP10 rail enable |
| `RST_ASSERT` / `RST_T` | Reset control / open-drain target reset |
| `TRIG_IN` / `TRIG_OUT` | Raw trigger input / conditioned GP3 input |
| `UART_OE` / `UVCCB` | GP9 UART disable / isolated UART target reference |
| `ISENSE_P` / `ISENSE_N` | Separate R20 sense terminals; differential probing only |

Full pin allocation, timing and power states are in [DESIGN.md](../docs/DESIGN.md).
Read [PCB_REVIEW.md](PCB_REVIEW.md) and [VALIDATION.md](../docs/VALIDATION.md)
before any order or target connection.
