# Current ponytail physics

The current model is `art/yara/yara.blend`. The playable runtime remains `assets/characters/yara/yara_playable.glb`. Three ponytail bones have smooth normalized weights; the root is blended into Head. The fitted scalp, baby hairs, ear curls, bow and gold ring stay attached to Head.

YaraSkin.gd installs YaraHairPhysics.gd under Skeleton3D. The SkeletonModifier3D runs after animation. Its damped spring responds to head translation and angular motion, walking/running cadence, jumping, falling, landing, flips and the other clips. Rotation is bounded and resets on teleport or a long paused step. Animated bone axes and the character's world scale are respected. This behavior is unchanged by the file organization.

Checks cover all nine clips, anchored head/tie, finite bounded motion, settling, turning, teleport reset and actual engine execution after animation. Use `tools/yara/validate_hair.gd`; it writes `art/yara/validation/hair_physics_validation.json`. Current previews are in `art/yara/previews/`. Historical weight/deformation audits and older walking GIFs are preserved in the local backup listed in `art/README.md`.
