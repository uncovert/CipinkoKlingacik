# Licence scope and notices

Copyright © 2026 ČipinkoKlingáčik contributors, for original project material.

- **Original hardware design:** CERN-OHL-P-2.0, full unmodified text in
  [LICENSE](LICENSE). This covers the original schematic/PCB arrangement,
  connectivity, part-selection/assembly/fabrication data and their original
  hardware-derived drawings under `hardware/`, subject to upstream exceptions below.
- **Original software and prose:** MIT, full text in [LICENSE-MIT](LICENSE-MIT).
  This covers `scripts/`, `tests/`, original Markdown documentation, CI and repository
  configuration. No firmware implementation is included.
- **Third-party KiCad primitives, footprints and embedded copies:** their original
  licences/copyrights and design-use exceptions remain applicable. Full upstream
  texts are in `hardware/vendor/LICENSE-kicad-symbols.md` and
  `hardware/vendor/LICENSE-kicad-footprints.md`; provenance/hashes are retained.
  Their use does not imply authorship of the upstream geometry or relicense it.
- **3D models:** installed KiCad-library models, not bundled STEP sources. Renders
  contain generic library geometry and a disclosed Pico proxy. Applicable upstream
  notices/terms are not replaced by an original-project licence declaration.
- Manufacturer documents are linked, not redistributed or relicensed. Raspberry Pi,
  KiCad, component/vendor and tool names do not imply endorsement.

Modification notice, 2026-10-30: public-release preparation renamed the project
and local libraries/artwork to ČipinkoKlingáčik, consolidated current documentation
and removed superseded attempts/intermediates. Electrical geometry/connectivity
and stable component UUIDs were preserved **at that C3 rename step**.

Subsequent modification notice, 2026-10-30: **C4 / alpha.2** changes U6 to the
TPS7A20 pinout with local routing/bypass placement changes, updates sourcing and
moves C4/C7/C9/C11 ground vias outside solder openings. The earlier rename-only
preservation statement is historical, not a claim that C4 is identical to C3.

This is an **unqualified engineering prototype**, supplied as-is without warranty.
No production, safety, pulse-performance, IP novelty or device-protection-bypass
claim is made. Preserve these notices and licence texts when redistributing
covered sources/manufacturing packages or products as required by their licences.
