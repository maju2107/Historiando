# Yara - current playable character

The current authoring model is **art/yara/yara.blend** (checkpoint 54). Its approved checkpoint-52 hair and current face painting are preserved. Original high-resolution meshes, the UV-painted game skin, 60-bone rig, normalized weights and three authoring RigCheck actions remain in that file.

This folder contains the current game asset: `yara_playable.glb`, `YaraSkin.tscn`, the animation-path/material adapter `YaraSkin.gd`, live ponytail physics `YaraHairPhysics.gd`, and the canonical PNGs in `textures/`. The GLB has 112,484 triangles, 16 material surfaces, a 60-joint skin and at most four normalized influences. Images are embedded. See [UV_PAINT.md](UV_PAINT.md) and [HAIR_PHYSICS.md](HAIR_PHYSICS.md).

Yara replaces Gobot only in `_testes/cenario_ilha/CenarioIlha.tscn` via `YaraPlayer.tscn`. The controller, camera, collisions and movement settings remain unchanged. The nine clips are Idle, Walk, Run, Jump, Fall, Flip, VictorySign, EdgeGrab and WallSlide. The existing controller uses the first five; the other clips are available to gameplay through the same AnimationPlayer. Existing project bindings have not been changed.

Current checks and captures: `tools/yara/`. Reports: `art/yara/validation/`. Previews and design references: `art/yara/`. The archive location and original inventories are documented in `art/README.md`.

Animation attribution and the historical GDQuest CC-BY-4.0 license are included here. [gobot_provenance.json](gobot_provenance.json) records the exact historical binary match. Character geometry and supplied reference art are user project assets.

The folder cleanup changed authoring paths and documentation; game mesh bytes, textures, rig, movement scripts and hair physics were checksum-verified unchanged. Current engine and spring checks pass. Existing unrelated whole-project rock_m.fbx import and shutdown resource-leak messages remain recorded in the backup logs.
