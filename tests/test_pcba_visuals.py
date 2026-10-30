"""Check render freshness/population, not mechanical fit or image realism."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

HW = Path(__file__).resolve().parent.parent / "hardware"
VIEWS = HW / "visuals"


class PCBVisualTests(unittest.TestCase):
    def test_render_source_and_artifact_hashes(self):
        manifest = json.loads((VIEWS / "manifest.json").read_text())
        for key, filename in (("source_board_sha256", "cipinkoklingacik.kicad_pcb"),
                              ("source_project_sha256", "cipinkoklingacik.kicad_pro")):
            self.assertEqual(manifest[key], hashlib.sha256((HW / filename).read_bytes()).hexdigest())
        expected = {f"cipinkoklingacik-C4-{name}.png" for name in
                    ("isometric", "top", "bottom", "module-removed", "overview")}
        expected.add("cipinkoklingacik-C4-assembly-views.pdf")
        self.assertEqual(set(manifest["artifacts"]), expected)
        for name, item in manifest["artifacts"].items():
            data = (VIEWS / name).read_bytes()
            self.assertEqual(item["sha256"], hashlib.sha256(data).hexdigest(), name)
            self.assertEqual(item["bytes"], len(data))
            if name.endswith(".png"):
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", data[16:24]), (2400, 2190))
            else:
                self.assertTrue(data.startswith(b"%PDF"))

    def test_visual_population_and_proxy_limits_are_explicit(self):
        manifest = json.loads((VIEWS / "manifest.json").read_text())
        baseline = json.loads((HW / "manufacturing" / "manifest.json").read_text())
        self.assertEqual(manifest["hidden_dnp_refs"], baseline["dnp_refs"])
        self.assertEqual(set(manifest["modelled_fitted_refs"]),
                         set(baseline["baseline_smt_refs"] + baseline["baseline_hand_fit_refs"]))
        self.assertEqual(manifest["unmodelled_fitted_refs"], [])
        self.assertIn("JP2 ARM open", manifest["population"])
        self.assertIn("NOT exact Pico 2", manifest["pico_model"])
        self.assertIn("NOT approved", manifest["illustrative_stack"])
        self.assertIn("No physical clearance, USB fit or hardware qualification implied", manifest["limitations"])


if __name__ == "__main__":
    unittest.main()
