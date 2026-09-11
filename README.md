# Battlezone II XSI Importer / Exporter for Blender

Blender add-on for importing and exporting Battlezone II / Combat Commander XSI assets.

## Features

- Import `.xsi` models and scenes.
- Export supported Blender scenes back to Battlezone II XSI.
- Browse/import XSI assets directly from Battlezone II `.pak` archives.
- Extract `.pak` archives.
- Decode Softimage `.pic` textures and convert them to PNG during import.
- Handle common Battlezone II material, UV, vertex-color, animation, envelope, light, and camera data.

## Blender compatibility

The add-on metadata requires **Blender 4.1 or newer**. The current v1.0.9 code includes compatibility work for the Blender 4.5 LTS API, including modern mesh normals and color attributes.

This repository is distributed as a **legacy Blender add-on** rather than a Blender Extensions package. Blender 4.5 LTS still supports installing legacy add-ons from disk.

## Install from a GitHub Release

1. Download `io_scene_bz2xsi-v1.0.9.zip` from the latest GitHub Release.
2. In Blender, open **Edit > Preferences > Add-ons**.
3. Use **Install from Disk** and select the ZIP.
4. Enable **BZ2 XSI format**.
5. Use **File > Import > BZ2 XSI / PAK** or **File > Export > BZ2 XSI**.

Do not unzip the release archive manually before installing it. The release ZIP already contains the required top-level `io_scene_bz2xsi` folder.

## Manual development install

For a source checkout, create an `io_scene_bz2xsi` directory inside Blender's add-ons directory and place these runtime files inside it:

- `__init__.py`
- `bz2xsi.py`
- `bz2pak.py`
- `softimage_pic.py`
- `xsi_blender_importer.py`
- `xsi_blender_exporter.py`

Restart Blender or refresh add-ons, then enable **BZ2 XSI format**.

## Release packaging

GitHub release tags (`v*`) are validated before publishing. The release workflow checks that the tag matches `bl_info["version"]`, byte-compiles the runtime Python files, builds an installable Blender ZIP, verifies its layout, and attaches it to the GitHub Release.
