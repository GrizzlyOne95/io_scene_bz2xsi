# Battlezone II XSI Importer / Exporter for Blender

Blender add-on for working with **Battlezone II** / **Battlezone: Combat Commander** Softimage XSI assets.

It imports game XSI models and scenes into Blender, exports supported Blender scenes back to the game's XSI format, can browse and extract assets from Battlezone II `.pak` archives, and includes texture helpers for original game art formats.

## Project status

- **Add-on version:** v1.0.10
- **Blender metadata:** Blender 4.1+
- **Current development branch:** `main`
- **Validated on current `main`:** Blender 5.2
- **Distribution:** legacy Blender add-on (not a Blender Extensions package)

## Features

### XSI import

- Import Battlezone II / Combat Commander `.xsi` models and scenes.
- Import meshes, normals, UVs, vertex colors, materials, lights, and cameras.
- Import object animation and bone-envelope animation.
- Support Blender 4.4+/5.x layered Actions.
- Build skinned armatures from `SI_FrameBasePoseMatrix` bind poses.
- Preserve bone ancestry across non-bone XSI frames.
- Convert XSI root orientation to Blender's coordinate system.
- Emulate common Battlezone II XSI frame flags.
- Preserve Battlezone material override values as Blender custom properties.

### XSI export

- Export supported Blender scenes back to Battlezone II XSI.
- Export the active collection or selected objects.
- Export meshes, UVs, materials, vertex colors, envelopes, and animation.
- Export Blender 4.4+/5.x layered Actions.
- Export skinned meshes in the armature rest pose.
- Write texture references by file name for game-friendly output.
- Optional generated helper geometry for empty objects and bones.

### PAK support

- Browse XSI assets directly inside Battlezone II `.pak` archives.
- Import a selected XSI asset without manually extracting the whole archive first.
- Extract complete PAK archives from Blender.
- Preserve the archive's directory layout, including the game's 1-based directory table indexing.
- Optionally cache extracted PAK contents.

### Texture support

- Decode Softimage `.pic` textures and save PNG copies during import.
- Convert Battlezone II `.dxtbz2` textures to DDS automatically.
- Search common image formats when resolving XSI texture references.
- Ignore obsolete `//SERVER/...` studio-network texture paths and resolve assets locally instead.
- Cache texture lookups during an import.
- Handle Battlezone II `reflection3` chrome material setup using Blender's current Principled BSDF inputs.

## Blender compatibility

The add-on metadata requires **Blender 4.1 or newer**.

The current `main` branch includes explicit support for the layered Action API introduced in Blender 4.4 and used by Blender 5.x. Import and export regression testing was performed with **Blender 5.2**.

The older `Action.fcurves` path remains for Blender 4.1–4.3, but those versions were not part of the September 2026 regression run.

This repository is packaged as a **legacy Blender add-on**. Blender versions that still support installing legacy add-ons can install the release ZIP or a correctly packaged source checkout.

### Blender Extensions migration

Migration to Blender's current **Extensions** package format is underway on `feature/blender-extension-migration`. The runtime code already uses relative package imports and does not rely on writing into the installed add-on directory, so the main remaining work is packaging and installed-Extension validation.

The original upstream project, `frute94/io_scene_bz2xsi`, does not currently declare a software license. Because this fork contains and modifies that code, a final Extension manifest is intentionally not being published with a guessed license. See [`docs/BLENDER_EXTENSION_MIGRATION.md`](docs/BLENDER_EXTENSION_MIGRATION.md) for the technical migration status and licensing blocker.

## Skinned models and animation

v1.0.10 includes a substantial rewrite of the skinned-model path.

Skinned XSI files are imported with bones placed from their `SI_FrameBasePoseMatrix` bind transforms. Skinned meshes retain their bind transform, and pose bones are animated so each bone follows its XSI frame's animated world matrix.

This also handles cases where plain, non-bone frames exist between bones in the XSI hierarchy.

The deformation path was checked against an independent NumPy implementation of XSI skinning on real Battlezone assets including `mcwing_fly.xsi` and `jak_kill.xsi`.

On export, skinned meshes are written from the armature rest pose so the mesh and exported bone rest matrices remain consistent.

## Installing the latest GitHub Release

The latest packaged release is **v1.0.10**.

1. Download `io_scene_bz2xsi-v1.0.10.zip` from the GitHub Releases page.
2. In Blender, open **Edit > Preferences > Add-ons**.
3. Choose **Install from Disk** and select the ZIP.
4. Enable **BZ2 XSI format**.
5. Use **File > Import > BZ2 XSI / PAK** or **File > Export > BZ2 XSI**.

Do not manually unpack the release ZIP before installing it. The archive already contains the required top-level `io_scene_bz2xsi` directory.

## Manual development install

Clone or download the repository, then place the add-on in an `io_scene_bz2xsi` directory inside Blender's add-ons directory.

The runtime add-on consists of:

- `__init__.py`
- `bz2xsi.py`
- `bz2pak.py`
- `softimage_pic.py`
- `xsi_blender_importer.py`
- `xsi_blender_exporter.py`

Restart Blender or refresh the add-on list, then enable **BZ2 XSI format**.

## Basic usage

### Import an XSI file

Use **File > Import > BZ2 XSI / PAK**, select an `.xsi` file, configure the desired mesh, material, texture, animation, and envelope options, then import.

### Import from a PAK archive

Use **File > Import > BZ2 XSI / PAK** and select a `.pak` file. The import panel exposes the XSI assets found in the archive so one can be selected and imported directly.

### Extract a PAK archive

Use **File > Import > BZ2 PAK Extract**, choose the archive and output directory, and extract the complete file tree.

### Export XSI

Use **File > Export > BZ2 XSI**. Export can operate on the active collection or selected objects and can include mesh data, materials, vertex colors, envelopes, and animation.

## v1.0.10 highlights

The September 26, 2026 Blender 5 compatibility pass fixed several issues that could materially affect real game assets:

- Restored animation import on Blender 4.4+/5.x after the removal of the legacy `Action.fcurves` interface.
- Corrected skinned bind-pose and animated-bone transforms.
- Fixed bone parenting when non-bone frames appear in the hierarchy.
- Fixed object-animation transforms and offset-root coordinate conversion.
- Corrected PAK extraction directory assignment.
- Fixed an XSI envelope-parser skip that could discard a following `AnimationSet`.
- Fixed vertex-color writer output so exported data can be parsed back correctly.
- Fixed duplicated animation keys on export.
- Fixed exporter rest transforms being sampled from the previous object's last animation frame.
- Fixed crashes from empty material slots and generated bone meshes.
- Fixed duplicate child export in **Only Selected Objects** mode.
- Fixed texture paths being exported as full host paths.
- Avoided slow probes of obsolete network texture paths and cached texture lookups.
- Updated Blender 5 normal/material API handling.

## Tests

Two regression-test paths are included under `tests/`.

### Parser corpus

```text
tests/xsi_parse_corpus.py <folder>
```

This parses every XSI file in a supplied folder using the standalone `bz2xsi` parser.

### Blender regression suite

```text
blender -b --factory-startup -P tests/xsi_blender_tests.py -- [tests]
```

The Blender suite exercises importer/exporter behavior, animation, skinning, round trips, PAK import, materials, and known edge cases.

For the September 26 Blender 5.2 validation:

- **21 named regression tests passed.**
- **101 BZCC source XSI files imported with 0 failures.**
- **23 Battlezone II demo XSI files imported with 0 failures.**
- The source corpus included **35 animated** and **4 skinned** assets.

See the test script docstring for the corpus environment variables used by the full-data tests.

## Release packaging

Merging a `release/*` pull request into `main` runs the release workflow. It derives the version from `bl_info["version"]`, creates the matching version tag, validates the runtime files, byte-compiles the add-on, builds and verifies the installable ZIP, and publishes the GitHub Release.

Tag pushes and manual workflow dispatch remain available as fallback release paths.

## Scope

The add-on targets the XSI dialect and asset conventions used by Battlezone II / Battlezone: Combat Commander. It is not intended to be a general-purpose Softimage XSI implementation.

Because the format contains game- and toolchain-specific behavior, round-trip fidelity should still be validated on important production assets before replacing original source files.
