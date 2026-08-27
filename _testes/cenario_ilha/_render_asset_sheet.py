import bpy
import math
import os
import sys
from mathutils import Vector


ROOT = os.path.join(os.getcwd(), "assets", "models", "creative_trio")
GROUPS = {
	"Trees02Selected": ["Tree_001", "Tree_002", "Tree_003", "Tree_004", "Tree_008", "Tree_009", "Tree_011", "Tree_017", "Tree_029", "Tree_030", "Tree_037", "Tree_038", "Tree_039"],
    "Trees01": ["Tree_001", "Tree_002", "Tree_003", "Tree_004", "Tree_005", "Tree_006", "Tree_007", "Tree_008", "Tree_009", "Tree_010", "Tree_011", "Tree_012", "Tree_013", "Tree_014", "Tree_015", "Tree_016", "Tree_017", "Tree_018", "Tree_019", "Tree_020", "Tree_021", "Tree_026", "Tree_027"],
    "Trees02": ["Tree_001", "Tree_002", "Tree_003", "Tree_004", "Tree_008", "Tree_009", "Tree_010", "Tree_011", "Tree_015", "Tree_016", "Tree_017", "Tree_018", "Tree_022", "Tree_023", "Tree_024", "Tree_025", "Tree_029", "Tree_030", "Tree_031", "Tree_032", "Tree_036", "Tree_037", "Tree_038", "Tree_039"],
    "Plants02": ["Plant_003", "Plant_004", "Plant_005", "Plant_006", "Plant_007", "Plant_008", "Plant_010", "Plant_013", "Plant_020", "Plant_027", "Plant_028", "Plant_030", "Plant_037", "Plant_047"],
    "Plants01": ["Cylinder", "Cylinder_002", "Plane", "Plane_001", "Plane_003", "Plane_004", "Plane_006", "Plane_010", "Plane_014", "Plane_015", "Plane_018", "Plane_019", "Plane_021", "Plane_023", "Plane_024", "Plane_026", "Plane_027", "Plane_029", "Plane_030", "Spiral", "Spiral_001"],
    "Flowers": ["Flower", "Flower002", "Flower008", "Flower011", "Flower012", "Flower016", "Flower017", "Flower018", "Flower019", "Flower020", "Flower022", "Flower023", "Flower024", "Flower025", "Flower027", "Flower028", "Flower029", "Flower030", "Flower031"],
    "Rocks": ["Rock_001", "Rock_002", "Rock_004", "Rock_006", "Rock_007", "Rock_009", "Rock_011", "Rock_019", "Rock_Formation_001", "Rock_Formation_002", "Rock_Formation_003", "Rock_Formation_004", "Rock_Formation_005", "Rock_Formation_008", "Rock_Formation_010", "Rock_Formation_012", "Rock_Formation_013", "Rock_Formation_016"],
}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(objects):
    points = []
    for obj in objects:
        if obj.type == "MESH":
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def main():
    group = sys.argv[sys.argv.index("--") + 1]
    output = os.path.join(os.getcwd(), "_testes", "cenario_ilha", f"_{group}.png")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    names = GROUPS[group]
    columns = 5
    rows = math.ceil(len(names) / columns)
    cell_width = 5.0
    cell_height = 5.0
    left = -(columns - 1) * cell_width * 0.5
    top = (rows - 1) * cell_height * 0.5

    for index, name in enumerate(names):
        before = set(bpy.context.scene.objects)
        source_group = "Trees02" if group == "Trees02Selected" else group
        bpy.ops.wm.fbx_import(filepath=os.path.join(ROOT, source_group, name + ".fbx"))
        imported = [obj for obj in bpy.context.scene.objects if obj not in before]
        meshes = [obj for obj in imported if obj.type == "MESH"]
        if not meshes:
            continue
        low, high = bounds(meshes)
        dimensions = high - low
        fit = 3.75 / max(dimensions.x, dimensions.z)
        pivot = bpy.data.objects.new("PreviewPivot", None)
        bpy.context.collection.objects.link(pivot)
        for obj in imported:
            if obj.parent not in imported:
                obj.parent = pivot
                obj.matrix_parent_inverse = pivot.matrix_world.inverted()
        column = index % columns
        row = index // columns
        pivot.scale = (fit, fit, fit)
        pivot.location = (
            left + column * cell_width - (low.x + high.x) * 0.5 * fit,
            -(low.y + high.y) * 0.5 * fit,
            top - row * cell_height - low.z * fit,
        )

        bpy.ops.object.text_add(location=(left + column * cell_width, -0.9, top - row * cell_height - 0.52), rotation=(math.pi / 2, 0, 0))
        label = bpy.context.object
        label.data.body = name
        label.data.align_x = "CENTER"
        label.data.align_y = "CENTER"
        label.data.size = 0.35
        label.data.extrude = 0.002
        label.data.materials.append(label_material)

    bpy.ops.object.light_add(type="AREA", location=(-10, -12, 18))
    key = bpy.context.object
    key.data.energy = 1500
    key.data.shape = "DISK"
    key.data.size = 10
    look_at(key, (0, 0, 4))
    bpy.ops.object.light_add(type="AREA", location=(14, -6, 8))
    fill = bpy.context.object
    fill.data.energy = 900
    fill.data.size = 9
    look_at(fill, (0, 0, 5))

    bpy.ops.object.camera_add(location=(0, -50, 0))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(rows * cell_height + 2.0, columns * cell_width / (1800 / 1100) + 2.0)
    look_at(camera, (0, 0, 0))
    bpy.context.scene.camera = camera

    world = bpy.context.scene.world
    world.color = (0.72, 0.79, 0.74)
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.72, 0.79, 0.74, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.65

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = output
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.resolution_percentage = 100
    bpy.ops.render.render(write_still=True)
    print("SAVED", output)


label_material = bpy.data.materials.new("LabelMaterial")
label_material.diffuse_color = (0.025, 0.055, 0.035, 1)
main()
