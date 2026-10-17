# Kai — editable character source

Open **kai.blend** for the current character. The source includes the base character mesh and rig, separate clothing and accessories, material shaders, studio lights, camera, and the packed reference image.

The design follows the user-supplied Kai turnaround: warm brown skin, relaxed amber eyes, thick dark eyebrows, pale layered waves and nape hair, a sleeveless violet top, golden camouflage cargo shorts, rear-facing purple elbow protectors, and purple monster boots with ivory laces and cream engraved soles.

## Current review

- `previews/front.png`, `three_quarter.png`, `side.png`, and `back.png` are rendered from this character.
- The purple guards sit on the back (+Y in the rest pose) of the elbows; brown straps wrap around the arms.
- The marked crown, fringe, outer side and nape locks have rounded cross-sections with roughly twice the earlier depth. Added jaw and neck curls follow the user's marked silhouette. Crown locks sit lower and slope down around the skull, following the user's gravity correction.
- Hair locks retain tapered ends and regular UV strips. They remain independent subdivision meshes for editing. `hair_volume_validation.json` records the revised lock dimensions and confirms the non-target meshes were preserved.
- Eyebrows are thicker than the initial Kai pass.
- Added temple bridges, behind-ear sweeps, short jaw flicks, a center-part curl and a small crown curl in the user's marked areas. The rear's 28 crossing short-lock objects were replaced by a continuous backing and nine separated long locks; nape roots meet the rear hair surface. See `hair_cleanup_validation.json` for the scoped preservation check.
- Added a finer foreground layer on the fringe, a thin curled wisp beside the eyebrow, extra cheek curls and four fine rear wisps. The exposed lower rear backing is shaped into 13 tapered tufts, filling the smooth band above the nape without another crowded row of separate thick locks.
- Hair uses irregular UV-aligned pearl/lavender fiber strokes, subtle surface relief and directional highlights. The game skin now has a baked 4K color atlas and 2K roughness/metallic atlas; the editable source retains the material nodes.
- The central fringe and part were lowered to reduce the visible forehead. Upper eyelids are now shaped directly in the existing body eye-socket loops; the separate skin patches were removed. The eyebrows have gentler, tapered arcs. `face_refinement_validation.json` lists the local eye-loop edits and verifies that all other body control vertices were preserved. `previews/face.png` shows the close-up.
- `validation.json` records a separate Blender reopen and mesh/weight checks. Yara's subsequently authorized facial revisions are verified by the scoped source comparisons in `art/island_intro/facial_source_validation.json`, with exact source/runtime hashes.
- The marked existing side lock now extends into the crown to cover the small temple gap. Its lower curl and all other meshes were preserved in that pass; see `side_lock_validation.json`.
- The tank has sloping shoulders, rounded armholes, a thin cotton edge and a hem tucked inside the waistband. Its neutral shape was settled with cloth simulation to create soft folds. The brown elbow wraps are now broad, flat woven bands; the rear-facing purple pads are wider and thinner, with flat printed spots.
- The user's manually edited right eyebrow is preserved exactly and mirrored onto the left. The ahoge is a single tapered hooked lock rooted in the crown.
- Each eye now has one continuous, thicker cartoon-ink surface band joining the upper lid around the outer corner to the lower outer half. The upper section is approximately 9 mm wide and the lower section 5 mm, with tapered ends. The smooth outline is clipped directly against the evaluated facial surface to keep the outer corner solid and prevent folded overlap. Shrinkwrap after head deformation maintains contact, and thin solidification embeds its back edge into the skin. `leg_lash_validation.json` records connectivity and measured contact distances. `previews/eyelashes.png` includes profile inspection views with hair temporarily hidden; the saved model keeps its complete hair.
- The exposed knee profiles between the shorts and boots have been softened on both legs. Only the local cross-section positions were adjusted; joint-loop topology, vertex heights and skin weights were retained. `previews/legs.png` shows the profile before and after this local correction.
- The cargo shorts' collapsed bottom loops were replaced by continuous turned hems, with attached stitching, fitted soft pocket patches and flaps, and projected front pocket/fly seams. Camouflage uses one consistent rest-space scale across the waistband, shorts and pockets. The boot finish adds folded cuffs, lining, shaped tongues, ring eyelets, flat cotton laces and continuous recessed tooth grooves spaced along the sole perimeter. See `finish_validation.json`, `previews/finish_details.png`, and `previews/lower.png`.

## Cloth physics

The tank's modifier order is torso armature, **Soft cotton cloth physics**, smooth subdivision, then thin solidification. The **Cloth anchors** group supports the neckline, shoulders and tucked waist. The skinned body is the collision surface. Play sequentially from frame 1 to simulate; the working range is frames 1–72. The neutral drape is stored in the editable mesh, so the saved model opens with the intended shape even before simulation.

`cloth_validation.json` records the settling pass and a separate 72-frame test with torso leaning and opposing arm motion. `previews/cloth_motion.gif` shows sampled frames from that test. The live cloth modifier is for Blender authoring; the game uses the stored drape with painted torso/shoulder deformation.

## Scope

The editable source now has normalized joint/clothing paint, twelve animation actions and seventeen facial shape keys. `KAI_Base_Body` controls the facial keys; linked eyebrows, eyelids/lashes and oral pieces follow it through drivers. The eyes retain their volume. Reflowed concentric lip loops and soft outer support replace the pinched mouth, with an actual dark cavity, dental band and rounded tongue. The game skin has extra local mouth resolution and fairing, and fitted lash correctives for eyelid motion. The elbow cushions curve around the arms and blend between upper arm, elbow-volume helper and forearm. Boot shafts follow the shins, with a foot/ankle transition below; locomotion has restrained ankle rotation and hinge-only elbow flexion.

The non-destructive **Concealed skin inside boots** display mask keeps covered skin out of the render. Disable it to edit the original feet; their control geometry and paint remain intact. The game mesh omits those concealed faces.

The game actor is `assets/characters/kai/KaiActor.tscn`, backed by `kai.glb`. It appears after the island close-up in `CenarioIlha.tscn`. Yara remains the playable character. Locomotion clips are Idle, Walk, Run, Jump, Fall and VictorySign; cinematic clips are Talk, Explain, Correct, Shrug, Point and React. The game uses shape-driven mouth movement, expressions and blinks in response to the Dialogic timeline. It does not include recorded voice audio.

`previews/rig/` contains Godot deformation views. `runtime_motion_validation.json`, `joint_motion_validation.json`, `footwear_coverage_validation.json`, `facial_pad_validation.json` and `validation.json` record engine/source checks. Cutscene and expression previews are in `art/island_intro/previews/`; mission and skip checks are in `art/island_intro/kai_validation.json`. This is a reviewed cinematic NPC export, without a mobile performance or LOD certification.

## Continued editing and backups

Use `kai.blend` as the starting point for manual edits. `tools/kai/build.py` records construction from the donor base; rerunning it rebuilds the generated source and does **not** preserve subsequent manual edits. `tools/kai/validate.py` only reads the source and writes the validation report.

`tools/kai/refine_hair_volume.py` records the marked hair-volume pass and gravity correction. Its saved pre-pass source is outside the repository; it must not be rerun over later manual changes without updating that input.

`tools/kai/clean_hair_layers.py` records the current gap-fill and rear cleanup. It reads the saved pre-cleanup source outside the repository. Use the current `kai.blend` for subsequent edits rather than rerunning earlier construction passes.

`tools/kai/hair_detail_pass.py` records the latest fine-strand, lower-band and material pass. It reads its own pre-pass backup outside the repository, so it must not be rerun after new manual edits without updating that input.

`tools/kai/refine_forehead_eyelids_brows.py` records the latest forehead/eyelid/brow pass. Its input backup is `C:/Users/obran/Historiando_Backups/kai_face_2026-10-16/kai_before_forehead_lids_brows.blend`; use the current model for future edits.

`tools/kai/fit_marked_side_lock.py` records the local hair join correction. `tools/kai/refine_cloth.py` records the shirt and elbow-wrap reconstruction. Both read external pre-pass checkpoints; do not rerun them over later manual changes. `tools/kai/test_cloth_motion.py` runs the isolated motion review; its `--settle` option also writes a new neutral drape to the source. The pre-clothing backup is in `C:/Users/obran/Historiando_Backups/kai_cloth_2026-10-16/`.

`tools/kai/refine_finish.py` records the eyebrow, ahoge, eyelash, cargo and boot finish pass. Its input is the user's saved model from immediately before that pass, preserved as `C:/Users/obran/Historiando_Backups/kai_finish_2026-10-16/kai_before_finish.blend`. Use the current `kai.blend` for further manual edits; rerunning this checkpoint script discards later edits. `tools/kai/render_review.py` renders the current source into an external scratch folder for inspection.

`tools/kai/fit_cartoon_lashes.py` replaces the earlier floating lash cords with the fitted ribbons. Its input checkpoint is `C:/Users/obran/Historiando_Backups/kai_lashes_2026-10-16/kai_before_lash_fit.blend`; do not rerun it over later manual changes. `tools/kai/render_lash_review.py` renders close-ups and measures the evaluated lash surfaces against the eyelid mesh.

`tools/kai/smooth_legs_connect_lashes.py` records the latest knee-profile smoothing and unified thicker lash strips. Its pre-pass checkpoint is `C:/Users/obran/Historiando_Backups/kai_leg_lash_2026-10-16/kai_before_leg_lash.blend`. Use the current source for future manual edits.

The pre-refinement source and scratch files are stored outside the repository in:
`C:/Users/obran/Historiando_Backups/kai_work_2026-10-15/`

## References and provenance

- Character design: user's `Turnaround de Personagem Chibi em Três Vistas.png`, copied to `references/kai_turnaround.png` and packed into the Blender file.
- Editable body/face and rig: cloned from the user's existing `art/yara/yara.blend`. The later expression pass updates both characters' faces at the user's request; original hair, clothing, accessories, limbs and animation actions are preserved.
- Hair workflow references supplied by the user: [ItsPaulTodd — How to create FAST Stylized Hair/Fur in Blender 4.0](https://www.youtube.com/watch?v=ethg2nYSjqg), and [JAEY 3D — Sitting Chibi Hair Tutorial](https://www.youtube.com/watch?v=vUEPHy3QQF4). Captions were reviewed for path/profile shaping, tapered ends, broad initial masses, layered sections, and multi-view refinement. No tutorial meshes were downloaded or incorporated.
- The inherited rig and six locomotion actions have Gobot/GDQuest and project Yara adaptation provenance. See `ATTRIBUTION.md` and `GDQuest-LICENSE.txt`. The six dialogue gestures and facial shapes were authored for Kai.
