"""Supplier-format/parity tests, not approval of reel rotation or procurement."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from export_jlcpcb import (SNAPSHOT, bom_rows, cpl_rows, export, unit_price,
                           planning_quantity, validate_supplier_identity)
from hardware_parts import JLCPCB_CODES
from kicad_sexpr import loads, children, child

OUT = ROOT / "hardware/manufacturing/assembly"


def csv_rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


class JLCPCBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts = csv_rows(OUT / "baseline-smt-bom.csv")
        cls.positions = csv_rows(OUT / "baseline-smt-pos.csv")

    def test_grouped_supplier_bom_exactly_covers_baseline(self):
        expected = {row["Reference"]: row for row in self.parts}
        seen = set()
        bom = csv_rows(OUT / "jlcpcb-bom.csv")
        self.assertEqual(bom, bom_rows(self.parts))
        self.assertEqual(len(bom), 24)
        for row in bom:
            for ref in row["Designator"].split(","):
                self.assertNotIn(ref, seen)
                seen.add(ref)
                self.assertEqual(row["Manufacturer Part Number"], expected[ref]["MPN"])
                self.assertEqual(row["LCSC Part #"], expected[ref]["LCSC"])
                self.assertEqual(row["LCSC Part #"], JLCPCB_CODES[expected[ref]["MPN"]])
                self.assertEqual(row["Footprint"], expected[ref]["Footprint"].split(":")[1])
        self.assertEqual(seen, set(expected))
        self.assertEqual(len(seen), 68)

    def test_supplier_cpl_preserves_gerber_origin_and_board_rotations(self):
        actual = csv_rows(OUT / "jlcpcb-cpl.csv")
        self.assertEqual(actual, cpl_rows(self.parts, self.positions))
        board = loads((ROOT / "hardware/cipinkoklingacik.kicad_pcb").read_text())
        fps = {next(p[2] for p in children(fp, "property") if p[1] == "Reference"): fp
               for fp in children(board, "footprint")}
        for row in actual:
            at = child(fps[row["Designator"]], "at")
            self.assertEqual(float(row["Mid X"]), float(at[1]))
            self.assertEqual(float(row["Mid Y"]), -float(at[2]))
            self.assertEqual(float(row["Rotation"]), float(at[3] if len(at) > 3 else 0) % 360)
            self.assertEqual(row["Layer"], "Top")
            self.assertLess(float(row["Mid Y"]), 0)  # no silent mirror/shift

    def test_export_refuses_unmapped_duplicate_dnp_or_mismatched_populations(self):
        missing = copy.deepcopy(self.parts)
        missing[0]["LCSC"] = ""
        with self.assertRaises(ValueError):
            bom_rows(missing)
        with self.assertRaises(ValueError):
            bom_rows(self.parts + [self.parts[0]])
        dnp = copy.deepcopy(self.parts)
        dnp[0]["DNP"] = "yes"
        with self.assertRaises(ValueError):
            bom_rows(dnp)
        with self.assertRaises(ValueError):
            cpl_rows(self.parts, self.positions[:-1])
        with self.assertRaises(ValueError):
            cpl_rows(self.parts, self.positions + [self.positions[0]])
        bottom = copy.deepcopy(self.positions)
        bottom[0]["Side"] = "bottom"
        with self.assertRaises(ValueError):
            cpl_rows(self.parts, bottom)

    def test_regeneration_is_offline_deterministic_and_snapshot_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            export(self.parts, self.positions, target)
            for name in ("jlcpcb-bom.csv", "jlcpcb-cpl.csv", "jlcpcb-sourcing.csv", "jlcpcb-cost-estimate.json"):
                self.assertEqual((OUT / name).read_bytes(), (target / name).read_bytes(), name)
        manifest = json.loads((OUT.parent / "manifest.json").read_text())
        self.assertEqual(manifest["jlcpcb_snapshot_sha256"], hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest())

    def test_hashed_csv_files_use_git_compatible_lf_line_endings(self):
        # .gitattributes enforces LF. Hashes must survive a fresh git checkout,
        # not just pass against CRLF working-tree files from csv.writer.
        for path in OUT.glob("*.csv"):
            self.assertNotIn(b"\r", path.read_bytes(), path.name)

    def test_cost_counts_boards_joints_and_feeders_separately(self):
        report = json.loads((OUT / "jlcpcb-cost-estimate.json").read_text())
        self.assertEqual(report["smt_solder_joints_per_board"], 161)
        self.assertEqual(report["baseline_smt_placements"], 68)
        self.assertEqual(report["unique_skus"], 24)
        self.assertEqual(report["paid_extended_skus"], 15)
        self.assertAlmostEqual(report["economic_feeder_total_USD"], 15 * 3.07)
        stock = {row["lcsc"]: row for row in json.loads(SNAPSHOT.read_text())["parts"]}
        terms = json.loads(SNAPSHOT.read_text())["assembly_terms"]["parts"]
        quantities = {}
        for row in self.parts:
            quantities[row["LCSC"]] = quantities.get(row["LCSC"], 0) + 1
        for estimate in report["estimates"]:
            count = estimate["assembled_boards"]
            self.assertAlmostEqual(estimate["smt_joint_charge_USD"], count * 161 * 0.0016)
            self.assertAlmostEqual(estimate["additional_pre_reflow_USD_if_applied"], count * 161 * 0.016)
            component_cost = sum(q * count * unit_price(stock[code], q * count) for code, q in quantities.items())
            self.assertAlmostEqual(estimate["components_USD_excluding_attrition"], component_cost)
            self.assertAlmostEqual(estimate["subtotal_USD"], component_cost + count * 161 * 0.0016 + 8.18 + 1.53 + 0.45 + 15 * 3.07)
            self.assertEqual(estimate["snapshot_stock_shortfalls_before_attrition"], [])
            allowance_cost = 0
            for code, q in quantities.items():
                required = max(q * count + terms[code]["lossNumber"],
                               terms[code]["leastNumber"], stock[code]["min_purchase"])
                allowance_cost += required * unit_price(stock[code], required)
            self.assertAlmostEqual(estimate["quantity_allowance_components_USD"], allowance_cost, places=4)
            self.assertAlmostEqual(estimate["quantity_allowance_subtotal_USD"],
                                   allowance_cost + count * 161 * 0.0016 + 56.21, places=4)
            self.assertEqual(estimate["snapshot_stock_shortfalls_with_quantity_allowance"], [])

    def test_procurement_allowance_adds_loss_before_minimum(self):
        terms = {"leastNumber": 20, "lossNumber": 6, "leastNumberPrice": 0.336}
        self.assertEqual(planning_quantity(2, terms), 20)  # Not 20 + 6.
        self.assertEqual(planning_quantity(18, terms), 24)
        self.assertEqual(planning_quantity(2, terms, 30), 30)
        with self.assertRaises(ValueError):
            planning_quantity(0, terms)
        self.assertEqual(planning_quantity(2, {**terms, "leastNumberPrice": 100}), 20)

    def test_supplier_manufacturer_and_package_are_not_fuzzy_matches(self):
        stock = {row["lcsc"]: row for row in json.loads(SNAPSHOT.read_text())["parts"]}
        for row in bom_rows(self.parts):
            item = stock[row["LCSC Part #"]]
            validate_supplier_identity(row, item)
            for field in ("mpn", "manufacturer", "package"):
                bad = {**item, field: "Unreviewed lookalike"}
                with self.assertRaises(ValueError, msg=field):
                    validate_supplier_identity(row, bad)

    def test_quality_sourcing_substitutions_and_retained_sensitive_parts(self):
        parts = {row["Reference"]: row for row in self.parts}
        for ref, mpn in {"F1": "1206L025YR", "R15": "RC2512FK-7W15RL",
                         "R16": "RC2512FK-7W15RL", "Q2": "Si2377EDS-T1-GE3",
                         "Q3": "Si2377EDS-T1-GE3", "Q4": "2N7002,215",
                         "D1": "BAT54WS-7-F", "C9": "EEE-FK1C101P",
                         "U6": "TPS7A2036PDBVR"}.items():
            self.assertEqual(parts[ref]["MPN"], mpn)
        audit = csv_rows(OUT / "jlcpcb-sourcing.csv")
        self.assertEqual(sum(row["Library_type"] == "Basic" for row in audit), 9)
        self.assertFalse([row for row in audit if "OUT OF STOCK" in row["Warning"]])
        for row in audit:
            self.assertGreaterEqual(int(row["Stock_at_snapshot"]), 10 * int(row["Quantity_per_board"]))
            self.assertEqual(int(row["Catalog_minPurchaseNum"]), 1)
            self.assertGreaterEqual(int(row["Assembly_leastNumber"]), 1)
            self.assertGreaterEqual(int(row["Assembly_lossNumber"]), 0)
        self.assertEqual(parts["R15"]["Value"], "15 1% 2W")
        self.assertEqual(parts["D1"]["Datasheet"], "https://www.diodes.com/assets/Datasheets/BAT54WS.pdf")


if __name__ == "__main__":
    unittest.main()
