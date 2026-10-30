"""Checks against real KiCad exports, independent of kiutils and the generator."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kicad_sexpr import loads, child, children

HW = ROOT / "hardware"
DNP = {"U8", "C18", "JP3", "JP4", "JP5", "R20", "R31", "R40", "R41"}


class HardwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sch = loads((HW / "cipinkoklingacik.kicad_sch").read_text())
        cls.symbols = {next(p[2] for p in children(s, "property") if p[1] == "Reference"): s
                       for s in children(cls.sch, "symbol")}
        cls.libs = {s[1]: s for s in children(child(cls.sch, "lib_symbols"), "symbol")}
        cls.netlist = loads((HW / "cipinkoklingacik.net").read_text())
        cls.nets = {}
        cls.members = {}
        for net in children(child(cls.netlist, "nets"), "net"):
            # All labels are local to the root sheet; KiCad qualifies them with '/'.
            name = child(net, "name")[1].removeprefix("/")
            cls.members[name] = set()
            for node in children(net, "node"):
                pin = (child(node, "ref")[1], child(node, "pin")[1])
                if pin in cls.nets:
                    raise AssertionError(f"Pin in multiple nets: {pin}")
                cls.nets[pin] = name
                cls.members[name].add(pin)

    def net(self, ref, pin):
        return self.nets[(ref, str(pin))]

    def test_export_matches_complete_connectivity_contract(self):
        contract = json.loads((HW / "cipinkoklingacik-connectivity.json").read_text())
        self.assertEqual(set(contract), set(self.symbols))
        for ref, pins in contract.items():
            if ref.startswith("#"):
                continue  # ERC-only flags are intentionally absent from the physical netlist.
            for pin, expected in pins.items():
                with self.subTest(ref=ref, pin=pin):
                    actual = self.net(ref, pin)
                    if expected is None:
                        self.assertTrue(actual.startswith("unconnected-"), actual)
                        self.assertEqual(self.members[actual], {(ref, pin)})
                    else:
                        self.assertEqual(actual, expected)

    def test_critical_manufacturer_pinouts(self):
        expected = {
            "U2": ["AUX5", "GND", "U2P", "U2N", "U2O"],
            "U3": ["MY1", "GND", "MY0", "MZ", "MVCC", "MUX_S"],
            "U4": ["AUX5", "GND", "EN_H", None, "VH"],
            "U5": ["AUX5", "GND", "EN_L", None, "VL"],
            "U6": ["GND", "HOLD", "MVCC", None, None],
            "U7": [None, "TRIG_F", "GND", "TRIG_OUT", "3V3"],
            "Q1": ["Q1G", "GND", "GL"],
            "Q2": ["Q23G", "Q23S", "MZ"],
            "Q3": ["Q23G", "Q23S", "T_PRE"],
            "Q4": ["TGT_G", "GND", "Q4D"],
            "D1": ["RET", "AUX5"], "D2": ["GND", "LEDA"],
            "C4": ["VH", "GND"], "C7": ["VL", "GND"], "C9": ["HOLD", "GND"],
        }
        for ref, nets in expected.items():
            for pin, name in enumerate(nets, start=1):
                if name is not None:
                    self.assertEqual(self.net(ref, pin), name, f"{ref}.{pin}")

    def test_pico_full_socket_and_all_grounds(self):
        self.assertEqual({p[1] for p in children(self.symbols["U1"], "pin")},
                         {str(i) for i in range(1, 41)})
        for pin in (3, 8, 13, 18, 23, 28, 33, 38):
            self.assertEqual(self.net("U1", pin), "GND")
        for pin, net in {1: "UTX", 2: "URX", 4: "CB_PULSE", 5: "TRIG_OUT",
                         6: "TGT_ON", 7: "MUX_CMD", 9: "RST_ASSERT", 10: "LED",
                         11: "ARM_EN", 12: "UART_OE", 14: "REN", 36: "3V3", 40: "VBUS"}.items():
            self.assertEqual(self.net("U1", pin), net)

    def test_current_limit_and_crowbar_separation(self):
        for ref, a, b in (("R15", "VH", "MY0"), ("R16", "VL", "MY1")):
            self.assertEqual((self.net(ref, 1), self.net(ref, 2)), (a, b))
        self.assertEqual(self.members["MY0"], {("R15", "2"), ("U3", "3")})
        self.assertEqual(self.members["MY1"], {("R16", "2"), ("U3", "1")})
        self.assertEqual(self.members["GL"], {("Q1", "3"), ("J1", "1")})
        self.assertNotEqual(self.net("Q1", 3), self.net("J2", 1))

    def test_added_control_resistors(self):
        for ref, a, b in (("R8", "REN", "EN_H"), ("R35", "REN", "EN_L"),
                          ("R36", "MUX_CMD", "MUX_S"), ("R37", "MUX_S", "GND"),
                          ("R38", "Q4D", "Q23G")):
            self.assertEqual((self.net(ref, 1), self.net(ref, 2)), (a, b))

    def test_uart_isolation_and_fixed_directions(self):
        self.assertEqual((self.net("R40", 1), self.net("R40", 2)), ("UVCCB", "GND"))
        self.assertEqual((self.net("R41", 1), self.net("R41", 2)), ("UTX_T", "GND"))
        for ref in ("R6", "R34"):
            self.assertEqual((self.net(ref, 1), self.net(ref, 2)), ("UART_OE", "3V3"))
        self.assertEqual(self.net("C18", 1), self.net("U8", 15))
        self.assertNotEqual(self.net("C18", 1), self.net("J2", 1))
        for pin, net in {1: "3V3", 2: "GND", 3: "UTX", 4: "URX",
                         7: "GND", 8: "GND", 9: "UART_OE", 10: "GND",
                         11: "GND", 12: "GND", 13: "UTX_T", 14: "URX_T",
                         15: "UVCCB", 16: "3V3"}.items():
            self.assertEqual(self.net("U8", pin), net)

    def test_uart_bleeder_sinks_off_supply_current_budget(self):
        props = {p[1]: p[2] for p in children(self.symbols["R40"], "property")}
        self.assertEqual(props["MPN"], "RC0805FR-074K7L")
        self.assertTrue(props["Value"].endswith("k"))
        resistance = float(props["Value"][:-1]) * 1000
        # AXC4T774 ICCB: as much as 12 uA sourced out at VCCA=3.6, VCCB=0.
        # Use it as a near-zero sizing budget, not a measured I/V curve.
        self.assertLess(resistance * 1.01 * 12e-6, 0.1)
        self.assertLess(3.35 / (resistance * 0.99), 0.75e-3)

    def test_every_physical_pin_has_matching_local_footprint_pad(self):
        for ref, symbol in self.symbols.items():
            if ref.startswith("#"):
                continue
            with self.subTest(ref=ref):
                properties = {p[1]: p[2] for p in children(symbol, "property")}
                self.assertTrue(properties["MPN"])
                lib, name = properties["Footprint"].split(":")
                self.assertEqual(lib, "CipinkoKlingacik")
                fp = loads((HW / "CipinkoKlingacik.pretty" / (name + ".kicad_mod")).read_text())
                pads = {p[1] for p in children(fp, "pad") if p[1]}
                pins = {p[1] for p in children(symbol, "pin")}
                self.assertEqual(pads, pins)
                embedded = self.libs[child(symbol, "lib_id")[1]]
                libpins = {child(p, "number")[1] for unit in children(embedded, "symbol") for p in children(unit, "pin")}
                self.assertEqual(pins, libpins)

    def test_native_dnp_and_bom_variants(self):
        actual = {ref for ref, sym in self.symbols.items() if child(sym, "dnp")[1] == "yes"}
        self.assertEqual(actual, DNP)
        with (HW / "cipinkoklingacik-parts-all.csv").open() as stream:
            all_rows = {r["Reference"]: r for r in csv.DictReader(stream)}
        with (HW / "cipinkoklingacik-bom.csv").open() as stream:
            baseline = {r["Reference"]: r for r in csv.DictReader(stream)}
        self.assertEqual(set(all_rows), {r for r in self.symbols if not r.startswith("#")})
        self.assertEqual({r for r, p in all_rows.items() if p["DNP"] == "yes"}, DNP)
        self.assertEqual(set(baseline), set(all_rows) - DNP - {f"TP{i}" for i in range(1, 9)})
        self.assertTrue(all(p["MPN"] and p["Footprint"] for p in baseline.values()))

    def test_pinned_footprint_checksums(self):
        manifest = json.loads((HW / "vendor" / "footprints.json").read_text())
        for name, item in manifest.items():
            data = (HW / "CipinkoKlingacik.pretty" / (name + ".kicad_mod")).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])

    def test_pico_socket_geometry(self):
        fp = loads((HW / "CipinkoKlingacik.pretty" / "RaspberryPi_Pico_Common_THT.kicad_mod").read_text())
        pads = {p[1]: child(p, "at")[1:3] for p in children(fp, "pad")}
        for pin in range(1, 21):
            self.assertEqual([float(n) for n in pads[str(pin)]], [0, round((pin - 1) * 2.54, 2)])
        for pin in range(21, 41):
            self.assertEqual([float(n) for n in pads[str(pin)]], [17.78, round((40 - pin) * 2.54, 2)])

    def test_kelvin_force_and_sense_are_separate(self):
        self.assertNotIn("JP1", self.symbols)
        self.assertEqual((self.net("R39", 1), self.net("R39", 2)), ("T_PRE", "TVDD"))
        self.assertEqual(self.net("R20", 1), "T_PRE")
        self.assertEqual(self.net("R20", 4), "TVDD")
        self.assertEqual(self.members["ISENSE_P"], {("R20", "2"), ("TP7", "1")})
        self.assertEqual(self.members["ISENSE_N"], {("R20", "3"), ("TP8", "1")})
        self.assertNotEqual(self.net("R20", 1), self.net("R20", 2))
        self.assertNotEqual(self.net("R20", 3), self.net("R20", 4))


if __name__ == "__main__":
    unittest.main()
