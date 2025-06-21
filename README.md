# Path Tiles Generator

This project generates Path Tiles board game tiles by enumerating all perfect matchings of swirling tracks on a square tile and exporting 3D models (STL) for 3D printing.

> **Compatible with Tsuro®. Not affiliated with or endorsed by Calliope Games.**

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

## Sample Output

Check out the sample files in the `sample/` directory to see what the generated tiles look like:

![Sample Tile Pattern](sample/sample.png)

* `sample/sample.stl` - A 3D model file ready for 3D printing

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

## Command Line Options

To see all available options:

```bash
python create_tile_mesh.py --help
```

### Available Arguments

- `--engine {earcut,triangle}`: Triangulation engine ('earcut' for mapbox-earcut, 'triangle' for triangle)
- `--sample N`: Number of random tiles to export (default: 36)
- `--output DIR`: Output directory for STL files (default: "output")
- `--tile-size FLOAT`: Tile size in mm (default: 100.0)
- `--tile-thickness FLOAT`: Tile thickness in mm (default: 5.0)
- `--channel-depth FLOAT`: Depth of the curved channels in mm (default: 3.0)
- `--path-radius FLOAT`: Radius of the path channels in mm (default: 2.0)
- `--dot-radius FLOAT`: Radius of endpoint dots in mm (default: None, which is 3x path_radius)

### Example Commands

```bash
# Export 10 tiles with custom dimensions
python create_tile_mesh.py --sample 10 --tile-size 80 --tile-thickness 4

# Create thicker tiles with deeper channels
python create_tile_mesh.py --tile-thickness 8 --channel-depth 5 --path-radius 2.5

# Export all tiles with large endpoint dots
python create_tile_mesh.py --sample 105 --dot-radius 8

# Use triangle engine with custom output directory
python create_tile_mesh.py --engine triangle --output my_tiles
```

## Configuration

All tile dimensions and path parameters can be customized via command line arguments:

* **Tile dimensions**:
  * `--tile-size` (e.g. `100.0` mm)
  * `--tile-thickness` (e.g. `5.0` mm)

* **Path parameters**:
  * `--channel-depth` (e.g. `3.0` mm)
  * `--path-radius` (e.g. `2.0` mm)
  * `--dot-radius` (e.g. `6.0` mm) - radius of semicircle dots at endpoints

Feel free to tweak these values to suit your printer and design aesthetic. Use `python create_tile_mesh.py --help` to see all available options.

## License

This project is licensed under the MIT License. Feel free to adapt and extend it for personal or commercial use.
