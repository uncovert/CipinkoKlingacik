# Pinned KiCad assets

Source: KiCad **10.0.7** Flatpak libraries installed on 2026-10-28.

- `primitives.kicad_sym`: R, C, C_Polarized, D_Schottky, LED from `Device`;
  Q_NMOS_GSD and Q_PMOS_GSD from `Transistor_FET`. Parsed/serialized by
  kiutils 1.4.8, then copied/renamed by the schematic generator.
- `../CipinkoKlingacik.pretty/`: unmodified standard KiCad footprints.
- `footprints.json`: original library/name and SHA-256 of each footprint.
- `LICENSE-kicad-symbols.md` / `LICENSE-kicad-footprints.md`: upstream licenses
  including their design-use exceptions. These apply to these vendored assets,
  not a new licensing declaration for the whole project.

An explicit library refresh uses `scripts/vendor_kicad_assets.py`, from a venv
with the hardware requirements installed. This overwrites pinned assets. Review
pad geometry/orientation and the manifest diff, regenerate, and re-run all checks.
Normal regeneration does not update footprints from the system installation.

3D models are optional references to the KiCad 10 model libraries, not vendored
or necessary for electrical connectivity. Socket/USB clearance still requires
a physical/mechanical check.
