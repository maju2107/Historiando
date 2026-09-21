# Active task: seven checkpoint milestones

User requests a faithful editable Blender chibi reconstruction, continuing existing work, with numbered immutable .blend files after each milestone. Never restart the old procedural full-model builder to resume this project. Latest state is in progress.json and RESUME.md.

1. References and quantitative analysis.
2. Body/head silhouette review and fitting of existing mesh.
3. Production topology: editable half and Mirror before Subdivision.
4. Face and ears: fix eye fit, match rounded helix/concha and small nose/mouth.
5. Hands and feet: user explicitly requires FOUR fingers plus thumb on each hand, overriding the earlier three-finger interpretation; maintain continuous body and quad topology.
6. Validate all views and compare quantitatively/visually; refine obvious errors.
7. Final topology cleanup, checks, renders, exports and final save.

Required final: output/chibi_female_base.blend, 1 m tall, feet Z=0, center X=0, front -Y; CHR_Body with Mirror and Subdivision2; separate named eyes/lashes/brows, disabled aligned reference collection and four orthographic cameras. Keep original reference files unchanged. Configurable dimensions/alignment are in scripts/config.py. Source script must remain modular. Each modeling stage must render and be visually inspected.

Current baseline was imported from ../Chibi_Feminina.blend (2026-09-20), already 2320 body quads with a quad-grid crown, 16-segment eye rims, orderly legs and three long fingers plus thumb. It is not a primitive model. Current project scripts load preceding checkpoints and edit them in place.

Important pending issues:
- M4: old eyeballs protrude slightly through lower outside eyelid/cheek, visible as a thin broken rim in clay view. Fix eye components based on current saved geometry; don't rebuild the whole head. Previous planned ellipse in legacy coordinates: centerY -.468, X radius .164, Z radius .156, forward depth .076, Y slope .16*side*relativeX. Convert using scene import_scale/import_floor, then account for milestone2 silhouette transform curves in renders/m02_measurements.json. Eye socket center old raw head(cx=±.268, z2.945), hc=(x*1.09,y*1.03,2.30+(z-2.465)*1.30/1.135). Can also fit from actual eyelid vertex bounds.
- M4: milestone2 currently uses neutral Y offset at z1.001; top of skull may need posterior shift continued from .97 sample, because reference skull center is behind neck. Inspect side before changing.
- M5: replace only hands beyond existing 8-vertex wrist on positive half body. Current groups Arm.L, Hand / palm.L, Hand / webs.L, Finger / {thumb,index,middle,little}.L. New palm can use 20-vertex cross section (bottom9, rear-side1, top9 reversed, front-side1), four rings; wrist8->palm20 with index groups [(0,1,2),(3,4,5),(6,7,8),(9,),(10,11,12),(13,14,15),(16,17,18),(19,)] makes all quads. Thumb socket in rows0,1 columns18,19; four finger roots each consume2 front edges and share web mids. Keep body and wrist intact. Mirror supplies other hand. Rounded finger rings8 and quad tips. Target wristX~.29, palm length~.10, longfinger lengths .05–.065, palm halfYwidth~.055, thumb short/chubby.
- Normal final check must account for half-mesh seam (open control seam intentional) and evaluate Mirror alone for full control mesh, then Mirror+Subsurf for final. Check quads, normals, symmetry, manifold edges, coincident vertices, self intersections, UVs, parts and exports. Existing ../validate_character.py can inform implementation but references old names and full mesh assumptions.
- Material: gray clay, dark wire, dark neutral world. helpers.rebuild_wire applies Mirror to temporary proxies before smooth_preview.make_wire_overlay so full control-edge display stays correct.

Commands (PowerShell):
```
& 'C:\AI\Blender\blender-5.2.1-windows-x64\blender.exe' --background --threads 6 --python-exit-code 1 --python art\chibi_female_reference\project\scripts\build_character.py -- --milestone N *> art\chibi_female_reference\project\milestone_0N.log
```
PowerShell may report exit1 from harmless Blender deprecation warnings; inspect log for traceback and CHECKPOINT SAVED. Helpers refuse overwriting numbered checkpoints. Need implement milestones4–7 in modeling.py and likely hands.py/validation.py.

User's latest instructions prioritize image fidelity over speed. Source images measure about2.76 heads tall (documented in analysis.json), so don't impose generic3.5-head proportions. Reference source SIDE faces right; CAM_Right views opposite side, so compare against a horizontally flipped reference side image.

No new agents unless explicitly authorized under active developer instruction. Earlier agents finished most work; pending old thumbs-only suggestion is superseded by the five-digit hand requirement.

Unrelated Godot files have user edits; do not modify or revert them.
