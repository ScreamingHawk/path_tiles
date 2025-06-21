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
from shapely.geometry import LineString, Polygon
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
    endpoint_dot_radius: float = 6.0,
    bezier_steps: int = 64,
    triang_engine: str = None,
) -> trimesh.Trimesh:
    """Build a Path Tiles tile with curved grooves and endpoint circle cuts embedded into the surface."""
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

    # Create endpoint dots as cylinders, clipped to the tile boundary
    endpoint_dots = []
    for i in range(8):
        x, y = endpoints2d[i]
        try:
            # Create a simple cylinder
            cylinder = trimesh.creation.cylinder(
                radius=endpoint_dot_radius, height=channel_depth, sections=32
            )
            # Position the cylinder so its top is flush with the tile top
            cylinder.apply_translation([x, y, tile_thickness - channel_depth / 2])
            # Clip to tile boundary by creating a box and intersecting
            tile_box = trimesh.creation.box(
                extents=[tile_size, tile_size, channel_depth],
                transform=trimesh.transformations.translation_matrix(
                    [tile_size / 2, tile_size / 2, tile_thickness - channel_depth / 2]
                ),
            )
            # Intersect cylinder with tile box
            try:
                clipped_cylinder = trimesh.boolean.intersection(
                    [cylinder, tile_box], engine="manifold"
                )
                if clipped_cylinder is not None and clipped_cylinder.volume > 0:
                    endpoint_dots.append(clipped_cylinder)
                else:
                    print(
                        f"Warning: Invalid clipped cylinder at endpoint {i}, skipping"
                    )
            except Exception as e:
                print(f"Warning: Boolean intersection failed at endpoint {i}: {e}")
                # Fallback: use original cylinder if intersection fails
                if cylinder.volume > 0:
                    endpoint_dots.append(cylinder)
        except Exception as e:
            print(f"Warning: Failed to create cylinder dot at endpoint {i}: {e}")

    # After all endpoint dot creation logic
    if len(endpoint_dots) < 8:
        raise RuntimeError(
            f"Failed to create all endpoint dots! Only {len(endpoint_dots)} were created. Check your dot radius and tile size."
        )

    # Combine all groove meshes
    channel_mesh = None
    if groove_meshes:
        channel_mesh = trimesh.util.concatenate(groove_meshes)
    dot_mesh = None
    if endpoint_dots:
        dot_mesh = trimesh.util.concatenate(endpoint_dots)

    # Validate meshes before boolean operations
    def is_valid_mesh(mesh):
        """Check if mesh is valid for boolean operations."""
        if mesh is None:
            return False
        # Check if mesh has volume and is watertight
        return mesh.volume > 0 and mesh.is_watertight and mesh.is_winding_consistent

    # Subtract both grooves and endpoint dots from the base
    cutters = []
    if channel_mesh is not None and is_valid_mesh(channel_mesh):
        cutters.append(channel_mesh)
    if dot_mesh is not None and is_valid_mesh(dot_mesh):
        cutters.append(dot_mesh)

    if cutters:
        try:
            carved = difference([base] + cutters, engine="manifold")
        except Exception as e:
            print(f"Warning: Manifold boolean failed: {e}")
            try:
                carved = difference([base] + cutters, engine="scad")
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to create tile mesh: both manifold and scad boolean operations failed. Manifold error: {e}, SCAD error: {e2}"
                )
    else:
        carved = base

    return carved


def export_tiles(
    matchings,
    output_dir: str = "output",
    sample_size: int = None,
    triang_engine: str = None,
    tile_size: float = 100.0,
    tile_thickness: float = 5.0,
    channel_depth: float = 3.0,
    path_radius: float = 2.0,
    endpoint_dot_radius: float = 6.0,
):
    """Export Path Tiles meshes to STL."""
    os.makedirs(output_dir, exist_ok=True)
    pool = random.sample(matchings, sample_size) if sample_size else matchings

    for idx, m in enumerate(pool, start=1):
        mesh = create_tile_mesh(
            m,
            tile_size=tile_size,
            tile_thickness=tile_thickness,
            channel_depth=channel_depth,
            path_radius=path_radius,
            endpoint_dot_radius=endpoint_dot_radius,
            triang_engine=triang_engine,
        )
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
    parser.add_argument(
        "--tile-size",
        type=float,
        default=100.0,
        help="Tile size in mm (default: 100.0).",
    )
    parser.add_argument(
        "--tile-thickness",
        type=float,
        default=5.0,
        help="Tile thickness in mm (default: 5.0).",
    )
    parser.add_argument(
        "--channel-depth",
        type=float,
        default=3.0,
        help="Depth of the curved channels in mm (default: 3.0).",
    )
    parser.add_argument(
        "--path-radius",
        type=float,
        default=2.0,
        help="Radius of the path channels in mm (default: 2.0).",
    )
    parser.add_argument(
        "--dot-radius",
        type=float,
        default=6.0,
        help="Radius of endpoint dots in mm (default: 6.0).",
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
        tile_size=args.tile_size,
        tile_thickness=args.tile_thickness,
        channel_depth=args.channel_depth,
        path_radius=args.path_radius,
        endpoint_dot_radius=args.dot_radius,
    )


if __name__ == "__main__":
    main()
