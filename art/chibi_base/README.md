# Chibi character base

Open `Chibi_Base.blend` in Blender. The active scene contains the character, camera, lights, and floor.

The simplified model follows the supplied character sheet: a large rounded head, voluminous brown ponytail, white cat-ear headband, purple jacket and wide trousers, and golden slip-on shoes with flat soles.

Editable parts are organized into `Head`, `Hair`, `Body`, `Torso`, `Pants`, `Shoes`, and `Accessories`. `Character_Root` moves the character as a whole. The drawing is packed inside the blend under the initially hidden `Reference` collection.

This is a sculpting base with separate, overlapping components. It is not rigged. Keep an original copy before joining or voxel-remeshing parts for continuous sculpting. Bevel and hair-cap thickness modifiers remain editable.

Previews: `front.png` and `three_quarter.png`.

The project was created, rendered, and reopened successfully in Blender 5.2.1 LTS. `validation.json` records checks for materials, finite geometry, nondegenerate faces, object organization, the active camera, and flat shoe bases. The generator uses Blender 3.x/4.x-compatible API choices, but those versions were not available for runtime testing.

`build_chibi.py` is included both alongside the model and as a Blender Text datablock. Run the external script with Blender's `--python` argument; add `-- --render` to regenerate previews. Rebuilding overwrites the generated blend and previews, so save manual edits under a different name first.
