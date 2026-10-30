"""GitHub-release hygiene and identity checks; not physical qualification."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from package_release import verify_repository, release_files
from kicad_sexpr import loads, child, children


class ReleaseTests(unittest.TestCase):
    def test_release_sources_links_licences_and_hashes(self):
        version, files = verify_repository()
        self.assertEqual(version, (ROOT / "VERSION").read_text().strip())
        self.assertTrue(files)
        self.assertIn(ROOT / ".github/workflows/checks.yml", files)

    def test_public_identity_and_project_mapping(self):
        board = loads((ROOT / "hardware/cipinkoklingacik.kicad_pcb").read_text())
        self.assertIn("ČipinkoKlingáčik C4", {text[1] for text in children(board, "gr_text")})
        sch = loads((ROOT / "hardware/cipinkoklingacik.kicad_sch").read_text())
        self.assertIn("ČipinkoKlingáčik", child(child(sch, "title_block"), "title")[1])
        self.assertEqual(child(child(board, "title_block"), "rev")[1], "C4")
        self.assertEqual(child(child(sch, "title_block"), "rev")[1], "C4")
        self.assertTrue(all(fp[1].startswith("CipinkoKlingacik:") for fp in children(board, "footprint")))

    def test_obsolete_attempts_and_local_state_are_not_release_sources(self):
        names = {p.relative_to(ROOT).as_posix() for p in release_files()}
        self.assertFalse(any("__pycache__" in n or "audit-sources/" in n or n.endswith(".kicad_prl") for n in names))
        for script in ("generate_pcb.py", "generate_draft_schematic.py", "polish_pcb.py",
                       "apply_c3_review_layout.py", "add_c3_uart_defaults.py", "refine_power_routes.py"):
            self.assertFalse((ROOT / "scripts" / script).exists(), script)


if __name__ == "__main__":
    unittest.main()
