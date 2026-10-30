#!/usr/bin/env python3
"""Run full PCB DRC/parity and export review drawings, never fabrication files.

Unrouted items, warnings, parity errors and ignored checks always fail.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import cairosvg

from kicad_sexpr import loads, children, child

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cli = ["kicad-cli"] if shutil.which("kicad-cli") else ["flatpak", "run", "--command=kicad-cli", "org.kicad.KiCad"]

    def run(*command):
        subprocess.run(command, cwd=ROOT, check=True)

    board = "hardware/cipinkoklingacik.kicad_pcb"
    run(*cli, "pcb", "drc", board, "-o", "hardware/cipinkoklingacik-drc.json", "--format", "json",
        "--schematic-parity", "--severity-all", "--all-track-errors", "--refill-zones")
    report = json.loads((HW / "cipinkoklingacik-drc.json").read_text())
    if report["ignored_checks"]:
        raise SystemExit(f"Unreviewed ignored DRC checks: {report['ignored_checks']}")
    status = {
        "revision": "C3", "fabrication_release": False,
        "design_stage": "engineering-prototype candidate",
        "routing_complete": not bool(report["unconnected_items"]),
        "geometry_violations": len(report["violations"]),
        "unconnected_items": len(report["unconnected_items"]),
        "schematic_parity_issues": len(report["schematic_parity"]),
        "board_sha256": digest(HW / "cipinkoklingacik.kicad_pcb"),
        "schematic_sha256": digest(HW / "cipinkoklingacik.kicad_sch"),
        "project_sha256": digest(HW / "cipinkoklingacik.kicad_pro"),
        "drc_sha256": digest(HW / "cipinkoklingacik-drc.json"),
        "hardware_qualification": "NOT PERFORMED",
    }
    (HW / "cipinkoklingacik-pcb-status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(f"PCB: {status['geometry_violations']} geometry violations, "
          f"{status['schematic_parity_issues']} parity issues, "
          f"{status['unconnected_items']} unconnected items. Hardware qualification NOT PERFORMED.", flush=True)
    if report["violations"] or report["schematic_parity"]:
        raise SystemExit("PCB geometry/parity check failed; see the full DRC JSON.")

    # Review list from actual board, not a claimed assembly-house CPL.
    pcb = loads((HW / "cipinkoklingacik.kicad_pcb").read_text())
    with (HW / "cipinkoklingacik-placement.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Reference", "MPN", "X_mm", "Y_mm", "Rotation_deg", "Layer", "DNP", "Status"])
        for fp in children(pcb, "footprint"):
            props = {f[1]: f[2] for f in children(fp, "property")}
            at = child(fp, "at")
            attr = child(fp, "attr") if children(fp, "attr") else []
            writer.writerow([props["Reference"], props.get("MPN", ""), at[1], at[2],
                             at[3] if len(at) > 3 else "0", child(fp, "layer")[1],
                             "yes" if "dnp" in attr else "no", "REVIEW LIST - USE BASELINE SMT EXPORT FOR PLACEMENT"])
    run(*cli, "pcb", "export", "svg", board, "-o", "hardware/cipinkoklingacik-pcb-top.svg",
        "--layers", "F.Cu,F.SilkS,F.Fab,Edge.Cuts", "--mode-single", "--fit-page-to-board",
        "--exclude-drawing-sheet", "--crossout-DNP-footprints-on-fab-layers")
    run(*cli, "pcb", "export", "pdf", board, "-o", "hardware/cipinkoklingacik-pcb-review.pdf",
        "--layers", "F.Cu,B.Cu,F.Fab,F.SilkS,Edge.Cuts", "--common-layers", "Edge.Cuts",
        "--mode-multipage", "--sketch-pads-on-fab-layers", "--crossout-DNP-footprints-on-fab-layers")
    run(*cli, "pcb", "export", "svg", board, "-o", "hardware/cipinkoklingacik-pcb-bottom.svg",
        "--layers", "B.Cu,Edge.Cuts", "--mode-single", "--fit-page-to-board", "--exclude-drawing-sheet")
    for side in ("top", "bottom"):
        cairosvg.svg2png(url=str(HW / f"cipinkoklingacik-pcb-{side}.svg"),
                        write_to=str(HW / f"cipinkoklingacik-pcb-{side}.png"), output_width=1800)
    if report["unconnected_items"]:
        raise SystemExit("Routing is INCOMPLETE. Strict PCB check failed (no fabrication release).")


if __name__ == "__main__":
    main()
