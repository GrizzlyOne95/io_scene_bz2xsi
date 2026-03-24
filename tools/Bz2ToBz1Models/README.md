# BZ2 To BZ1 Models

The main model-port problem is not mesh serialization. The local toolchain already has:

- BZ2 XSI import in [io_scene_bz2xsi](/c:/Users/istuart/Documents/GIT/io_scene_bz2xsi)
- BZ1 legacy `.geo/.vdf/.sdf` export in [BZ98RBlenderToolKit](/c:/Users/istuart/Documents/GIT/BZ98RBlenderToolKit)

The difficult step is translating BZ2 helper frames like `hp_*` into legacy GEO role IDs.

## Current hardpoint map

`[high confidence]`

- `hp_eyepoint*` -> `40` `EYEPOINT`
- `hp_com*` -> `42` `COM`
- `hp_gun*`, `hp_weapon*` -> `70` `WEAPON_HARDPOINT`
- `hp_cannon*` -> `71` `CANNON_HARDPOINT`
- `hp_rocket*` -> `72` `ROCKET_HARDPOINT`
- `hp_mortar*` -> `73` `MORTAR_HARDPOINT`
- `hp_special*` -> `74` `SPECIAL_HARDPOINT`
- `hp_fire*`, `flame_*`, `hp_flame*` -> `75` `FLAME_EMITTER`
- `hp_smoke*`, `hp_moresmoke*` -> `76` `SMOKE_EMITTER`
- `hp_dust*` -> `77` `DUST_EMITTER`
- `hp_light*` -> `38` `HEADLIGHT_MASK`

`[medium/low confidence]`

- `hp_emit*`, `hp_trail*` -> `76` `SMOKE_EMITTER`
  These are generic particle anchors in BZ2. Smoke is the safer BZ1 default than dust.
- `hp_shield*`, `hp_hand*`, `hp_pack*` -> `74` `SPECIAL_HARDPOINT`
  BZ2 inventory-slot semantics do not have a clean BZ1 equivalent.
- `hp_powerup*`, `hp_vehicle*`, `hp_spray*` -> `74` `SPECIAL_HARDPOINT`
  These need ODF-aware review.

## Helper tool

[hardpoint_name_map.py](/c:/Users/istuart/Documents/GIT/io_scene_bz2xsi/tools/Bz2ToBz1Models/hardpoint_name_map.py) classifies helper names and tells you which ones are safe to auto-map.

Examples:

```powershell
python tools\Bz2ToBz1Models\hardpoint_name_map.py hp_gun_1 hp_cannon_1 hp_light_1
```

```powershell
Get-Content names.txt | python tools\Bz2ToBz1Models\hardpoint_name_map.py --tsv
```

## What still needs scripting

- Turn imported BZ2 helper empties into legacy-exportable helper meshes.
- Rename exported objects into valid legacy GEO slot names.
- Apply the inferred GEO role IDs onto `GEOPropertyGroup.GEOType`.
- Leave `hp_light*` and other ambiguous helpers in a review report instead of forcing them.
