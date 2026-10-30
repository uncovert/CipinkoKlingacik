#!/usr/bin/env python3
"""Export checked engineering-prototype data, NOT supplier/production approval.

Requires a clean full DRC/parity result. Generates bare-board Gerber/drill data,
baseline-only paste, baseline SMT BOM/positions and hand-fit lists, plus hashes.
Never orders boards or claims hardware qualification.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

from export_jlcpcb import SNAPSHOT, export as export_jlcpcb

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"
OUT = HW / "manufacturing"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cli = ["kicad-cli"] if shutil.which("kicad-cli") else ["flatpak", "run", "--command=kicad-cli", "org.kicad.KiCad"]

    def run(*command):
        subprocess.run(command, cwd=ROOT, check=True)

    run(sys.executable, "scripts/check_pcb.py")
    review = json.loads((HW / "cipinkoklingacik-return-review.json").read_text())
    assert review["board_sha256"] == sha(HW / "cipinkoklingacik.kicad_pcb"), "Refresh return-path review before exporting"
    assert all(t["nearest_ground_via_mm"] <= 2.01 for t in review["signal_transitions"]), "Unreviewed signal return transition"
    with (HW / "cipinkoklingacik-parts-all.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    fitted = [r for r in rows if r["DNP"] == "no" and r["Assembly"] != "PCB feature"]
    smt = [r for r in fitted if r["Assembly"] == "SMT"]
    hand = [r for r in fitted if r["Assembly"] != "SMT"]
    for subdirectory in ("gerbers", "stencil", "assembly"):
        (OUT / subdirectory).mkdir(parents=True, exist_ok=True)
    for name, selected in (("baseline-smt-bom.csv", smt), ("baseline-hand-fit.csv", hand)):
        with (OUT / "assembly" / name).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(selected)
    run(*cli, "pcb", "export", "pos", "hardware/cipinkoklingacik.kicad_pcb", "-o",
        str(OUT / "assembly" / "baseline-smt-pos.csv"), "--format", "csv", "--units", "mm",
        "--side", "front", "--smd-only", "--exclude-dnp")
    with (OUT / "assembly" / "baseline-smt-pos.csv").open() as stream:
        positions = list(csv.DictReader(stream))
    assert {r["Ref"] for r in positions} == {r["Reference"] for r in smt}, "BOM/position population mismatch"
    export_jlcpcb(smt, positions, OUT / "assembly")
    run(*cli, "pcb", "export", "gerbers", "hardware/cipinkoklingacik.kicad_pcb", "-o", str(OUT / "gerbers"),
        "--layers", "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts", "--check-zones")
    run(*cli, "pcb", "export", "drill", "hardware/cipinkoklingacik.kicad_pcb", "-o", str(OUT / "gerbers"),
        "--format", "excellon", "--excellon-units", "mm", "--excellon-separate-th",
        "--generate-map", "--map-format", "pdf", "--generate-report",
        "--report-path", str(OUT / "drill-report.txt"))
    # DNP copper/mask pads stay on the real board. Only baseline paste is omitted.
    with tempfile.TemporaryDirectory(prefix=".baseline-stencil-", dir=HW) as directory:
        stencil_board = Path(directory) / "cipinkoklingacik.kicad_pcb"
        run("flatpak", "run", "--command=python3", "org.kicad.KiCad",
            "scripts/prepare_baseline_stencil.py", "--output", str(stencil_board))
        run(*cli, "pcb", "export", "gerbers", str(stencil_board), "-o", str(OUT / "stencil"),
            "--layers", "F.Paste")

    with (OUT / "assembly" / "accessories-candidates.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["Purpose", "MPN", "Manufacturer", "Qty", "Fit_policy", "Approval"])
        for row in (
            ("Pico module headers", "TSW-120-07-G-S", "Samtec", 2, "Hand-fit to SC1631", "Mating/height approval pending"),
            ("Carrier Pico sockets", "SSQ-120-03-G-S", "Samtec", 2, "Hand-fit at U1", "Mating/height approval pending"),
            ("ARM shorting cap", "SNT-100-BK-G", "Samtec", 1, "SUPPLY LOOSE - JP2 SHIPS OPEN", "Purchasing approval pending"),
            ("Optional UART link caps", "SNT-100-BK-G", "Samtec", 3, "OPTIONAL UART KIT ONLY - change all JP3-JP5 together, power off", "Not baseline; purchasing approval pending"),
            ("M2.5 screws", "USER-SUPPLIED/TBD", "TBD", 4, "Length/head clearance to suit approved standoff stack", "Mechanical approval pending; not an orderable MPN"),
            ("M2.5 standoffs", "USER-SUPPLIED/TBD", "TBD", 4, "Height/material to suit socket/USB/bench clearances", "Mechanical approval pending; not an orderable MPN"),
        ):
            writer.writerow(row)

    archive = OUT / "cipinkoklingacik-C4-bare-pcb.zip"
    files = sorted((OUT / "gerbers").glob("*"))
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, path.name)
        z.write(ROOT / "LICENSE", "LICENSE")
        z.write(ROOT / "LICENSE-MIT", "LICENSE-MIT")
        z.write(ROOT / "NOTICE.md", "NOTICE.md")
    artifacts = sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "manifest.json")
    manifest = {
        "revision": "C4", "purpose": "Engineering-prototype quote/review data; NOT production approval",
        "fabrication_release": False, "hardware_qualification": "NOT PERFORMED",
        "board_sha256": sha(HW / "cipinkoklingacik.kicad_pcb"),
        "schematic_sha256": sha(HW / "cipinkoklingacik.kicad_sch"),
        "project_sha256": sha(HW / "cipinkoklingacik.kicad_pro"),
        "drc_sha256": sha(HW / "cipinkoklingacik-drc.json"),
        "erc_sha256": sha(HW / "cipinkoklingacik-erc.rpt"),
        "pcb_status_sha256": sha(HW / "cipinkoklingacik-pcb-status.json"),
        "jlcpcb_snapshot_sha256": sha(SNAPSHOT),
        "baseline_smt_refs": sorted(r["Reference"] for r in smt),
        "baseline_hand_fit_refs": sorted(r["Reference"] for r in hand),
        "dnp_refs": sorted(r["Reference"] for r in rows if r["DNP"] == "yes"),
        "artifacts": {str(p.relative_to(OUT)): {"sha256": sha(p), "bytes": p.stat().st_size} for p in artifacts},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"C4 prototype data exported: {len(smt)} SMT parts, {len(hand)} hand-fit references. Supplier sign-off still required.")


if __name__ == "__main__":
    main()
