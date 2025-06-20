"""
Path Tiles Generator with Curved, Embedded Channels

This script enumerates perfect matchings for Path Tiles and exports
STL models where swirling tracks are carved as curved grooves in the tile surface.

Usage:
```
python create_tile_mesh.py [--engine earcut|triangle] [--sample 36]
```
"""

import os
import random
import argparse
import numpy as np
import trimesh
from shapely.geometry import LineString
from shapely.ops import unary_union
from trimesh.creation import extrude_polygon
from trimesh.boolean import difference

from generate_path_tiles import generate_matchings

try:
    import mapbox_earcut

    DEFAULT_ENGINE = "earcut"
except ImportError:
    try:
        import triangle

        DEFAULT_ENGINE = "triangle"
    except ImportError:
        DEFAULT_ENGINE = None


def create_tile_mesh(
    matching,
    tile_size: float = 100.0,
    tile_thickness: float = 5.0,
    channel_depth: float = 3.0,
    path_radius: float = 2.0,
    bezier_steps: int = 64,
    triang_engine: str = None,
) -> trimesh.Trimesh:
    """Build a Path Tiles tile with curved grooves embedded into the surface."""
    engine = triang_engine or DEFAULT_ENGINE
    if engine is None:
        raise ImportError(
            "No triangulation engine found. Install mapbox-earcut or triangle via:\n"
            "  pip install mapbox-earcut triangle"
        )

    base = trimesh.creation.box(
        extents=[tile_size, tile_size, tile_thickness],
        transform=trimesh.transformations.translation_matrix(
            [tile_size / 2, tile_size / 2, tile_thickness / 2]
        ),
    )

    q = tile_size / 4.0
    endpoints2d = [
        (q, tile_size),
        (3 * q, tile_size),
        (tile_size, 3 * q),
        (tile_size, q),
        (3 * q, 0),
        (q, 0),
        (0, q),
        (0, 3 * q),
    ]
    center = np.array([tile_size / 2, tile_size / 2])

    # Create individual groove polygons first
    groove_polygons = []
    for i, j in matching:
        p0 = np.array(endpoints2d[i])
        p1 = np.array(endpoints2d[j])
        ts = np.linspace(0, 1, bezier_steps)
        curve = np.vstack(
            [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * center + t**2 * p1 for t in ts]
        )
        line = LineString(curve)
        tube = line.buffer(path_radius, cap_style=1, join_style=1)
        groove_polygons.append(tube)

    # Merge overlapping groove polygons using shapely union
    if groove_polygons:
        merged_grooves = unary_union(groove_polygons)

        # Handle both single polygon and multipolygon cases
        if merged_grooves.geom_type == "Polygon":
            groove_meshes = [
                extrude_polygon(merged_grooves, height=channel_depth, engine=engine)
            ]
        elif merged_grooves.geom_type == "MultiPolygon":
            groove_meshes = []
            for polygon in merged_grooves.geoms:
                groove_mesh = extrude_polygon(
                    polygon, height=channel_depth, engine=engine
                )
                groove_meshes.append(groove_mesh)
        else:
            groove_meshes = []
    else:
        groove_meshes = []

    # Apply translation to all groove meshes
    for groove_mesh in groove_meshes:
        groove_mesh.apply_translation([0, 0, tile_thickness - channel_depth])

    # Combine all groove meshes
    if groove_meshes:
        channel_mesh = trimesh.util.concatenate(groove_meshes)
        # Use a more robust boolean operation
        try:
            carved = difference([base, channel_mesh], engine="manifold")
        except Exception:
            # Fallback to scad engine if manifold fails
            carved = difference([base, channel_mesh], engine="scad")
    else:
        carved = base

    return carved


def export_tiles(
    matchings,
    output_dir: str = "output",
    sample_size: int = None,
    triang_engine: str = None,
):
    """Export Path Tiles meshes to STL."""
    os.makedirs(output_dir, exist_ok=True)
    pool = random.sample(matchings, sample_size) if sample_size else matchings

    for idx, m in enumerate(pool, start=1):
        mesh = create_tile_mesh(m, triang_engine=triang_engine)
        path = os.path.join(output_dir, f"tile_{idx:03d}.stl")
        mesh.export(path)
        print(f"→ Exported {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export Path Tiles as STL with curved grooves."
    )
    parser.add_argument(
        "--engine",
        choices=["earcut", "triangle"],
        help="Triangulation engine ('earcut' for mapbox-earcut, 'triangle' for triangle).",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=36,
        help="Number of random tiles to export (default: 36).",
    )
    parser.add_argument(
        "--output", default="output", help="Output directory for STL files."
    )
    args = parser.parse_args()

    engine = args.engine or DEFAULT_ENGINE
    if engine is None:
        parser.error(
            "No triangulation engine available; install mapbox-earcut or triangle."
        )

    endpoints = list(range(8))
    all_matchings = list(generate_matchings(endpoints))
    export_tiles(
        matchings=all_matchings,
        output_dir=args.output,
        sample_size=args.sample,
        triang_engine=engine,
    )


if __name__ == "__main__":
    main()
