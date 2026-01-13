import math
import numpy as np
from shapely import Polygon
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points


def connect_infill_smooth(infill_lines, angle_deg):
    """
    infill_lines: List[LineString]
    angle_deg: infill angle (same as used in infill)

    Returns: List[LineString] ordered smoothly
    """

    if not infill_lines:
        return []

    theta = math.radians(angle_deg)
    dir_vec = np.array([math.cos(theta), math.sin(theta)])

    projected = []
    for line in infill_lines:
        coords = np.array(line.coords)
        mid = coords.mean(axis=0)
        proj = np.dot(mid, dir_vec)
        projected.append((proj, line))

    projected.sort(key=lambda x: x[0])
    sorted_lines = [l for _, l in projected]

    ordered = []
    used = [False] * len(sorted_lines)

    current = sorted_lines[0]
    ordered.append(current)
    used[0] = True
    current_end = current.coords[-1]

    for _ in range(1, len(sorted_lines)):
        best_idx = None
        best_dist = float("inf")
        best_oriented = None

        for i, line in enumerate(sorted_lines):
            if used[i]:
                continue

            coords = list(line.coords)
            d_start = math.dist(current_end, coords[0])
            d_end = math.dist(current_end, coords[-1])

            if d_start < best_dist:
                best_dist = d_start
                best_idx = i
                best_oriented = coords

            if d_end < best_dist:
                best_dist = d_end
                best_idx = i
                best_oriented = coords[::-1]

        used[best_idx] = True
        ordered.append(LineString(best_oriented))
        current_end = best_oriented[-1]

    return ordered

def optimize_travel_segments(island, ordered_lines):
    """
    island: {outer, holes}
    ordered_lines: List[LineString]

    Returns:
        List of (extrude_line, travel_line_or_None)
    """

    shell = island["outer"]
    holes = island["holes"]

    poly = Polygon(shell=shell, holes=holes)

    hole_polys = [Polygon(h) for h in holes]

    optimized = []

    for i, line in enumerate(ordered_lines):
        travel_line = None

        if i < len(ordered_lines) - 1:
            end_pt = Point(line.coords[-1])
            next_start = Point(ordered_lines[i + 1].coords[0])

            direct = LineString([end_pt, next_start])

            crosses_hole = False
            for h in hole_polys:
                if direct.intersects(h):
                    crosses_hole = True
                    break

            # Case 1: safe direct travel
            if poly.contains(direct) and not crosses_hole:
                travel_line = direct

            # Case 2: reroute along outer boundary
            else:
                boundary = poly.exterior

                p1, _ = nearest_points(end_pt, boundary)
                p2, _ = nearest_points(next_start, boundary)

                travel_line = LineString([end_pt, p1, p2, next_start])

        optimized.append((line, travel_line))

    return optimized