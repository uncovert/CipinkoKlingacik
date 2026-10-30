"""Synthetic checks for the geometric bypass verifier, independent of PCB data."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from pcb_geometry import footprint_pads, track_path_mm


def footprint(ref, x, y, angle=0, pad_x=0, pad_y=0, net="/SUPPLY"):
    return ["footprint", "Test", ["property", "Reference", ref],
            ["at", x, y, angle],
            ["pad", "1", "smd", "rect", ["at", pad_x, pad_y], ["net", net]]]


def segment(a, b, layer="F.Cu", net="/SUPPLY"):
    return ["segment", ["start", *a], ["end", *b], ["layer", layer], ["net", net]]


class GeometryVerifierTests(unittest.TestCase):
    def test_kicad_rotation_uses_board_downward_y(self):
        board = ["kicad_pcb", footprint("C1", 10, 20, angle=90, pad_x=2, pad_y=1),
                 footprint("C2", 10, 20, angle=270, pad_x=2, pad_y=1)]
        pads = footprint_pads(board)
        self.assertEqual(pads[("C1", "1")][0], (11, 18))
        self.assertEqual(pads[("C2", "1")][0], (9, 22))

    def test_same_net_branch_splits_a_long_unsplit_track(self):
        board = ["kicad_pcb", footprint("U1", 0, 0), footprint("C1", 3, 2),
                 segment((0, 0), (5, 0)), segment((3, 0), (3, 2))]
        self.assertAlmostEqual(track_path_mm(board, ("U1", "1"), ("C1", "1")), 5)

    def test_layers_only_join_at_actual_vias(self):
        board = ["kicad_pcb", footprint("U1", 0, 0), footprint("C1", 4, 0),
                 segment((0, 0), (1, 0)), segment((1, 0), (3, 0), "B.Cu"),
                 segment((3, 0), (4, 0))]
        with self.assertRaisesRegex(ValueError, "No explicit track-centre path"):
            track_path_mm(board, ("U1", "1"), ("C1", "1"))
        for x in (1, 3):
            board.append(["via", ["at", x, 0], ["net", "/SUPPLY"]])
        self.assertAlmostEqual(track_path_mm(board, ("U1", "1"), ("C1", "1")), 4)

    def test_different_net_geometry_cannot_create_a_shortcut(self):
        board = ["kicad_pcb", footprint("U1", 0, 0), footprint("C1", 4, 0),
                 segment((0, 0), (0, 2)), segment((0, 2), (4, 2)),
                 segment((4, 2), (4, 0)), segment((0, 0), (4, 0), net="/OTHER")]
        self.assertAlmostEqual(track_path_mm(board, ("U1", "1"), ("C1", "1")), 8)
        board[2] = footprint("C1", 4, 0, net="/OTHER")
        with self.assertRaisesRegex(ValueError, "Different nets"):
            track_path_mm(board, ("U1", "1"), ("C1", "1"))

    def test_no_zone_or_pad_spreading_path_is_invented(self):
        board = ["kicad_pcb", footprint("U1", 0, 0), footprint("C1", 4, 0.1),
                 segment((0, 0), (4, 0))]
        with self.assertRaisesRegex(ValueError, "No explicit track-centre path"):
            track_path_mm(board, ("U1", "1"), ("C1", "1"))


if __name__ == "__main__":
    unittest.main()
