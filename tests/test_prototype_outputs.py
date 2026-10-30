"""Verify the exported engineering-prototype package against the actual board."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import re
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"
OUT = HW / "manufacturing"
sys.path.insert(0, str(ROOT / "scripts"))
from kicad_sexpr import loads, children, child
from pcb_geometry import footprint_pads


class PrototypeOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((OUT / "manifest.json").read_text())
        cls.board = loads((HW / "cipinkoklingacik.kicad_pcb").read_text())
        cls.fps = {next(v[2] for v in children(fp, "property") if v[1] == "Reference"): fp
                   for fp in children(cls.board, "footprint")}

    def test_package_hashes_match_sources_and_every_artifact(self):
        for key, name in (("board_sha256", "cipinkoklingacik.kicad_pcb"),
                          ("schematic_sha256", "cipinkoklingacik.kicad_sch"),
                          ("project_sha256", "cipinkoklingacik.kicad_pro"),
                          ("drc_sha256", "cipinkoklingacik-drc.json"),
                          ("erc_sha256", "cipinkoklingacik-erc.rpt"),
                          ("pcb_status_sha256", "cipinkoklingacik-pcb-status.json")):
            self.assertEqual(self.manifest[key], hashlib.sha256((HW / name).read_bytes()).hexdigest())
        for name, item in self.manifest["artifacts"].items():
            data = (OUT / name).read_bytes()
            self.assertEqual(len(data), item["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"], name)
        self.assertFalse(self.manifest["fabrication_release"])
        self.assertEqual(self.manifest["hardware_qualification"], "NOT PERFORMED")

    def test_baseline_bom_positions_and_hand_fit_are_consistent(self):
        with (OUT / "assembly" / "baseline-smt-bom.csv").open() as stream:
            bom = {r["Reference"]: r for r in csv.DictReader(stream)}
        with (OUT / "assembly" / "baseline-smt-pos.csv").open() as stream:
            positions = {r["Ref"]: r for r in csv.DictReader(stream)}
        with (OUT / "assembly" / "baseline-hand-fit.csv").open() as stream:
            hand = {r["Reference"]: r for r in csv.DictReader(stream)}
        self.assertEqual(set(bom), set(positions))
        self.assertEqual(set(bom), set(self.manifest["baseline_smt_refs"]))
        self.assertEqual(set(hand), set(self.manifest["baseline_hand_fit_refs"]))
        self.assertFalse(set(bom) & set(hand))
        self.assertFalse((set(bom) | set(hand)) & set(self.manifest["dnp_refs"]))
        self.assertEqual(len(bom), 68)
        self.assertEqual(len(hand), 7)
        self.assertIn("R39", bom)
        self.assertNotIn("R20", bom)

    def test_positions_and_rotations_match_board_coordinate_convention(self):
        with (OUT / "assembly" / "baseline-smt-pos.csv").open() as stream:
            for row in csv.DictReader(stream):
                fp = self.fps[row["Ref"]]
                at = child(fp, "at")
                self.assertAlmostEqual(float(row["PosX"]), float(at[1]), places=5)
                self.assertAlmostEqual(float(row["PosY"]), -float(at[2]), places=5)
                self.assertAlmostEqual(float(row["Rot"]) % 360, float(at[3] if len(at) > 3 else 0) % 360, places=5)
                self.assertEqual(row["Side"], "top")
                self.assertEqual(row["Package"], fp[1].split(":", 1)[1])

    def test_baseline_stencil_contains_only_fitted_smt_parts(self):
        text = (OUT / "stencil" / "cipinkoklingacik-F_Paste.gtp").read_text()
        refs = set(re.findall(r"%TO\.C,([^*]+)\*%", text))
        self.assertEqual(refs, set(self.manifest["baseline_smt_refs"]))
        self.assertFalse(refs & set(self.manifest["dnp_refs"]))
        self.assertIn("%MOMM*%", text)
        self.assertTrue(text.rstrip().endswith("M02*"))

    def test_baseline_paste_flash_centres_match_every_selected_pad(self):
        expected = {}
        pads = footprint_pads(self.board)
        for ref in self.manifest["baseline_smt_refs"]:
            expected[ref] = Counter((round(x, 6), round(-y, 6))
                                    for (name, _), ((x, y), _) in pads.items() if name == ref)
        actual = {}
        ref = None
        for line in (OUT / "stencil/cipinkoklingacik-F_Paste.gtp").read_text().splitlines():
            attr = re.fullmatch(r"%TO\.C,([^*]+)\*%", line)
            if attr:
                ref = attr[1]
            flash = re.fullmatch(r"X(-?\d+)Y(-?\d+)D03\*", line)
            if flash:
                self.assertIsNotNone(ref)
                actual.setdefault(ref, Counter())[(int(flash[1]) / 1e6, int(flash[2]) / 1e6)] += 1
        self.assertEqual(actual, expected)

    def test_drill_inventory_matches_board_and_separates_npth(self):
        pth, npth = 0, 0
        for fp in self.fps.values():
            for pad in children(fp, "pad"):
                if pad[2] == "thru_hole":
                    pth += 1
                elif pad[2] == "np_thru_hole":
                    npth += 1
        pth += len(children(self.board, "via"))
        plated = (OUT / "gerbers" / "cipinkoklingacik-PTH.drl").read_text()
        unplated = (OUT / "gerbers" / "cipinkoklingacik-NPTH.drl").read_text()
        self.assertEqual(len(re.findall(r"^X[-\d.]+Y[-\d.]+", plated, re.M)), pth)
        self.assertEqual(len(re.findall(r"^X[-\d.]+Y[-\d.]+", unplated, re.M)), npth)
        self.assertEqual(npth, 4)
        self.assertIn("C0.300", plated)
        self.assertIn("C2.700", unplated)

    def test_drilled_hole_coordinates_match_the_actual_board(self):
        for kind, filename in (("thru_hole", "PTH"), ("np_thru_hole", "NPTH")):
            expected = []
            for ref, fp in self.fps.items():
                for pad in children(fp, "pad"):
                    if pad[2] != kind:
                        continue
                    at = child(fp, "at")
                    angle = math.radians(float(at[3]) if len(at) > 3 else 0)
                    x, y = map(float, child(pad, "at")[1:3])
                    point = (float(at[1]) + x * math.cos(angle) + y * math.sin(angle),
                             float(at[2]) - x * math.sin(angle) + y * math.cos(angle))
                    expected.append(point)
            if kind == "thru_hole":
                expected.extend(tuple(map(float, child(v, "at")[1:3])) for v in children(self.board, "via"))
            text = (OUT / f"gerbers/cipinkoklingacik-{filename}.drl").read_text()
            actual = [(float(x), -float(y)) for x, y in re.findall(r"^X([-\d.]+)Y([-\d.]+)", text, re.M)]
            self.assertEqual(len(expected), len(actual))
            for point in expected:
                closest = min(actual, key=lambda p: math.dist(point, p))
                self.assertLessEqual(math.dist(point, closest), 0.0015)  # Excellon has 0.001 mm resolution.
                actual.remove(closest)
            self.assertEqual(actual, [])

    def test_bare_pcb_archive_and_outline(self):
        expected = {p.name: p.read_bytes() for p in (OUT / "gerbers").glob("*") if p.is_file()}
        expected["LICENSE"] = (ROOT / "LICENSE").read_bytes()
        expected["LICENSE-MIT"] = (ROOT / "LICENSE-MIT").read_bytes()
        expected["NOTICE.md"] = (ROOT / "NOTICE.md").read_bytes()
        with zipfile.ZipFile(OUT / "cipinkoklingacik-C4-bare-pcb.zip") as z:
            self.assertEqual(set(z.namelist()), set(expected))
            for name, data in expected.items():
                self.assertEqual(z.read(name), data)
        self.assertFalse(any("Paste" in name for name in expected))
        profile = (OUT / "gerbers" / "cipinkoklingacik-Edge_Cuts.gm1").read_text()
        self.assertIn("%FSLAX46Y46*%", profile)
        points = {(int(x), int(y)) for x, y in re.findall(r"X(-?\d+)Y(-?\d+)D0[12]\*", profile)}
        self.assertEqual(points, {(0, 0), (100_000_000, 0), (100_000_000, -85_000_000), (0, -85_000_000)})


if __name__ == "__main__":
    unittest.main()
