#!/usr/bin/env python3
"""Create a temporary paste-only variant; never edits the authoritative PCB."""
import argparse
from pathlib import Path
import pcbnew as p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "Use a fresh temporary stencil board path"
    root = Path(__file__).resolve().parent.parent
    board = p.LoadBoard(str(root / "hardware" / "cipinkoklingacik.kicad_pcb"))
    excluded = []
    for fp in board.GetFootprints():
        if fp.IsDNP():
            excluded.append(fp.GetReference())
            for pad in fp.Pads():
                layers = pad.GetLayerSet()
                layers.RemoveLayer(p.F_Paste)
                layers.RemoveLayer(p.B_Paste)
                pad.SetLayerSet(layers)
    p.SaveBoard(str(args.output), board)
    print("Baseline stencil omits DNP paste:", ", ".join(sorted(excluded)))


if __name__ == "__main__":
    main()
