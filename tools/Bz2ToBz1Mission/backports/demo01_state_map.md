# `demo01` Lua Backport Notes

Source mission DLL:
`C:\Users\istuart\Documents\GIT\BZ2_Source\_analysis\BZ2_1.3.7_a130DLLSource\BZ2 1.3.7-a130 Dll Source Code\Missions\demo01\demo01.cpp`

## Practical Porting Approach

The mission script can be backported to Lua because the important mission APIs are already exposed in Lua:

- `BuildObject`
- `Goto`
- `Attack`
- `Follow`
- `Service`
- `AudioMessage`
- `SetObjectiveOn`
- `SetObjectiveName`
- `AddObject`
- `DeleteObject`

The main incompatibility is the intro/config UI layer:

- `IFace_CreateCommand`
- `IFace_Exec`
- `IFace_Activate`
- `IFace_GetInteger`
- `IFace_SetInteger`
- `IFace_CreateString`

For a BZ1 Lua port, the simplest path is:

1. Skip the setup/config screens.
2. Skip or simplify the opening cinematic.
3. Start from the playable mission segment, equivalent to `missionState = 10`.

## Mission State Map

- `0`: Setup intro/config screens.
- `1`: Idle on intro screen, spawn ambient animals.
- `2`: Idle on config screen.
- `3`: Cleanup UI state and restore saved objects.
- `4`: Opening dropship/crash cinematic.
- `5`: Focus on animal after crash.
- `6`: Pull camera away from animal.
- `7`: Land dropship and deploy.
- `8`: Spawn service truck.
- `9`: Spawn mortar bikes and assign initial orders.
- `10`: Main combat. Clear route to crash site. Spawn APC/supplies if player is low.
- `11`: Move player to crash site. Spawn pilot and attack animals.
- `12`: Rescue sequence. Spawn pilots, tug behavior, clear attacking animals.
- `13`: Scuttle/dustoff transition.
- `14`: Move to dustoff site. Final ambush.
- `15`: Mission success.
- `16`: End/cleanup.

## Helper Functions To Preserve

- `CommandMortarBikes()`
  Rotates wingman targets toward live turrets and advances the mission if no turret targets remain.

- `DoService(truck)`
  Makes the service truck repair low-health or low-ammo wingmen and returns it to follow mode.

- `CheckLoseConditions()`
  Fails on dead service truck in early mission or dead tug at any point.

- `FindTurrTarget()`
  Picks the next untargeted turret first, then any remaining turret.

- `FindSentTarget()`
  Returns the first living friendly target for enemy sentries.

- `SkipCin()`
  Useful for Lua as an explicit "start playable segment now" bootstrap.

- `SetDifficulty(object, level)`
  BZ2 maps difficulty levels `0,1,2` to skills `0,1,3`.

## Recommended Backport Scope

First pass:

- Start in playable state.
- Spawn friend bikes, service truck, tug, crashsite objective.
- Port `CommandMortarBikes`, `DoService`, `CheckLoseConditions`, and wave spawning.
- Port states `10` through `15`.

Second pass:

- Recreate cinematic states `4` through `9`.
- Replace the old IFace setup flow with Lua-friendly options or fixed defaults.

## Object/Path Dependencies From `demo01.bzn`

Important object names from the parsed map:

- `turr0` .. `turr8`
- `guntow2`
- `spawn`, `spawn2`, `spawn3`, `spawn4`
- `crashSite`
- `service`
- `animal0` .. `animal4`
- `apc1`, `apc2`
- `dustoff`

Important path names from the parsed map:

- `spawn`
- `spawn2`
- `spawn3`
- `spawn4`
- `service`
- `animal0` .. `animal4`
- `apc1`
- `apc2`
- `dustoff`
- `crashSite`

## Current Output

A starter Lua scaffold lives at:
`tools\Bz2ToBz1Mission\backports\demo01.lua`

The current Lua backport now ports gameplay states `10` through `15` and still intentionally starts from the playable path instead of trying to emulate the IFace screen flow.

Known compromises:

- Opening IFace/config states `0` through `9` are still skipped.
- DLL-only helpers such as `SetGroup`, `LookAt`, `SetAnimation`, and `SetAvoidType` are used only when the runtime exposes them.
- The animal-eating transition uses a time fallback when animation-frame queries are unavailable.
