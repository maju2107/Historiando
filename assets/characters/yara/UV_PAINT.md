# Current UV painting

Open `art/yara/yara.blend` and select Yara_PaintedSkin. Its YaraPaintUV layout is the existing packed layout, with separate image sets. Pick the material's Albedo image before using Texture Paint. Original high-resolution sculpt meshes remain hidden in CHARACTER.

Five sets (SkinEyes, Hair, Outfit, Shoes, Accessories) have 2048-pixel Albedo, Roughness, Normal and UV wire PNGs. The chest-underlap set is 256 pixels. All 24 editable maps are in `assets/characters/yara/textures/`. Images are also packed in the blend and embedded in the GLB. Active authoring image paths are relative to this canonical texture folder.

Hair uses the exact approved checkpoint-52 shader and textures, including its normal map and strength. The user called that hair perfect; retain its look unless explicitly asked to change it. Current face painting has soft cheek/nose blush, a nose highlight, warm eyelid shading, pronounced aegyo-sal, subtle lip tint, brown oval pupils and amber crescents/glints. Clothing and shoes retain checkpoint-53 painting, with fine purple zebra markings, gold uppers, shoe blush and cream soles.

Geometry, UVs, weight paint and animation curves are unchanged by organization. Current previews are in `art/yara/previews/`; receipts are in `art/yara/validation/`. All older models, duplicate working files, texture kits and painting scripts are in the external local archive listed in `art/README.md`.
