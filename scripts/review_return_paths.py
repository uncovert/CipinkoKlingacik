#!/usr/bin/env python3
"""Add local ground stitching at routed layer transitions and record geometry.

Run with KiCad Python. Conservative pad/track collision screening is followed
by mandatory full KiCad DRC; this is not an electromagnetic simulation.
"""
import hashlib
import json
import math
from pathlib import Path

import pcbnew as p

ROOT = Path(__file__).resolve().parent.parent
HW = ROOT / "hardware"


def xy(v):
    return p.ToMM(v.x), p.ToMM(v.y)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def segment_distance(q, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = max(0, min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / length2)) if length2 else 0
    return distance(q, (a[0] + t * dx, a[1] + t * dy))


def main():
    path = HW / "cipinkoklingacik.kicad_pcb"
    status = json.loads((HW / "cipinkoklingacik-pcb-status.json").read_text())
    previous_path = HW / "cipinkoklingacik-return-review.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    assert hashlib.sha256(path.read_bytes()).hexdigest() == status["board_sha256"], "Refresh DRC first"
    assert status["geometry_violations"] == status["unconnected_items"] == status["schematic_parity_issues"] == 0
    board = p.LoadBoard(str(path))
    tracks = list(board.GetTracks())
    ground_vias = [xy(t.GetPosition()) for t in tracks if type(t) is p.PCB_VIA and t.GetNetname() == "/GND"]
    signal_vias = [t for t in tracks if type(t) is p.PCB_VIA and t.GetNetname() != "/GND"]
    pads = [pad for fp in board.GetFootprints() for pad in fp.Pads()]
    ground = next(pad.GetNet() for pad in pads if pad.GetNetname() == "/GND")
    added, transitions = [], []

    def available(q):
        if not (0.85 <= q[0] <= 99.15 and 0.85 <= q[1] <= 84.15):
            return False
        # Preserve the library's common Pico/W antenna keepout even on Pico 2.
        if 11.3 < q[0] < 26.5 and 43.8 < q[1] < 54:
            return False
        for hx, hy in ((4, 4), (96, 4), (4, 81), (96, 81)):
            if distance(q, (hx, hy)) < 3.3:
                return False
        for pad in pads:
            sx, sy = xy(pad.GetSize())
            # Keep vias off solder lands, including same-net pads.
            radius = math.hypot(sx, sy) / 2
            if distance(q, xy(pad.GetPosition())) < radius + 0.52:
                return False
        for t in tracks:
            if type(t) is p.PCB_VIA:
                margin = 0.56 if t.GetNetname() == "/GND" else 0.82
                if distance(q, xy(t.GetPosition())) < margin:
                    return False
            elif t.GetNetname() != "/GND":
                if segment_distance(q, xy(t.GetStart()), xy(t.GetEnd())) < p.ToMM(t.GetWidth()) / 2 + 0.52:
                    return False
        return all(distance(q, v) >= 0.56 for v in added)

    for signal in signal_vias:
        location = xy(signal.GetPosition())
        existing = min((distance(location, g) for g in ground_vias), default=1e9)
        if existing > 2:
            found = None
            for radius in (1, 1.3, 1.6, 1.9, 2.2, 2.6, 3):
                for k in range(16):
                    theta = 2 * math.pi * k / 16
                    q = (round(location[0] + radius * math.cos(theta), 3),
                         round(location[1] + radius * math.sin(theta), 3))
                    if available(q):
                        found = q
                        break
                if found:
                    break
            if found:
                via = p.PCB_VIA(board)
                via.SetPosition(p.VECTOR2I(p.FromMM(found[0]), p.FromMM(found[1])))
                via.SetWidth(p.FromMM(0.6))
                via.SetDrill(p.FromMM(0.3))
                via.SetViaType(p.VIATYPE_THROUGH)
                via.SetLayerPair(p.F_Cu, p.B_Cu)
                via.SetNet(ground)
                board.Add(via)
                ground_vias.append(found)
                added.append(found)
        nearest = min((distance(location, g) for g in ground_vias), default=None)
        transitions.append({"net": signal.GetNetname(), "position_mm": location,
                            "nearest_ground_via_mm": round(nearest, 3) if nearest is not None else None})

    p.ZONE_FILLER(board).Fill(board.Zones())
    p.SaveBoard(str(path), board)
    # Retain the current review's stitch provenance without depending on a
    # retired board generator or its obsolete ownership stamp.
    reviewed = previous.get("added_ground_vias_mm", []) + added
    current = {tuple(round(n, 4) for n in g) for g in ground_vias}
    new_ground = sorted({tuple(round(n, 4) for n in g) for g in reviewed} & current)
    review = {"revision": "C4", "method": "Geometric return-stitch review, not field simulation",
              "board_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "added_ground_vias_mm": new_ground, "signal_transitions": transitions,
              "limitations": ["No measured loop inductance, pulse response or thermal rating",
                              "Dual-layer ground pours bridge bottom signal routing; not an uninterrupted bottom plane",
                              "Solid ground pad connections require an appropriate soldering profile"]}
    (HW / "cipinkoklingacik-return-review.json").write_text(json.dumps(review, indent=2) + "\n")
    print(f"Added {len(added)} return stitches for {len(transitions)} signal transitions. Run DRC again.")


if __name__ == "__main__":
    main()
