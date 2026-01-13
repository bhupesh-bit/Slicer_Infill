from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid

from common import extract_islands


def classify_topology(path_2d, area_threshold=0.1):
    """
    Robust hole-preserving topology classification.
    DOES NOT use unary_union (because it destroys holes).
    """

    polygons = path2d_to_shapely_polygons(path_2d, area_threshold)
    if not polygons:
        return []

    # Fix invalids and flatten
    clean = []
    for p in polygons:
        if not p.is_valid:
            p = make_valid(p)
        if p.is_empty:
            continue
        if isinstance(p, MultiPolygon):
            clean.extend(list(p.geoms))
        else:
            clean.append(p)

    if not clean:
        return []

    # --------------------------------------
    # Build parent-child (outer-hole) relation
    # --------------------------------------
    clean = sorted(clean, key=lambda p: p.area, reverse=True)

    used = [False] * len(clean)
    result = []

    for i, outer in enumerate(clean):
        if used[i]:
            continue

        holes = []

        for j, inner in enumerate(clean):
            if i == j or used[j]:
                continue

            # if inner is completely inside outer → it's a hole
            if outer.contains(inner):
                holes.append(inner)
                used[j] = True

        if holes:
            hole_coords = [list(h.exterior.coords) for h in holes]
            poly = Polygon(outer.exterior.coords, holes=hole_coords)
        else:
            poly = outer

        result.append(poly)
        used[i] = True

    return extract_islands(result)


# -------------------------------
# Helpers
# -------------------------------

def path2d_to_shapely_polygons(path_2d, area_threshold=0.1):
    if path_2d is None:
        return []

    polygons = []

    # Best source
    if path_2d.polygons_closed is not None and len(path_2d.polygons_closed) > 0:
        for p in path_2d.polygons_closed:
            if p.area >= area_threshold:
                polygons.append(p)
        return polygons

    # Fallback
    for loop in path_2d.discrete:
        if len(loop) < 3:
            continue
        try:
            poly = Polygon(loop)
            if poly.area < area_threshold:
                continue
            if not poly.is_valid:
                poly = make_valid(poly)
            if poly.is_empty:
                continue
            if isinstance(poly, MultiPolygon):
                polygons.extend(list(poly.geoms))
            else:
                polygons.append(poly)
        except:
            continue

    return polygons
