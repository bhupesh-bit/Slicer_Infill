# 3D Printing Infill Path Generator



## Requirements

- Python 3.14
- numpy
- trimesh
- shapely
- matplotlib

## Installation

Install the required dependencies:

```bash
pip install numpy trimesh shapely matplotlib
```

## Usage

### Basic Usage

Run the main script with default settings:

```bash
python main.py
```

This will process `Carburetor.stl` and generate visualization images in the `final_infill_output/` directory.

### Configuration

Edit the configuration section in `main.py`:

```python
MODEL_NAME = "Carburetor.stl"      # Input STL file
LAYER_HEIGHT = 0.2                 # Layer height in mm
AREA_THRESHOLD = 0.5               # Minimum area for islands (mm²)
INFILL_SPACING = 1.0               # Infill line spacing in mm
INFILL_ANGLE = 30.0                # Infill angle in degrees
OUTPUT_DIR = "final_infill_output" # Output directory
```

## Project Structure

```
infill_final/
├── main.py                 # Main pipeline orchestrator
├── common.py               # Mesh loading and slicing utilities
├── slicer_topology.py      # Topology classification (islands/holes)
├── infill_generator.py     # Parametric infill pattern generation
├── toolpath_planner.py     # Path optimization and connection
├── Carburetor.stl          # Example STL model
├── cluster.stl             # Example STL model
└── final_infill_output/    # Generated visualization images
    ├── 0.00/
    │   └── layer.png
    ├── 0.20/
    │   └── layer.png
    └── ...
```

## How It Works

### 1. Mesh Loading (`common.py`)
- Loads STL files using trimesh
- Generates Z-levels based on layer height
- Slices the mesh at each Z-level to create 2D cross-sections

### 2. Topology Classification (`slicer_topology.py`)
- Converts 2D slices to Shapely polygons
- Identifies separate islands (disconnected regions)
- Detects holes within islands
- Filters out small features below the area threshold

### 3. Infill Generation (`infill_generator.py`)
- Generates parallel infill lines at the specified angle
- Clips lines to polygon boundaries
- Handles multiple islands and holes correctly

### 4. Path Optimization (`toolpath_planner.py`)
- **Smooth Connection**: Orders infill lines to minimize travel distance
- **Travel Optimization**: 
  - Uses direct travel when safe (within polygon, not crossing holes)
  - Reroutes along boundaries when direct travel would cross holes
- **Island Ordering**: Orders islands by nearest-neighbor for global optimization

### 5. Visualization (`main.py`)
- Generates PNG images for each layer showing:
  - **Black lines**: Island boundaries
  - **Red lines**: Holes
  - **Blue lines**: Extrusion paths
  - **Orange dashed lines**: Travel moves
  - **Green marker**: Start point
  - **Purple marker**: End point

## Output Format

Each processed layer generates a folder named after its Z-height (e.g., `0.00/`, `0.20/`) containing:
- `layer.png`: Visualization of the toolpath for that layer

## Example Output

The visualization shows:
- Island perimeters in black
- Holes in red
- Extrusion paths in blue (solid lines)
- Travel moves in orange (dashed lines)
- Start/end markers for the toolpath

## Dependencies

- **numpy**: Numerical operations
- **trimesh**: 3D mesh loading and slicing
- **shapely**: 2D geometric operations (polygons, lines, intersections)
- **matplotlib**: Visualization and image generation

## Notes

- The toolpath planner intelligently avoids crossing holes during travel moves
- Islands are automatically ordered to minimize total travel distance
- Invalid polygons are automatically fixed using `make_valid()`
- Empty or very small features are filtered out based on the area threshold
