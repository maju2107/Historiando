# Corrections based on the user's FBX

The original has 114,357 mesh vertices across seven mesh objects. Its character surfaces are closed and entirely quad based. Body and pelvis are already continuous. Head, neck, ears, eyes and eyelids are separate usable parts. Keep them and deform their existing vertices.

The separate rectangular `quadril` object covers an already modeled pelvis. Archive that temporary part, keeping it recoverable, instead of replacing the body beneath it.

At 1 m total height, the head is 0.3135 m wide versus approximately 0.35 m in the front reference. Its height is already close. Broaden it about 12%, reduce its front-to-back depth about 10%, and refine the lower-face landmarks. Preserve the user's rounded cheek and ear surfaces.

The eye surfaces are approximately 0.079 × 0.054 m. Increase their vertical dimension toward 0.085 m, move their centers inward from ±0.093 to approximately ±0.0765 m, and reshape the surrounding existing socket and eyelid area. Keep eye parts separate.

Raise the crotch and knees, fit the long flared legs and large feet to measured front/side widths, and shorten arm reach slightly. The source inspection found three long fingers plus a thumb. Preserve those and add only the missing fourth finger through a local palm patch.

Imported meshes are dense but clean. Trial un-subdivision damaged the head/body quad layout, so it will not be applied to these useful meshes. Prefer preserved all-quad connectivity, mirrored symmetry and modest subdivision preview over destructive reduction.

Checkpoints are immutable. Continue from `progress.json`, never from the older generated project. The original FBX remains in `source/base.fbx` and checkpoint 01 preserves the complete import.
