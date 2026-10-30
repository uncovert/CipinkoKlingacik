# C4 review and provenance

The current design underwent repeated independent **DeepSeek V4.1 Flash 1017
(Ollama)** reviews, primary verification of manufacturer evidence, justified
corrections and post-fix review. Final review found no known actionable
design-file defect for the stated supervised engineering-prototype scope.
**This is not hardware qualification, an IP novelty audit or production approval.**

## Verified corrections retained

- Correct manufacturer pinouts/polarities, full Pico socket and unused-pin capture;
  exact candidate parts and pinned KiCad geometry with native DNP population.
- Complete routing with strict DRC/parity and no ignored PCB checks/exclusions.
- Shortened regulator/driver bypass paths; dual GND pours and local transition
  stitching; separate crowbar and mux current-limit paths.
- Optional UART C18 downstream of its reference link; R40 **4.7 kΩ** sized with
  the translator's off-supply source-current budget, R41 **100 kΩ** supplemental
  input default. All-links-together/power-off procedure remains mandatory.
- R6/R34 parallel 10 kΩ pulls disclosed as **5 kΩ effective**. Internal UART data
  pull-down loads are included in the total-target-load accounting.
- AP2112 EN-low discharge path disclosed, without adding fictitious initial
  currents from equal-voltage capacitors. A typical short-current datum is not
  extrapolated into a guaranteed foldback or sustained thermal rating.
- Optional Kelvin R20 force/sense separation, baseline R39 bypass, baseline-only
  stencil exclusions and explicit variant/hand-solder requirements.
- Connector function labels, accessory population and sourcing/rotation caveats.

Accepted compromises remain explicit in [PCB_REVIEW.md](../hardware/PCB_REVIEW.md):
~48.6 mm target force detour, unkeyed connectors, 13 mm-spaced Kelvin pads limited
initially to calibrated DC/low-bandwidth checks, distributed C14 bypass, and no
independent stuck-on timer. None is represented as a measured capability.

## Tool/source provenance

The schematic is generated from project-maintained Python using stable UUIDs;
the fully routed PCB is authoritative. Non-critical routing was completed locally
using [Freerouting 2.5.0](https://github.com/freerouting/freerouting/releases/tag/v2.5.0),
followed by explicit geometry/power-width/return review and KiCad 10.0.7 checks.
No remote routing service is needed to open or maintain this release.
Manufacturer source links are in [SOURCES.md](../reference/SOURCES.md); KiCad
asset provenance/licences are retained in [vendor/](../hardware/vendor/README.md).

The historical C3 release rename to **ČipinkoKlingáčik** changed filenames, library identifiers,
titles and silkscreen branding, not the electrical design at that rename step. Stable schematic/PCB
UUIDs, contract, component positions/pads, tracks, vias and outline were compared
with a pre-rename snapshot. The snapshot/research diaries are retained outside
the public tree, not bundled as obsolete alternative designs.

The later **C4 / alpha.2** sourcing/DFM revision is not a rename-only change:
TPS7A20 replaces TLV704 with a different pinout, C10/C11 move, local U6 routing
changes, and C4/C7/C9/C11 ground vias move out of solder openings. F1/R15/R16 and
eight Basic passives have reviewed replacement selections. See [JLCPCB.md](JLCPCB.md)
and [PCB_REVIEW.md](../hardware/PCB_REVIEW.md); the historical preservation
comparison does not assert that C4 is electrically/geometrically identical to C3.

All current reports/manifests bind evidence to the actual sources; a green test
does not replace current measurement or supplier approval. Remaining gates are
tracked in [VALIDATION.md](VALIDATION.md). There is no implemented firmware, built
prototype, measured glitch waveform or demonstrated target attack in this release.
