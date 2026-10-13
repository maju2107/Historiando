# Yara - current working model

Open **yara.blend**. It is checkpoint 54 with file paths reorganized; geometry, UVs, weight paint, the 60-bone rig, all animations and texture pixels are unchanged. Images are embedded, and active material paths point to the canonical PNGs in `../../assets/characters/yara/textures/`.

Select **Yara_PaintedSkin** for current UV painting. Original high-resolution meshes are retained, hidden in CHARACTER. The hair is the exact approved checkpoint-52 painting. Keep that look unless the user explicitly requests a change. Current face paint includes soft blush, pronounced aegyo-sal, lip tint and detailed amber eyes.

Folders:

- `references/`: the four supplied Yara design references.
- `previews/`: current full-body poses, face, chest, shoes and back.
- `validation/`: current painting, rig, engine, hair and organization receipts.
- `progress.json`: current file locations and appearance constraints.

The playable asset remains at `assets/characters/yara/yara_playable.glb`. The island uses `YaraPlayer.tscn`, with the original movement/controller settings. Live ponytail physics covers all nine game actions. See `tools/yara/README.md` for export and checks.

All earlier versions, duplicate authoring aliases, unused model projects, scripts and render history are in `C:\Users\obran\Historiando_Backups\2026-10-12_art_cleanup/original/art/`. No original model file was deleted.
