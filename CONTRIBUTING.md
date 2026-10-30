# Contributing

Please keep the project within its documented supervised engineering-prototype
scope, or propose explicit requirements before changing that scope.

- Read [BUILD.md](docs/BUILD.md), source ownership in [hardware/README.md](hardware/README.md),
  [DESIGN.md](docs/DESIGN.md) and [VALIDATION.md](docs/VALIDATION.md).
- Edit the schematic generator/parts definitions, not only their generated files.
  Edit the authoritative PCB deliberately; never regenerate it from a historical seed.
- Do not change stable UUIDs, remove current limiters, suppress DRC checks or
  overwrite unrelated work merely to make tests pass.
- Keep KiCad primitive/footprint licence notices; review pinned-asset upgrades
  separately. Cite manufacturer documents rather than bundling their PDFs.
- After hardware edits run fresh ERC/DRC/parity, return review, renders and
  exports, then tests. Describe actual measurements separately from calculations.
- Add regression tests for proven defects; disclose accepted tradeoffs and
  unperformed validation. Never call a clean DRC a hardware certification.
- Do not commit credentials, local KiCad preferences, cache/venv directories,
  temporary boards or unapproved vendor uploads. Release outputs belong in `dist/`.

Contributions to original hardware are offered under CERN-OHL-P-2.0; original
software/prose contributions under MIT. Third-party material retains its own
terms. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
