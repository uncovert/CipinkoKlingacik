#!/usr/bin/env python3
"""Render illustrative baseline PCBA views without editing design/manufacturing data.

Uses KiCad 10 Flatpak's installed 3D library and renderer, and Pillow for captions.
The Pico is a disclosed common-form-factor proxy, with illustrative socket height.
Temporary boards change model visibility only; they are never fabrication inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"
OUT = HW / "visuals"
MODEL_ROOT = "/app/extensions/Library/Packages3D/3dmodels"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(directory):
    import pcbnew as p

    board_path = HW / "cipinkoklingacik.kicad_pcb"
    before = sha(board_path)
    report = {"source_board_sha256": before, "source_project_sha256": sha(HW / "cipinkoklingacik.kicad_pro"),
              "population": "baseline only; JP2 ARM open", "hidden_dnp_refs": [],
              "modelled_fitted_refs": [], "unmodelled_fitted_refs": [], "models": {},
              "pico_model": "KiCad RaspberryPi_Pico_AddedHeaders_H2.54mm: form-factor proxy, NOT exact Pico 2",
              "illustrative_stack": "generic 8.50 mm sockets; module/header model offset 11.04 mm; mating height NOT approved",
              "limitations": ["Generic package models, not exact vendor cosmetics or approved envelopes",
                              "PCB colours/finish illustrative, not supplier selections",
                              "No mounting hardware/cables or ARM shorting cap shown",
                              "No physical clearance, USB fit or hardware qualification implied"]}
    for variant in ("assembled", "module-removed"):
        board = p.LoadBoard(str(board_path))
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            if fp.IsDNP():
                # SWIG exposes model values as copies: editing m_Show in a
                # Python loop does not reliably persist. Remove render-only
                # models, then verify the serialized temporary board below.
                fp.Models().clear()
                if variant == "assembled":
                    report["hidden_dnp_refs"].append(ref)
                continue
            if ref == "U1":
                fp.Models().clear()
                for name, z in (("RaspberryPi_Pico_PinSockets_H8.50mm.step", 0),
                                ("RaspberryPi_Pico_AddedHeaders_H2.54mm.step", 11.04)):
                    if variant == "module-removed" and z:
                        continue
                    model = p.FP_3DMODEL()
                    model.m_Filename = MODEL_ROOT + "/Module.3dshapes/" + name
                    model.m_Offset.x, model.m_Offset.y, model.m_Offset.z = 8.89, -24.13, z
                    model.m_Show = True
                    fp.Add3DModel(model)
            shown = [m for m in fp.Models() if m.m_Show]
            fp.Models().clear()
            for model in shown:
                resolved = Path(model.m_Filename.replace("${KICAD10_3DMODEL_DIR}", MODEL_ROOT))
                assert resolved.is_file(), f"Missing model for {ref}: {resolved}"
                report["models"][str(resolved.relative_to(MODEL_ROOT))] = sha(resolved)
                model.m_Filename = str(resolved)
                fp.Add3DModel(model)
            if variant == "assembled" and not ref.startswith(("TP", "H")):
                target = "modelled_fitted_refs" if shown else "unmodelled_fitted_refs"
                report[target].append(ref)
        output = directory / (variant + ".kicad_pcb")
        p.SaveBoard(str(output), board)
        # Verify the saved renderer input, not just the population log.
        saved = p.LoadBoard(str(output))
        for fp in saved.GetFootprints():
            if fp.IsDNP():
                assert not any(m.m_Show for m in fp.Models()), f"DNP model still visible: {fp.GetReference()}"
    assert sha(board_path) == before, "Authoritative PCB changed"
    assert not report["unmodelled_fitted_refs"], report["unmodelled_fitted_refs"]
    for key in ("hidden_dnp_refs", "modelled_fitted_refs"):
        report[key].sort()
    (directory / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")


def caption(raw, output, title, subtitle, footer):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.open(raw).convert("RGBA")
    # KiCad may round its framebuffer down to a tile boundary. Pad rather than
    # stretch the image so every delivered sheet has the same dimensions.
    w, h = 2400, 1950
    assert image.width <= w and image.height <= h
    canvas = Image.new("RGB", (w, h + 240), "#eef2f6")
    canvas.paste(image, ((w - image.width) // 2, 128 + (h - image.height) // 2), image)
    draw = ImageDraw.Draw(canvas)
    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    bold = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 42)
    normal = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 24)
    small = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 21)
    draw.text((70, 25), title, font=bold, fill="#152536")
    draw.text((72, 82), subtitle, font=normal, fill="#435469")
    draw.line((70, h + 155, w - 70, h + 155), fill="#c6ced7", width=2)
    draw.text((72, h + 172), footer, font=small, fill="#435469")
    draw.text((72, h + 204), "Illustrative CAD render • not a photograph or mechanical/production approval", font=small, fill="#435469")
    canvas.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.prepare:
        prepare(args.prepare)
        return
    OUT.mkdir(exist_ok=True)
    source_hash = sha(HW / "cipinkoklingacik.kicad_pcb")
    cli = ["flatpak", "run", "--command=kicad-cli", "org.kicad.KiCad"]
    with tempfile.TemporaryDirectory(prefix=".pcba-visuals-", dir=HW) as temp:
        directory = Path(temp)
        subprocess.run(["flatpak", "run", "--command=python3", "org.kicad.KiCad", str(Path(__file__).resolve()),
                        "--prepare", str(directory)], cwd=ROOT, check=True)
        report = json.loads((directory / "preparation.json").read_text())
        cases = (
            ("assembled", "isometric", ["--rotate", "325,0,25"], "ČipinkoKlingáčik C3 — assembled baseline",
             "100 × 85 mm carrier • socketed Pico-form-factor proxy • all baseline hand-fit parts shown"),
            ("assembled", "top", ["--side", "top"], "ČipinkoKlingáčik C3 — top view",
             "68 SMT parts + 7 hand-fit references • nine DNP options left empty • ARM open"),
            ("assembled", "bottom", ["--side", "bottom"], "ČipinkoKlingáčik C3 — underside",
             "Viewed from below (mirrored versus top) • through-hole tails shown • no bottom-side SMT"),
            ("module-removed", "module-removed", ["--rotate", "325,0,25"], "ČipinkoKlingáčik C3 — module removed",
             "Service view: two generic 1×20 sockets remain fitted • module unplugged, not a different BOM"),
        )
        for board_name, name, view, title, subtitle in cases:
            raw = directory / (name + ".png")
            log = directory / (name + ".log")
            with log.open("w") as stream:
                subprocess.run([*cli, "pcb", "render", str(directory / (board_name + ".kicad_pcb")),
                                "-o", str(raw), "--width", "2400", "--height", "1950",
                                "--quality", "high", "--background", "transparent", "--zoom", "0.82",
                                *view], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
            footer = ("Generic component models • Pico 2 internals not exact • socket/header mating height illustrative"
                      if name != "bottom" else "Bare pads for unpopulated options are intentional • mounting screws/standoffs not shown")
            output = OUT / ("cipinkoklingacik-C3-" + name + ".png")
            caption(raw, output, title, subtitle, footer)
            print("Rendered", output.relative_to(ROOT))
        report["renderer"] = "KiCad 10 pcb render, high-quality raytrace; Pillow captions"
    from PIL import Image
    # A convenient overview; full-resolution views remain separate.
    overview = Image.new("RGB", (2400, 2190), "#eef2f6")
    for index, name in enumerate(("isometric", "top", "module-removed", "bottom")):
        image = Image.open(OUT / ("cipinkoklingacik-C3-" + name + ".png"))
        image.thumbnail((1200, 1095))
        overview.paste(image, ((index % 2) * 1200, (index // 2) * 1095))
    overview.save(OUT / "cipinkoklingacik-C3-overview.png")
    pages = [Image.open(OUT / ("cipinkoklingacik-C3-" + name + ".png")).convert("RGB")
             for name in ("isometric", "top", "module-removed", "bottom")]
    pages[0].save(OUT / "cipinkoklingacik-C3-assembly-views.pdf", save_all=True, append_images=pages[1:], resolution=220)
    report["artifacts"] = {p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                           for p in sorted(OUT.iterdir()) if p.suffix in (".png", ".pdf")}
    assert source_hash == sha(HW / "cipinkoklingacik.kicad_pcb") == report["source_board_sha256"]
    baseline = json.loads((HW / "manufacturing/manifest.json").read_text())
    assert report["hidden_dnp_refs"] == baseline["dnp_refs"]
    assert set(report["modelled_fitted_refs"]) == set(baseline["baseline_smt_refs"] + baseline["baseline_hand_fit_refs"])
    (OUT / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Source PCB unchanged; model visibility matches the checked baseline population.")


if __name__ == "__main__":
    main()
