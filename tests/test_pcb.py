"""Dependency-free checks of the placed board and its real KiCad DRC report."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"
sys.path.insert(0, str(ROOT / "scripts"))
from kicad_sexpr import child, children, loads
from pcb_geometry import track_path_mm


def properties(node):
    return {f[1]: f[2] for f in children(node, "property")}


class PCBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = loads((HW / "cipinkoklingacik.kicad_pcb").read_text())
        cls.fps = {properties(fp)["Reference"]: fp for fp in children(cls.board, "footprint")}
        cls.sch = loads((HW / "cipinkoklingacik.kicad_sch").read_text())
        cls.syms = {properties(s)["Reference"]: s for s in children(cls.sch, "symbol") if not properties(s)["Reference"].startswith("#")}
        cls.contract = json.loads((HW / "cipinkoklingacik-connectivity.json").read_text())
        cls.drc = json.loads((HW / "cipinkoklingacik-drc.json").read_text())
        cls.status = json.loads((HW / "cipinkoklingacik-pcb-status.json").read_text())

    def test_all_components_paths_fields_and_pads_match_schematic(self):
        self.assertEqual(set(self.fps), set(self.syms) | {"H1", "H2", "H3", "H4"})
        root = child(self.sch, "uuid")[1]
        for ref, sym in self.syms.items():
            with self.subTest(ref=ref):
                fp = self.fps[ref]
                self.assertEqual(fp[1], properties(sym)["Footprint"])
                self.assertEqual(child(fp, "path")[1], f"/{root}/{child(sym, 'uuid')[1]}")
                for key in ("MPN", "Manufacturer", "Requirement", "Assembly", "Datasheet", "Value"):
                    self.assertEqual(properties(fp)[key], properties(sym)[key])
                pads = {p[1]: p for p in children(fp, "pad") if p[1]}
                self.assertEqual(set(pads), set(self.contract[ref]))
                for pin, net in self.contract[ref].items():
                    actual = child(pads[pin], "net")[-1].removeprefix("/")
                    if net is None:
                        self.assertTrue(actual.startswith("unconnected-"), actual)
                    else:
                        self.assertEqual(actual, net)

    def test_dnp_and_non_smt_placement_exclusions(self):
        for ref, sym in self.syms.items():
            fp = self.fps[ref]
            attrs = child(fp, "attr")
            dnp = child(sym, "dnp")[1] == "yes"
            self.assertEqual("dnp" in attrs, dnp)
            assembly = properties(sym)["Assembly"]
            self.assertEqual("exclude_from_pos_files" in attrs, dnp or assembly != "SMT")
        self.assertIn("dnp", child(self.fps["R20"], "attr"))
        self.assertNotIn("dnp", child(self.fps["R39"], "attr"))

    def test_mechanical_outline_thickness_and_mounts(self):
        self.assertEqual(child(child(self.board, "general"), "thickness")[1], "1.6")
        copper = [layer for layer in child(self.board, "layers")[1:] if isinstance(layer, list) and layer[2] == "signal"]
        self.assertEqual({layer[1] for layer in copper}, {"F.Cu", "B.Cu"})
        edge = [line for line in children(self.board, "gr_line") if child(line, "layer")[1] == "Edge.Cuts"]
        segments = {(tuple(child(line, "start")[1:3]), tuple(child(line, "end")[1:3])) for line in edge}
        self.assertEqual(segments, {
            (("0", "0"), ("100", "0")), (("100", "0"), ("100", "85")),
            (("100", "85"), ("0", "85")), (("0", "85"), ("0", "0"))})
        for ref in ("H1", "H2", "H3", "H4"):
            attrs = child(self.fps[ref], "attr")
            self.assertTrue({"board_only", "exclude_from_pos_files", "exclude_from_bom"}.issubset(attrs))
            mounting_pad = child(self.fps[ref], "pad")
            self.assertEqual(mounting_pad[2], "np_thru_hole")
            self.assertEqual(child(mounting_pad, "drill")[1], "2.7")

    def test_filled_ground_plane_and_critical_route_inventory(self):
        zones = children(self.board, "zone")
        for layer in ("F.Cu", "B.Cu"):
            self.assertTrue(any(child(z, "net")[-1] == "/GND" and
                                child(z, "layer")[1] == layer and children(z, "filled_polygon") for z in zones))
        segments = children(self.board, "segment")
        self.assertTrue(any(child(s, "net")[-1] == "/GL" and float(child(s, "width")[1]) >= 1 for s in segments))
        for net in ("/ISENSE_P", "/ISENSE_N", "/Q1G", "/U2O", "/VH", "/VL", "/HOLD"):
            self.assertTrue(any(child(s, "net")[-1] == net for s in segments), net)
        for net in ("/GL", "/Q1G", "/U2O", "/ISENSE_P", "/ISENSE_N"):
            self.assertTrue(all(child(s, "layer")[1] == "F.Cu" for s in segments if child(s, "net")[-1] == net))
        via_nets = {child(v, "net")[-1] for v in children(self.board, "via")}
        self.assertFalse(via_nets & {"/GL", "/Q1G", "/U2O", "/ISENSE_P", "/ISENSE_N"})
        self.assertTrue(all(float(child(s, "width")[1]) >= 0.4 for s in segments if child(s, "net")[-1] == "/Q23S"))

    def test_current_drc_report_is_honest_and_has_no_exclusions(self):
        self.assertEqual(self.drc["violations"], [])
        self.assertEqual(self.drc["schematic_parity"], [])
        self.assertEqual(self.drc["unconnected_items"], [])
        self.assertEqual(self.drc["ignored_checks"], [])
        self.assertEqual(len(self.drc["unconnected_items"]), self.status["unconnected_items"])
        self.assertEqual(self.status["routing_complete"], not bool(self.drc["unconnected_items"]))
        self.assertFalse(self.status["fabrication_release"])
        for key, file in (("board_sha256", "cipinkoklingacik.kicad_pcb"),
                          ("schematic_sha256", "cipinkoklingacik.kicad_sch"),
                          ("project_sha256", "cipinkoklingacik.kicad_pro"),
                          ("drc_sha256", "cipinkoklingacik-drc.json")):
            self.assertEqual(self.status[key], hashlib.sha256((HW / file).read_bytes()).hexdigest())
        project = json.loads((HW / "cipinkoklingacik.kicad_pro").read_text())
        settings = project["board"]["design_settings"]
        self.assertEqual(settings["drc_exclusions"], [])
        self.assertEqual(settings["rule_severities"]["unconnected_items"], "error")
        self.assertEqual(settings["rule_severities"]["courtyards_overlap"], "error")
        for name in ("missing_courtyard", "track_not_centered_on_via",
                     "tuning_profile_track_geometries", "footprint_filters_mismatch",
                     "footprint_type_mismatch"):
            self.assertEqual(settings["rule_severities"][name], "error", name)
        self.assertFalse([name for name, severity in settings["rule_severities"].items()
                          if severity == "ignore"], "No unreviewed DRC suppression is allowed")

    def test_signal_transitions_have_local_ground_returns(self):
        import math
        vias = children(self.board, "via")
        ground = [tuple(map(float, child(v, "at")[1:3])) for v in vias if child(v, "net")[-1] == "/GND"]
        signal = [v for v in vias if child(v, "net")[-1] != "/GND"]
        self.assertTrue(signal)
        for via in signal:
            point = tuple(map(float, child(via, "at")[1:3]))
            self.assertLessEqual(min(math.dist(point, g) for g in ground), 2.01,
                                 f"No local reference stitching near {child(via, 'net')[-1]} at {point}")
        review = json.loads((HW / "cipinkoklingacik-return-review.json").read_text())
        self.assertEqual(len(review["signal_transitions"]), len(signal))
        self.assertEqual(review["board_sha256"], hashlib.sha256((HW / "cipinkoklingacik.kicad_pcb").read_bytes()).hexdigest())

    def test_no_duplicate_board_uuids(self):
        ids = []

        def visit(node):
            if isinstance(node, list):
                if node and node[0] == "uuid":
                    ids.append(node[1])
                for item in node:
                    if isinstance(item, list):
                        visit(item)
        visit(self.board)
        self.assertEqual(len(ids), len(set(ids)))

    def test_reviewed_bypass_routes_remain_local(self):
        for start, end, maximum in (
            (("U4", "5"), ("C5", "1"), 4.0),
            (("U5", "5"), ("C8", "1"), 4.0),
            (("U6", "2"), ("C10", "1"), 3.1),
            (("U6", "3"), ("C11", "1"), 4.0),
            (("U2", "1"), ("C13", "1"), 2.3),
        ):
            self.assertLessEqual(track_path_mm(self.board, start, end), maximum, (start, end))

    def test_connector_function_labels_are_present(self):
        texts = {item[1] for item in children(self.board, "gr_text")}
        self.assertTrue({"TRIG IN (3V3)", "RESET OD", "NOT VDD", "1=GND", "2=TGT RX", "3=TGT TX"} <= texts)


if __name__ == "__main__":
    unittest.main()
