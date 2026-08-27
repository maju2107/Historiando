import bpy
import math
import os
import re
from mathutils import Vector


ROOT = os.getcwd()


def parse_scene(relative_path):
    text = open(os.path.join(ROOT, relative_path), encoding="utf-8").read()
    resources = {}
    for match in re.finditer(r'\[ext_resource[^\]]*path="([^"]+)"[^\]]*id="([^"]+)"\]', text):
        resources[match.group(2)] = match.group(1).replace("res://", "")
    nodes = []
    blocks = re.split(r'(?=\[node )', text)
    for block in blocks[1:]:
        header = block.splitlines()[0]
        name_match = re.search(r'name="([^"]+)"', header)
        instance_match = re.search(r'instance=ExtResource\("([^"]+)"\)', header)
        model_match = re.search(r'model = ExtResource\("([^"]+)"\)', block)
        position_match = re.search(r'^position = Vector3\(([^)]+)\)', block, re.M)
        rotation_match = re.search(r'^rotation_degrees = Vector3\(([^)]+)\)', block, re.M)
        scale_match = re.search(r'^scale = Vector3\(([^)]+)\)', block, re.M)
        def vector(match, fallback):
            return tuple(float(value.strip()) for value in match.group(1).split(",")) if match else fallback
        nodes.append({
            "name": name_match.group(1) if name_match else "Node",
            "resource": resources.get(instance_match.group(1) if instance_match else model_match.group(1) if model_match else ""),
            "position": vector(position_match, (0, 0, 0)),
            "rotation": vector(rotation_match, (0, 0, 0)),
            "scale": vector(scale_match, (1, 1, 1)),
        })
    return nodes


def godot_transform(pivot, data):
    x, y, z = data["position"]
    sx, sy, sz = data["scale"]
    pivot.location = (x, -z, y)
    pivot.scale = (sx, sz, sy)
    pivot.rotation_euler[2] = -math.radians(data["rotation"][1])


def import_model(data):
    if not data["resource"]:
        return
    path = os.path.join(ROOT, data["resource"].replace("/", os.sep))
    if not os.path.exists(path):
        return
    before = set(bpy.context.scene.objects)
    if path.lower().endswith((".glb", ".gltf")):
        bpy.ops.import_scene.gltf(filepath=path)
    elif path.lower().endswith(".fbx"):
        bpy.ops.wm.fbx_import(filepath=path)
    else:
        return
    imported = [obj for obj in bpy.context.scene.objects if obj not in before]
    pivot = bpy.data.objects.new(data["name"], None)
    bpy.context.collection.objects.link(pivot)
    for obj in imported:
        if obj.parent not in imported:
            obj.parent = pivot
            obj.matrix_parent_inverse = pivot.matrix_world.inverted()
    godot_transform(pivot, data)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_water_cube(name, position, size):
    bpy.ops.mesh.primitive_cube_add(location=(position[0], -position[2], position[1]))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0] / 2, size[2] / 2, size[1] / 2)
    obj.data.materials.append(water_material)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    terrain = parse_scene(os.path.join("_testes", "cenario_ilha", "CenarioIlha.tscn"))
    for data in terrain:
        if data["resource"] and "kenney_platformer-kit" in data["resource"]:
            import_model(data)
    vegetation = parse_scene(os.path.join("_testes", "cenario_ilha", "PleistoceneVegetation.tscn"))
    for data in vegetation:
        import_model(data)

    add_water_cube("CorregoBase", (3, 4.1, 14), (2.6, .12, 19))
    add_water_cube("CorregoMedio", (3, 8.1, .5), (2.6, .12, 9))
    add_water_cube("CorregoTopo", (3, 12.1, -10), (2.6, .12, 8))
    add_water_cube("QuedaBase", (3, 2.1, 24), (2.6, 4, .18))
    add_water_cube("QuedaMedia", (3, 6.1, 5), (2.6, 4, .18))
    add_water_cube("QuedaTopo", (3, 10.1, -3), (2.6, 4, .18))

    bpy.ops.mesh.primitive_plane_add(size=180, location=(0, 0, -4.2))
    ocean = bpy.context.object
    ocean.data.materials.append(ocean_material)

    bpy.ops.object.light_add(type="SUN", location=(-20, -30, 60))
    sun = bpy.context.object
    sun.rotation_euler = (math.radians(28), 0, math.radians(-32))
    sun.data.energy = 2.2
    sun.data.angle = math.radians(18)
    bpy.ops.object.light_add(type="AREA", location=(25, -35, 45))
    fill = bpy.context.object
    fill.data.energy = 1100
    fill.data.size = 28
    look_at(fill, (0, 0, 5))

    bpy.ops.object.camera_add(location=(58, -68, 62))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 82
    camera.data.lens = 48
    look_at(camera, (0, 0, 4))
    bpy.context.scene.camera = camera

    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.64, 0.75, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.75
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(ROOT, "_testes", "cenario_ilha", "_island_preview.png")
    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.render.render(write_still=True)


water_material = bpy.data.materials.new("Water")
water_material.diffuse_color = (0.02, 0.48, 0.82, .9)
water_material.metallic = .18
water_material.roughness = .12
ocean_material = bpy.data.materials.new("Ocean")
ocean_material.diffuse_color = (0.015, 0.24, 0.4, 1)
ocean_material.roughness = .2
main()
