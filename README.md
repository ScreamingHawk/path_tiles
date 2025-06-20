# Path Tiles Generator

This project generates Path Tiles board game tiles by enumerating all perfect matchings of swirling tracks on a square tile and exporting 3D models (STL) for 3D printing.

## Prerequisites

* Python 3.8+ installed
* `pip` package manager

## Virtual Environment Setup

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```
2. Activate the environment:

   * On Linux/macOS:

     ```bash
     source venv/bin/activate
     ```
   * On Windows (PowerShell):

     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * On Windows (cmd.exe):

     ```cmd
     venv\Scripts\activate.bat
     ```

## Dependency Management

A `requirements.txt` file in the repo pins all Python dependencies for reproducibility.

* To **freeze** your current environment's packages:

  ```bash
  pip install --upgrade pip
  pip install numpy trimesh shapely
  pip freeze > requirements.txt
  ```
* To **install** the exact versions listed:

  ```bash
  pip install -r requirements.txt
  ```

> **Tip:** Whenever you add or update packages, rerun:
>
> ```bash
> pip freeze > requirements.txt
> ```
>
> to keep your dependencies locked.

## Scripts

The repository contains two main scripts:

* `generate_path_tiles.py`: Enumerates all perfect matchings on 8 endpoints and prints a sample of 36 patterns.
* `create_tile_mesh.py`: Uses `trimesh` to create 3D meshes for each tile and exports STL files to an `output/` folder.

## Usage

1. **Generate matchings and preview a sample**

   ```bash
   python generate_path_tiles.py
   ```

   * Outputs the total number of matchings (`105`) and prints a random sample of `36` unique swirl patterns.

2. **Export STL files**

   ```bash
   python create_tile_mesh.py
   ```

   * Creates an `output/` directory and writes files named `tile_001.stl`, `tile_002.stl`, … up to the default sample of `36`.
   * To export **all** `105` tiles, use:

     ```bash
     python create_tile_mesh.py --sample 105
     ```
   * To customize endpoint dot size:

     ```bash
     python create_tile_mesh.py --dot-radius 2.0
     ```

## Configuration

* **Tile dimensions** and **path parameters** live in the `create_tile_mesh` function:

  * `tile_size` (e.g. `100.0` mm)
  * `tile_thickness` (e.g. `5.0` mm)
  * `channel_depth` (e.g. `3.0` mm)
  * `path_radius` (e.g. `2.0` mm)
  * `endpoint_dot_radius` (e.g. `1.5` mm) - radius of semicircle dots at endpoints

Feel free to tweak these values to suit your printer and design aesthetic.

> **Note:** The code automatically handles overlapping grooves by merging them before creating the 3D mesh, ensuring proper cuts even when paths cross or overlap.

## Next Steps

* Replace straight cylinders with curved splines or Bezier patches for smoother swirling tracks.
* Add chamfers or fillets to base edges for a refined look.
* Integrate with a CAD API (e.g., FreeCAD) for more advanced modeling.

## License

This project is licensed under the MIT License. Feel free to adapt and extend it for personal or commercial use.
