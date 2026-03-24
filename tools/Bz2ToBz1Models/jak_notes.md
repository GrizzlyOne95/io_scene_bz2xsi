# Jak Notes

`jak_skel.msh` is the better candidate for a BZ1/BZRedux `person` port than `jak_kill.msh`.

Evidence from local files:

- [jak_kill.odf](C:/Users/istuart/Downloads/bz2demofiles/unpakbzd/jak_kill.odf) declares:
  - `classLabel = "i76building"`
  - `geometryName = "jak_kill.xsi"`
  - `animName1 = "eat1"`
  - `animFile1 = "jak_kill.xsi"`
- Raw string inspection of `jak_kill.msh` shows:
  - `hp_dummyroot`
  - `hp_eyepoint`
  - no clear locomotion clip names
- Raw string inspection of `jak_skel.msh` shows:
  - `hp_eyepoint`
  - `idle`
  - `walk`
  - `run`

Interpretation:

- `jak_skel.msh` looks like the gameplay locomotion asset.
- `jak_kill.msh` looks more like a special scripted/placed variant.
- For a BZ1/BZRedux `person` conversion, start from `jak_skel.msh`.
- `jak_kill.msh` can be treated later as an alternate animation/model state if needed.

Current blocker:

- The local parser in [bz2msh.py](C:/Users/istuart/Documents/GIT/io_scene_bz2msh/bz2msh.py) does not fully parse these two files yet.
- `jak_kill.msh` currently trips on mesh block `0x17`.
- `jak_skel.msh` currently trips on mesh block `0x80000`.

Practical path:

1. Extend `io_scene_bz2msh` to handle these mesh block variants.
2. Import `jak_skel.msh` as local meshes.
3. Convert helper names:
   - `hp_eyepoint` -> `GEO 40`
4. Treat the asset as a `person`-class export target in the legacy pipeline.
5. Use [aspilo.mesh](C:/Users/istuart/Documents/Battlezone%2098%20Redux/BZ_ASSETS/common/models/aspilo.mesh) and [aspilo.skeleton](C:/Users/istuart/Documents/Battlezone%2098%20Redux/BZ_ASSETS/common/models/aspilo.skeleton) as behavioral and scale references, not as proof that the source rig already matches pilot bone layout.
