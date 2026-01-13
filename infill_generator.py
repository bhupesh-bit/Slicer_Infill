import math
from shapely.geometry import Polygon, LineString, MultiLineString
from shapely.affinity import rotate, translate


def generate_parametric_infill(island, spacing=1.0, angle_deg=0.0):
    """
    island: {
        "outer": [(x,y), ...],
        "holes": [[(x,y), ...], ...]
    }

    Returns: List[LineString]
    """

    shell = island["outer"]
    holes = island["holes"]

    poly = Polygon(shell=shell, holes=holes)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return []

    minx, miny, maxx, maxy = poly.bounds
    width = maxx - minx
    height = maxy - miny
    diag = math.hypot(width, height)

    num_lines = int(diag / spacing) + 3

    base_lines = []
    for i in range(-num_lines, num_lines + 1):
        y = i * spacing
        line = LineString([(-diag, y), (diag, y)])
        base_lines.append(line)

    rotated = [rotate(l, angle_deg, origin=(0, 0)) for l in base_lines]

    cx, cy = poly.centroid.coords[0]
    moved = [translate(l, xoff=cx, yoff=cy) for l in rotated]

    clipped = []
    for line in moved:
        inter = poly.intersection(line)
        if inter.is_empty:
            continue
        if isinstance(inter, LineString):
            clipped.append(inter)
        elif isinstance(inter, MultiLineString):
            for seg in inter.geoms:
                clipped.append(seg)

    return clipped
