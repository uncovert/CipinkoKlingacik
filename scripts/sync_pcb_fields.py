#!/usr/bin/env python3
"""Synchronize explicitly selected component metadata, never PCB geometry/nets.

Requires an approved current board hash and matching footprint/path/pin nets.
Use after intentional generator-owned schematic field/value changes. Full
ERC/DRC, return-review refresh and exports are still mandatory afterwards.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pcbnew as p
from kicad_sexpr import loads, child, children

HW = Path(__file__).resolve().parent.parent / "hardware"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refs", nargs="+", required=True)
    parser.add_argument("--expected-board-sha256", required=True)
    args = parser.parse_args()
    path = HW / "cipinkoklingacik.kicad_pcb"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == args.expected_board_sha256
    board = p.LoadBoard(str(path))
    schematic = loads((HW / "cipinkoklingacik.kicad_sch").read_text())
    symbols = {next(v[2] for v in children(s, "property") if v[1] == "Reference"): s
               for s in children(schematic, "symbol")}
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    root = child(schematic, "uuid")[1]
    contract = json.loads((HW / "cipinkoklingacik-connectivity.json").read_text())
    for ref in args.refs:
        symbol, fp = symbols[ref], fps[ref]
        props = {v[1]: v[2] for v in children(symbol, "property")}
        assert fp.GetFPID().GetUniStringLibId() == props["Footprint"], "Footprint changes need explicit review"
        assert fp.GetPath().AsString() == f"/{root}/{child(symbol, 'uuid')[1]}", "Changed schematic association"
        assert fp.IsDNP() == (child(symbol, "dnp")[1] == "yes"), "Population changes need explicit review"
        pads = {pad.GetNumber(): pad for pad in fp.Pads() if pad.GetNumber()}
        assert set(pads) == set(contract[ref]), "Pin-set changes need explicit review"
        for number, expected in contract[ref].items():
            actual = pads[number].GetNetname().removeprefix("/")
            assert (actual == expected if expected is not None else actual.startswith("unconnected-")), "Net changes need explicit review"
        fp.SetValue(props["Value"])
        for key, value in props.items():
            if key not in ("Reference", "Value", "Footprint"):
                fp.SetField(key, value)
                fp.GetField(key).SetVisible(False)
    p.SaveBoard(str(path), board)
    print("Updated fields only:", ", ".join(args.refs), "- refresh strict checks and exports.")


if __name__ == "__main__":
    main()
