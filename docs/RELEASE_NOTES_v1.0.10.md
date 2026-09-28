# Battlezone II XSI Importer / Exporter v1.0.10

## Summary

v1.0.10 is a compatibility and correctness release focused on Blender 5.x, animation, skinned models, PAK archive handling, exporter reliability, and real-asset regression coverage.

The largest change is the rewritten skinned-model path: XSI bind poses and animated bone transforms now map correctly into Blender armatures, including hierarchies with non-bone frames between bones.

## Highlights

### Blender 5 animation support

- Restores animation import on Blender 4.4+/5.x using layered Actions.
- Adds layered-Action export support.
- Writes XSI animation keys with linear interpolation.
- Fixes object animation transforms that depended on unevaluated `matrix_local` state.
- Corrects root-frame coordinate conversion for offset roots.

### Skinned models

- Builds bones from `SI_FrameBasePoseMatrix` bind transforms.
- Places skinned meshes at their bind transform.
- Animates pose bones from the XSI frame world transforms.
- Preserves bone ancestry across intervening non-bone frames.
- Exports skinned meshes from the armature rest pose.

The deformation path was validated against an independent NumPy implementation of XSI skinning on real Battlezone assets including `mcwing_fly.xsi` and `jak_kill.xsi`.

### PAK archives

- Fixes the PAK file table's 1-based directory indices so extracted files land in the correct folders.
- Stabilizes and caches the archive asset selector used by Blender's import UI.

### XSI parser / writer

- Fixes `read_envelope_list` skipping an extra block and potentially losing a following `AnimationSet`.
- Fixes vertex-color output so exported XSI data can be read back correctly.

### Exporter fixes

- Stops writing each animation key once per channel.
- Samples rest transforms at the correct rest state rather than at the previous object's final key.
- Prevents crashes from empty material slots.
- Prevents crashes when **Generate Bone Mesh** is enabled.
- Prevents duplicate child export in **Only Selected Objects** mode.
- Writes texture references by file name instead of host-system absolute paths.

### Materials and textures

- Fixes Battlezone II `reflection3` chrome material setup against current Principled BSDF inputs.
- Avoids probing obsolete `//SERVER/...` source-art network paths.
- Ignores Blender's unresolved `//` texture directory when the blend file is unsaved.
- Caches texture resolution during import.
- Corrects Blender 5 normal API version handling.

## Validation

The Blender 5.2 regression pass completed with:

- **21 named regression tests passed**
- **101 BZCC source XSI files imported with 0 failures**
- **23 Battlezone II demo XSI files imported with 0 failures**
- Source corpus coverage included **35 animated** and **4 skinned** assets

The skinned-model tests compare Blender's evaluated deformation against an independent NumPy implementation of the XSI skinning transform.

## Installation

1. Download `io_scene_bz2xsi-v1.0.10.zip` from this release.
2. In Blender, open **Edit > Preferences > Add-ons**.
3. Choose **Install from Disk** and select the ZIP.
4. Enable **BZ2 XSI format**.
5. Use **File > Import > BZ2 XSI / PAK** or **File > Export > BZ2 XSI**.

The release ZIP contains the top-level `io_scene_bz2xsi` directory expected by Blender's legacy add-on installer.

## Compatibility

- Add-on metadata requires **Blender 4.1+**.
- Blender 4.4+/5.x layered Actions are supported.
- The v1.0.10 regression run was performed on **Blender 5.2**.
- Blender 4.1–4.3 retain the legacy Action path but were not part of this regression run.
