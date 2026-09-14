"""Run: blender --background Chibi_Base.blend --python validate_base.py."""

import json
import math
from pathlib import Path

import bpy


def validate_base():
    expected_path = Path(__file__).resolve().parent / "Chibi_Base.blend"
    actual_path = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    assert actual_path == expected_path, (
        "Open the sibling Chibi_Base.blend as Blender's CLI input file first."
    )

    required_collections = {
        "Head", "Hair", "Torso", "Pants", "Shoes", "Accessories", "Body"
    }
    required_objects = {
        "Head_Base", "Hair_Scalp_Cap", "Hair_Ponytail_Core", "Torso_Jacket",
        "Pants_Wide_Leg_L", "Pants_Wide_Leg_R", "Shoe_Upper_L", "Shoe_Upper_R",
    }

    scenes = [
        scene for scene in bpy.data.scenes
        if required_objects.issubset({obj.name for obj in scene.objects})
    ]
    assert len(scenes) == 1, "Expected exactly one complete character scene."
    scene = scenes[0]
    assert bpy.context.scene == scene, "The character scene must be active."
    assert scene.camera is not None and scene.camera.type == "CAMERA"
    assert scene.camera.name in scene.objects, "Active camera is absent from scene."

    scene_collections = {collection.name for collection in scene.collection.children_recursive}
    assert required_collections.issubset(scene_collections), (
        "Missing logical collections: "
        + ", ".join(sorted(required_collections - scene_collections))
    )
    for name in required_collections:
        assert len(bpy.data.collections[name].all_objects) > 0, name
    for name in required_objects:
        assert scene.objects[name].type == "MESH", name

    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    curves = [obj for obj in scene.objects if obj.type == "CURVE"]
    vertices = 0
    polygons = 0
    for obj in meshes:
        mesh = obj.data
        assert len(mesh.vertices) > 0 and len(mesh.polygons) > 0, obj.name
        assert len(mesh.materials) > 0, "Missing material: " + obj.name
        assert all(material is not None for material in mesh.materials), obj.name
        assert all(
            math.isfinite(component)
            for vertex in mesh.vertices for component in vertex.co
        ), "Nonfinite mesh coordinates: " + obj.name
        assert all(
            math.isfinite(polygon.area) and polygon.area > 1.0e-12
            for polygon in mesh.polygons
        ), "Degenerate raw face: " + obj.name
        vertices += len(mesh.vertices)
        polygons += len(mesh.polygons)

    soles = [
        obj for obj in meshes if obj.name.startswith("Shoe_Flat_Sole_")
    ]
    assert len(soles) == 2, "Expected two shoe soles."
    sole_minimum_z = {}
    for obj in soles:
        minimum_z = min((obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices)
        assert abs(minimum_z) < 1.0e-5, "Shoe sole is not on Z=0: " + obj.name
        sole_minimum_z[obj.name] = minimum_z

    packed_references = [
        image.name for image in bpy.data.images
        if image.source == "FILE" and image.packed_file is not None
    ]
    report = {
        "blend_reopened": True,
        "blend_file": str(actual_path),
        "active_scene": scene.name,
        "active_camera": scene.camera.name,
        "logical_collections": sorted(required_collections),
        "mesh_objects": len(meshes),
        "curve_objects": len(curves),
        "raw_vertices": vertices,
        "raw_polygons": polygons,
        "degenerate_raw_faces": 0,
        "shoe_sole_minimum_world_z": sole_minimum_z,
        "packed_reference_count": len(packed_references),
        "packed_reference_images": packed_references,
    }
    report_path = expected_path.with_name("validation.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("CHIBI_BASE_VALIDATED " + json.dumps(report))


if __name__ == "__main__":
    validate_base()
