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
