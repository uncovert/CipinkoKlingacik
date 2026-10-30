#!/usr/bin/env python3
"""Regenerate C4, run strict KiCad ERC/PCB checks and test exported connectivity.

Use a venv with requirements-hardware.txt. Requires KiCad 10 CLI (native or
Flatpak) and pdftoppm. PCB checks reject incomplete routing; they do NOT
establish hardware qualification or supplier release approval.
"""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"


def run(*command):
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    cli = ["kicad-cli"] if shutil.which("kicad-cli") else ["flatpak", "run", "--command=kicad-cli", "org.kicad.KiCad"]
    run(sys.executable, "scripts/generate_kicad_schematic.py")
    generated = ["cipinkoklingacik.kicad_sch", "cipinkoklingacik.kicad_sym", "cipinkoklingacik-bom.csv",
                 "cipinkoklingacik-parts-all.csv", "cipinkoklingacik-connectivity.json", "sym-lib-table", "fp-lib-table"]
    before = {name: (HW / name).read_bytes() for name in generated}
    run(sys.executable, "scripts/generate_kicad_schematic.py")
    for name, data in before.items():
        if (HW / name).read_bytes() != data:
            raise RuntimeError(f"Non-reproducible generator: {name}")
    schematic = "hardware/cipinkoklingacik.kicad_sch"
    run(*cli, "sch", "erc", schematic, "-o", "hardware/cipinkoklingacik-erc.rpt",
        "--severity-all", "--exit-code-violations")
    run(*cli, "sch", "export", "netlist", schematic, "-o", "hardware/cipinkoklingacik.net")
    netlist = HW / "cipinkoklingacik.net"
    netlist.write_text(netlist.read_text().replace(str(ROOT) + "/", ""))
    run(*cli, "sch", "export", "bom", schematic, "-o", "hardware/cipinkoklingacik-kicad-bom.csv")
    run(*cli, "sch", "export", "pdf", schematic, "-o", "hardware/cipinkoklingacik.pdf")
    run(*cli, "sch", "export", "svg", schematic, "-o", "hardware/svg")
    run("pdftoppm", "-scale-to", "3000", "-singlefile", "-png",
        "hardware/cipinkoklingacik.pdf", "hardware/cipinkoklingacik-schematic")
    if (HW / "cipinkoklingacik.kicad_pcb").exists():
        if (HW / "manufacturing" / "manifest.json").exists():
            run(sys.executable, "scripts/export_prototype.py")
        else:
            run(sys.executable, "scripts/check_pcb.py")
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
    print("C4 strict static checks passed. Hardware qualification and supplier approval remain open.")


if __name__ == "__main__":
    main()
