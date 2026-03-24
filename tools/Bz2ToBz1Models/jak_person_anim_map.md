# Jak Person Animation Map

The important detail for BZRedux `person` assets is slot index, not source clip name.

The porter in [bzportmodels.py](C:/Users/istuart/Documents/GIT/BZ98RBlenderToolKit/bz98tools/bzrmodelporter/bzportmodels.py) loads person animations by index and then exports them under hardcoded BZR names:

- `0` -> `stand2Kneel`
- `1` -> `kneel2stand`
- `2` -> `idle`
- `3` -> `fireRecoilSniper`
- `4` -> `runForward`
- `5` -> `runBackward`
- `6` -> `runLeft`
- `7` -> `runRight`
- `8` -> `death1`
- `9` -> `idleParachute`
- `10` -> `landParachute`
- `11` -> `jump`

That means the `jak` source clips do **not** need to be renamed to `aspilo` clip names internally. They need to be assigned to the right slot indexes before export.

## Available `jak_skel.msh` clips

Recovered by [inspect_msh_strings.py](C:/Users/istuart/Documents/GIT/io_scene_bz2xsi/tools/Bz2ToBz1Models/inspect_msh_strings.py):

- `idle`
- `walk`
- `jump`
- `death`
- `attack1`
- `attack2`
- `attack3`
- `attack4`
- `eat1`
- `eat2`

## Proposed minimum viable slot map

This is the lowest-risk map that preserves the creature's own transforms while satisfying the BZR person contract.

| Slot | Exported BZR Name | Proposed `jak` source |
|---|---|---|
| 0 | `stand2Kneel` | `idle` |
| 1 | `kneel2stand` | `idle` |
| 2 | `idle` | `idle` |
| 3 | `fireRecoilSniper` | `attack1` |
| 4 | `runForward` | `walk` |
| 5 | `runBackward` | `walk` |
| 6 | `runLeft` | `walk` |
| 7 | `runRight` | `walk` |
| 8 | `death1` | `death` |
| 9 | `idleParachute` | `idle` |
| 10 | `landParachute` | `idle` |
| 11 | `jump` | `jump` |

## Why this works

- `jak` has no obvious crouch/sniper/parachute set, so those slots should be harmless duplicates or substitutes.
- The locomotion slots `4..7` are the critical ones for gameplay feel. Reusing `walk` in all four directions preserves the creature motion even if strafing/backpedal are not distinct.
- `attack1` is the closest available substitute for `fireRecoilSniper`.
- `death` and `jump` map directly.

## Better version later

If we get full `.msh` parsing working:

- evaluate whether `attack2..4` contain cleaner one-shot transitions for slots `0`, `1`, or `3`
- decide whether `eat1/eat2` are useful as ambient alternates
- add creature-specific directional locomotion if hidden clips exist and the raw string scan missed them

## Practical consequence

For `jak`, the pipeline should be:

1. import `jak_skel.msh`
2. assign the above indices in the legacy scene `AnimationCollection`
3. export as a `person`-mode VDF/BZR asset
4. let the porter emit the required BZR person animation names automatically
