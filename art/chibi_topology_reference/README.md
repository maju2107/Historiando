# Chibi reference base

Open **Chibi_Reference_Base.blend** in Blender. The editable character is selected in a front orthographic view, with visible topology. The model follows the proportions, lowered arms, rounded featureless head, narrow waist, long legs, wide flat feet and simplified hands in the supplied September 12 reference.

- One continuous, closed surface: **807 vertices, 805 quad faces, 1,610 triangles**.
- Front is **-Y**; up is **Z**. Height is 4.04 Blender units, with both soles at Z = 0.
- UV unwrapped, neutral gray material, no rig.
- Vertex groups select the head, torso, arms, hands and legs. An optional subdivision modifier is included but disabled to retain the reference's low-poly appearance.
- The source JPEG is packed into the hidden reference collection. The generator and short instructions are also embedded as Blender Text datablocks.

The topology is reconstructed from the image; it is not an exact recovery of the original mesh. The image labels its original as 818 polygons / 1,636 triangles. This reconstruction uses 805 quads / 1,610 triangles and prioritizes the visible shape. The hands have a thumb and two finger groups, matching the simplified inset rather than a fully articulated five-finger hand.

## Files

- `Chibi_Reference_Base.blend`: editable Blender project.
- `Chibi_Reference_Base.glb`: model-only export for Godot and other glTF applications.
- `Chibi_Reference_Base.obj` + `.mtl`: model-only OBJ with quad faces and UVs.
- `preview.png`: front / side / back / hand overview.
- `front.png`, `side.png`, `back.png`, `three_quarter.png`, `hand_detail.png`: individual renders.
- `validation.json`: saved-project geometry checks.

The studio collection contains render-only edge curves, a camera and lights. It is hidden in the viewport. The curves are separate from the actual mesh and are excluded from both model exports. This folder has `.gdignore` so preview and source files are not imported into the existing game project; copy the GLB into the game's assets folder when ready to use it.

## Rebuild and verify

Created and checked in Blender 5.2.1 LTS. Run the included scripts with Blender:

```text
blender --background --threads 6 --python-exit-code 1 --python build_model.py
blender --background --threads 6 --python-exit-code 1 --python validate_model.py
```

The first command rebuilds and renders the project, overwriting generated files in this folder. Save manual edits under a different filename first. `make_preview.ps1` assembles the rendered overview using Windows System.Drawing.

Validation reopens the saved blend and checks connectivity, manifold edges, quad faces, finite geometry, face area, bilateral symmetry, nonadjacent face intersections, positive volume, UVs, packed reference and exported files.
