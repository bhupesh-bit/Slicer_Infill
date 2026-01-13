import os
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point

from common import load_mesh, generate_z_levels, slice_at_z
from slicer_topology import classify_topology
from infill_generator import generate_parametric_infill
from toolpath_planner import connect_infill_smooth, optimize_travel_segments



# =========================
# CONFIG
# =========================
MODEL_NAME = "Carburetor.stl"
LAYER_HEIGHT = 0.2
AREA_THRESHOLD = 0.5

INFILL_SPACING = 1.0
INFILL_ANGLE = 30.0

OUTPUT_DIR = "final_infill_output"


# =========================
# FINAL PLOT
# =========================
def plot_layer_all_islands(islands, global_path, save_path):
    fig, ax = plt.subplots(figsize=(8, 8))

    # -------------------------
    # Draw all island boundaries
    # -------------------------
    for island in islands:
        ox, oy = zip(*island["outer"])
        ax.plot(ox, oy, color="black", linewidth=2)

        for hole in island["holes"]:
            hx, hy = zip(*hole)
            ax.plot(hx, hy, color="red", linewidth=2)

    global_start = None
    global_end = None

    # -------------------------
    # Draw GLOBAL toolpath
    # -------------------------
    for extrude, travel in global_path:

        # Extrusion
        if extrude is not None:
            x, y = extrude.xy
            ax.plot(x, y, color="blue", linewidth=1.2)

            if global_start is None:
                global_start = extrude.coords[0]

            global_end = extrude.coords[-1]

        # Travel
        if travel is not None:
            tx, ty = travel.xy
            ax.plot(tx, ty, color="orange", linewidth=1, linestyle="--")

    # -------------------------
    # Mark START and END
    # -------------------------
    if global_start is not None:
        ax.plot(global_start[0], global_start[1], marker="o", color="green", markersize=10, label="Start")

    if global_end is not None:
        ax.plot(global_end[0], global_end[1], marker="o", color="purple", markersize=10, label="End")

    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()

def connect_islands_globally(optimized_paths_per_island):
    """
    optimized_paths_per_island: list of optimized_path (each is list of (extrude, travel))

    Returns:
        global_path: list of (extrude, travel)
        where travel also includes island-to-island travel
    """

    global_path = []

    prev_end_point = None

    for island_path in optimized_paths_per_island:
        if not island_path:
            continue

        # If this is not the first island, add travel from previous island end to this island start
        first_extrude = island_path[0][0]
        start_pt = Point(first_extrude.coords[0])

        if prev_end_point is not None:
            travel_line = LineString([prev_end_point, start_pt])
            global_path.append((None, travel_line))  # None means pure travel

        # Add island internal path
        for extrude, travel in island_path:
            global_path.append((extrude, travel))

        # Update prev_end_point
        last_extrude = island_path[-1][0]
        prev_end_point = Point(last_extrude.coords[-1])

    return global_path
def order_islands_by_nearest(optimized_paths_per_island):
    """
    optimized_paths_per_island: list of optimized_path (each is list of (extrude, travel))

    Returns:
        reordered list of optimized_paths_per_island
    """

    if not optimized_paths_per_island:
        return []

    remaining = optimized_paths_per_island.copy()
    ordered = []

    # start with first island
    current = remaining.pop(0)
    ordered.append(current)

    # current end point
    last_extrude = current[-1][0]
    current_pt = Point(last_extrude.coords[-1])

    while remaining:
        best_idx = None
        best_dist = float("inf")

        for i, island_path in enumerate(remaining):
            first_extrude = island_path[0][0]
            start_pt = Point(first_extrude.coords[0])

            dist = current_pt.distance(start_pt)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        next_island = remaining.pop(best_idx)
        ordered.append(next_island)

        last_extrude = next_island[-1][0]
        current_pt = Point(last_extrude.coords[-1])

    return ordered
# =========================
# MAIN PIPELINE
# =========================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading mesh...")
    mesh = load_mesh(MODEL_NAME)

    z_levels = generate_z_levels(mesh, LAYER_HEIGHT)
    print("Total layers:", len(z_levels))

    for i, z in enumerate(z_levels):
        section_2d = slice_at_z(mesh, z)
        if section_2d is None:
            continue

        islands = classify_topology(section_2d, AREA_THRESHOLD)
        if not islands:
            continue

        layer_folder = os.path.join(OUTPUT_DIR, f"{z:.2f}")
        os.makedirs(layer_folder, exist_ok=True)

        optimized_paths_per_island = []
    
        for island in islands:
            infill = generate_parametric_infill(
                island,
                spacing=INFILL_SPACING,
                angle_deg=INFILL_ANGLE
            )

            ordered_path = connect_infill_smooth(infill, INFILL_ANGLE)

            optimized_path = optimize_travel_segments(island, ordered_path)

            optimized_paths_per_island.append(optimized_path)

       
        # ---- OPTIMIZE ISLAND ORDER ----
        optimized_paths_per_island = order_islands_by_nearest(optimized_paths_per_island)
         # ---- GLOBAL CONNECTION ----
        global_path = connect_islands_globally(optimized_paths_per_island)

        save_path = os.path.join(layer_folder, "layer.png")
        plot_layer_all_islands(islands, global_path, save_path)

        if i % 10 == 0:
            print(f"Processed layer {i}/{len(z_levels)} at Z={z:.2f}")

    print("DONE. Output saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
