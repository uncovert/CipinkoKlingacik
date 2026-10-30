"""Dependency-free pad-centre/track geometry for regression review, not a solver.

Tracks are split at collinear same-net endpoints/pad centres; vias join copper
layers. Does not model zone-current distribution, pad spreading or inductance.
"""
import heapq
import math
from kicad_sexpr import child, children


def footprint_pads(board):
    result = {}
    for fp in children(board, "footprint"):
        ref = next(v[2] for v in children(fp, "property") if v[1] == "Reference")
        at = child(fp, "at")
        x, y = map(float, at[1:3])
        theta = math.radians(float(at[3]) if len(at) > 3 else 0)
        for pad in children(fp, "pad"):
            px, py = map(float, child(pad, "at")[1:3])
            point = (round(x + px * math.cos(theta) + py * math.sin(theta), 5),
                     round(y - px * math.sin(theta) + py * math.cos(theta), 5))
            if children(pad, "net"):
                result[(ref, pad[1])] = (point, child(pad, "net")[-1])
    return result


def via_smt_clearance_violations(board, clearance=0.1):
    """Conservative annulus-to-pad/mask/paste clearance for fitted SMT parts.

    Uses enclosing rectangles (including rotated pads and positive local mask/
    paste margins), so rounded corners never hide a possible solder opening.
    DNP parts and probe-only PCB features are not baseline solder joints.
    This is a baseline DFM guard, not a full soldermask/process simulation.
    """
    positions = footprint_pads(board)
    violations = []
    for fp in children(board, "footprint"):
        props = {p[1]: p[2] for p in children(fp, "property")}
        if props.get("Assembly") != "SMT" or "dnp" in child(fp, "attr"):
            continue
        ref = props["Reference"]
        for pad in children(fp, "pad"):
            if pad[2] != "smd":
                continue
            point, _ = positions[(ref, pad[1])]
            w, h = map(float, child(pad, "size")[1:3])
            at = child(pad, "at")
            # Pad angles in a board file are absolute, not relative to the FP.
            theta = math.radians(float(at[3]) if len(at) > 3 else 0)
            margin = 0.0
            for owner in (child(board, "setup"), fp, pad):
                for key in ("pad_to_mask_clearance", "solder_mask_margin", "solder_paste_margin"):
                    for value in children(owner, key):
                        margin = max(margin, float(value[1]))
            for via in children(board, "via"):
                x, y = map(float, child(via, "at")[1:3])
                dx, dy = x - point[0], y - point[1]
                local_x = dx * math.cos(theta) - dy * math.sin(theta)
                local_y = dx * math.sin(theta) + dy * math.cos(theta)
                distance = math.hypot(max(abs(local_x) - w / 2 - margin, 0),
                                      max(abs(local_y) - h / 2 - margin, 0))
                gap = distance - float(child(via, "size")[1]) / 2
                if gap < clearance - 1e-7:
                    violations.append({"pad": f"{ref}.{pad[1]}", "via": (x, y),
                                       "annulus_gap_mm": round(gap, 6)})
    return violations


def track_path_mm(board, start, end):
    pads = footprint_pads(board)
    a, net = pads[start]
    b, other = pads[end]
    if net != other:
        raise ValueError("Different nets")
    tracks = [s for s in children(board, "segment") if child(s, "net")[-1] == net]
    vias = [v for v in children(board, "via") if child(v, "net")[-1] == net]
    points = {a, b}
    for track in tracks:
        points.update(tuple(round(float(n), 5) for n in child(track, side)[1:3]) for side in ("start", "end"))
    for via in vias:
        points.add(tuple(round(float(n), 5) for n in child(via, "at")[1:3]))
    graph = {}

    def connect(u, v, length):
        graph.setdefault(u, []).append((v, length))
        graph.setdefault(v, []).append((u, length))

    for track in tracks:
        u = tuple(map(float, child(track, "start")[1:3]))
        v = tuple(map(float, child(track, "end")[1:3]))
        layer = child(track, "layer")[1]
        length = math.dist(u, v)
        if length < 1e-7:
            continue
        along = []
        for point in points:
            if abs(math.dist(u, point) + math.dist(point, v) - length) < 1e-5:
                along.append((math.dist(u, point), point))
        along.sort()
        for (du, pu), (dv, pv) in zip(along, along[1:]):
            connect((*pu, layer), (*pv, layer), dv - du)
    for via in vias:
        point = tuple(round(float(n), 5) for n in child(via, "at")[1:3])
        connect((*point, "F.Cu"), (*point, "B.Cu"), 0)
    queue, best = [(0, (*a, "F.Cu"))], {(*a, "F.Cu"): 0}
    while queue:
        length, node = heapq.heappop(queue)
        if node == (*b, "F.Cu"):
            return length
        if length != best[node]:
            continue
        for nxt, distance in graph.get(node, []):
            candidate = length + distance
            if candidate < best.get(nxt, math.inf):
                best[nxt] = candidate
                heapq.heappush(queue, (candidate, nxt))
    raise ValueError(f"No explicit track-centre path: {start} -> {end}")
