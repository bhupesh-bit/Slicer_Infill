from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid

from common import extract_islands


def classify_topology(path_2d, area_threshold=0.1):
    """
    Robust hole-preserving topology classification.
    Matches behaviour of your FIRST (good) pipeline.
    NO unary_union. Proper parent-child hierarchy.
    """

    polygons = path2d_to_shapely_polygons(path_2d, area_threshold)
    if not polygons:
        return []

    # -----------------------------
    # Clean + flatten
    # -----------------------------
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

    # -----------------------------
    # Sort by area (big → small)
    # -----------------------------
    clean = sorted(clean, key=lambda p: p.area, reverse=True)

    used = [False] * len(clean)
    result_polys = []

    # -----------------------------
    # Build hierarchy (outer + direct holes)
    # -----------------------------
    for i, outer in enumerate(clean):
        if used[i]:
            continue

        holes = []

        for j, inner in enumerate(clean):
            if i == j or used[j]:
                continue

            # must be strictly inside
            if outer.contains(inner):
                # check if inner is NOT inside another hole already selected
                is_direct_child = True
                for h in holes:
                    if h.contains(inner):
                        is_direct_child = False
                        break

                if is_direct_child:
                    holes.append(inner)
                    used[j] = True

        # build polygon with holes
        if holes:
            hole_coords = [list(h.exterior.coords) for h in holes]
            try:
                poly = Polygon(outer.exterior.coords, holes=hole_coords)
                if not poly.is_valid:
                    poly = make_valid(poly)
            except:
                poly = outer
        else:
            poly = outer

        result_polys.append(poly)
        used[i] = True

    # -----------------------------
    # Final formatting
    # -----------------------------
    return extract_islands(result_polys)


# ----------------------------------
# Helper: Path2D → shapely polygons
# ----------------------------------

def path2d_to_shapely_polygons(path_2d, area_threshold=0.1):
    if path_2d is None:
        return []

    polygons = []

    # BEST source (preserves holes correctly)
    if path_2d.polygons_closed is not None and len(path_2d.polygons_closed) > 0:
        for p in path_2d.polygons_closed:
            if p.area >= area_threshold:
                if not p.is_valid:
                    p = make_valid(p)
                if p.is_empty:
                    continue
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
