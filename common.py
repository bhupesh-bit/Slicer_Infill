import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon

def load_mesh(mesh_path):
    return trimesh.load(mesh_path)

def get_bounding_box(mesh):
    return mesh.bounds[0], mesh.bounds[1]

def generate_z_levels(mesh, layer_height):
    z_min, z_max = mesh.bounds[:, 2]
    eps = 1e-6
    return np.arange(z_min, z_max + eps, layer_height)

def slice_at_z(mesh, z):
    section_3d = mesh.section(
        plane_origin=[0, 0, z],
        plane_normal=[0, 0, 1]
    )
    if section_3d is None:
        return None
    section_2d, _ = section_3d.to_2D()
    return section_2d

def extract_islands(geometry):
    """
    Standardizes output format for all slicing methods.
    Accepts: shapely Polygon, MultiPolygon, or List[Polygon]
    Returns: List of dicts [{'outer': [], 'holes': []}, ...]
    """
    results = []
    
    # Handle List of Polygons (output from slicer_topology)
    if isinstance(geometry, list):
        geoms = geometry
    # Handle Single Polygon
    elif isinstance(geometry, Polygon):
        geoms = [geometry]
    # Handle MultiPolygon (output from unary_union)
    elif isinstance(geometry, MultiPolygon):
        geoms = list(geometry.geoms)
    else:
        return []

    for poly in geoms:
        if poly.is_empty:
            continue
            
        results.append({
            "outer": list(poly.exterior.coords),
            "holes": [list(h.coords) for h in poly.interiors]
        })

    return results