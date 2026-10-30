#!/usr/bin/env python3
"""Snapshot selected installed KiCad 10 assets; never run as part of a normal build.

Requires the org.kicad.KiCad Flatpak and kiutils. Review library upgrades explicitly.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from kiutils.symbol import SymbolLib
from hardware_parts import FOOTPRINT_SOURCES

ROOT = Path(__file__).resolve().parent.parent
BASE = "/app/extensions/Library"


def installed(path):
    return subprocess.check_output(["flatpak", "run", "--command=cat", "org.kicad.KiCad", path])


def main():
    target = ROOT / "hardware" / "CipinkoKlingacik.pretty"
    target.mkdir(exist_ok=True)
    manifest = {}
    for name, library in FOOTPRINT_SOURCES.items():
        source = f"{BASE}/Footprints/footprints/{library}.pretty/{name}.kicad_mod"
        data = installed(source)
        (target / f"{name}.kicad_mod").write_bytes(data)
        manifest[name] = {"upstream": f"{library}.pretty/{name}.kicad_mod", "sha256": hashlib.sha256(data).hexdigest()}

    dest = ROOT / "hardware" / "vendor"
    dest.mkdir(exist_ok=True)
    primitives = []
    for library, names in {
        "Device": ["R", "C", "C_Polarized", "D_Schottky", "LED"],
        "Transistor_FET": ["Q_NMOS_GSD", "Q_PMOS_GSD"],
    }.items():
        data = installed(f"{BASE}/symbols/{library}.kicad_sym").decode()
        # kiutils parses the S-expression but needs a file for this entry point.
        from kiutils.utils import sexpr
        lib = SymbolLib.from_sexpr(sexpr.parse_sexp(data))
        for name in names:
            item = next(s for s in lib.symbols if s.entryName == name)
            assert not item.extends, f"Resolve inherited symbol {name} before importing"
            primitives.append(item)
    SymbolLib(version="20211014", generator="kiutils", symbols=primitives).to_file(str(dest / "primitives.kicad_sym"))
    for kind in ("Symbols", "Footprints"):
        data = installed(f"{BASE}/{kind}/share/licenses/org.kicad.KiCad.Library.{kind}/kicad-{kind.lower()}/LICENSE.md")
        (dest / f"LICENSE-kicad-{kind.lower()}.md").write_bytes(data)
    (dest / "footprints.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
