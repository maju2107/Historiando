"""Build an editable chibi character. Run in Blender's Text Editor or with -P.

Creates a separate scene and saves Chibi_Base.blend next to this script.
Use -- --render on Blender's command line to render front and three-quarter views.
"""
import bpy
import bmesh
import math
import os
import sys
from pathlib import Path
from mathutils import Vector

ADD_FACE = True
REFERENCE = Path(r"C:\Users\obran\Downloads\WhatsApp Image 2026-09-10 at 17.27.48.jpeg")
OUT = Path(__file__).resolve().parent if "__file__" in globals() else Path(bpy.path.abspath("//"))
OUT.mkdir(parents=True, exist_ok=True)


def build_character():
    scene = bpy.data.scenes.new("Chibi_Character_Base")
    groups = {}
    for name in ("Head", "Hair", "Body", "Torso", "Pants", "Shoes", "Accessories", "Stage", "Reference"):
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
        groups[name] = collection
    root = bpy.data.objects.new("Character_Root", None)
    scene.collection.objects.link(root)
    root.empty_display_size = 0.35
    root["description"] = "Separate editable base mesh parts. Front is -Y; up is Z."
    root["sculpting_note"] = "Overlapping components are intentionally separate; join and voxel remesh a copy for a continuous sculpt."

    def material(name, color, roughness=0.75):
        rgb = [int(color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        rgb = [c / 12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4 for c in rgb]
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*rgb, 1)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = roughness
        return mat

    skin = material("Skin_Warm_Peach", "F5AD7B")
    hair = material("Hair_Dark_Brown", "653921")
    purple = material("Clothing_Deep_Purple", "493066")
    collar_mat = material("Clothing_Collar", "60417B")
    waistband_mat = material("Clothing_Waistband", "39254E")
    gold = material("Accents_Yellow_Orange", "EFB548", 0.55)
    cream = material("Accessories_Ivory", "F8EFDF")
    white = material("Eyes_White", "FFF6E8", 0.4)
    brown = material("Eyes_Brown", "663717", 0.4)
    dark = material("Face_Dark_Brown", "302018")
    floor_mat = material("Ground", "DDD4CC")

    def link(name, data, group, mat=None):
        obj = bpy.data.objects.new(name, data)
        groups[group].objects.link(obj)
        if group not in ("Stage", "Reference"):
            obj.parent = root
        if mat is not None:
            data.materials.append(mat)
            obj.color = mat.diffuse_color
        return obj

    def mesh(name, vertices, faces, group, mat, smooth=True):
        data = bpy.data.meshes.new(name + "_Mesh")
        data.from_pydata(vertices, [], faces)
        data.update()
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(data)
        bm.free()
        data.update()
        for face in data.polygons:
            face.use_smooth = smooth
        return link(name, data, group, mat)

    def sphere(name, location, radii, group, mat, segments=24, rings=16):
        data = bpy.data.meshes.new(name + "_Mesh")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1)
        for vertex in bm.verts:
            vertex.co.x *= radii[0]
            vertex.co.y *= radii[1]
            vertex.co.z *= radii[2]
        bm.normal_update()
        bm.to_mesh(data)
        bm.free()
        for face in data.polygons:
            face.use_smooth = True
        obj = link(name, data, group, mat)
        obj.location = location
        return obj

    def bevel(obj, width=0.025):
        mod = obj.modifiers.new("Soft_Edges", 'BEVEL')
        mod.width = width
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        mod.use_clamp_overlap = True
        return obj

    def loft(name, profiles, group, mat, sides=16):
        # Profiles: center X, center Y, Z, X radius, Y radius.
        vertices = [(cx+rx*math.cos(math.tau*i/sides), cy+ry*math.sin(math.tau*i/sides), z)
                    for cx, cy, z, rx, ry in profiles for i in range(sides)]
        faces = []
        for ring in range(len(profiles)-1):
            a, b = ring*sides, (ring+1)*sides
            for i in range(sides):
                j = (i+1) % sides
                faces.append((a+i, a+j, b+j, b+i))
        faces.append(tuple(reversed(range(sides))))
        top = (len(profiles)-1)*sides
        faces.append(tuple(top+i for i in range(sides)))
        obj = mesh(name, vertices, faces, group, mat)
        obj.data.polygons[-2].use_smooth = False
        obj.data.polygons[-1].use_smooth = False
        return obj

    def tube(name, start, end, r1, r2, group, mat):
        direction = Vector(end)-Vector(start)
        obj = loft(name, [(0, 0, 0, r1, r1), (0, 0, direction.length, r2, r2)], group, mat)
        obj.location = start
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = direction.to_track_quat('Z', 'Y')
        return obj

    def curve(name, points, radius, group, mat, cyclic=False, smooth=True):
        data = bpy.data.curves.new(name + "_Curve", 'CURVE')
        data.dimensions = '3D'
        data.resolution_u = 8
        data.bevel_depth = radius
        data.bevel_resolution = 2
        data.use_fill_caps = True
        spline = data.splines.new('BEZIER' if smooth else 'POLY')
        if smooth:
            spline.bezier_points.add(len(points)-1)
            for point, co in zip(spline.bezier_points, points):
                point.co = co
                point.handle_left_type = point.handle_right_type = 'AUTO'
        else:
            spline.points.add(len(points)-1)
            for point, co in zip(spline.points, points):
                point.co = (*co, 1)
        spline.use_cyclic_u = cyclic
        return link(name, data, group, mat)

    # Large UV-sphere head, simplified neck and ears.
    head = sphere("Head_Base", (0, -0.02, 4.16), (0.84, 0.67, 0.88), "Head", skin, 32, 20)
    tube("Neck", (0, 0, 3.17), (0, 0, 3.55), 0.19, 0.19, "Body", skin)
    for side, label in ((-1, "L"), (1, "R")):
        sphere("Ear_"+label, (side*0.80, -0.01, 4.02), (0.16, 0.12, 0.22), "Head", skin)

    # Skull-wrapping hair cap with the face exposed.
    vertices, faces = [(0, 0, 5.15)], []
    sides, rings = 32, 10
    for ring in range(1, rings+1):
        for i in range(sides):
            phi = math.tau*i/sides
            boundary = 1.85-0.63*max(0, -math.sin(phi))+0.60*max(0, math.sin(phi))
            theta = ring/rings*boundary
            vertices.append((0.90*math.sin(theta)*math.cos(phi),
                             0.75*math.sin(theta)*math.sin(phi), 4.20+0.95*math.cos(theta)))
    for i in range(sides):
        faces.append((0, 1+i, 1+(i+1)%sides))
    for ring in range(rings-1):
        a, b = 1+ring*sides, 1+(ring+1)*sides
        for i in range(sides):
            j = (i+1)%sides
            faces.append((a+i, b+i, b+j, a+j))
    cap = mesh("Hair_Scalp_Cap", vertices, faces, "Hair", hair)
    solidify = cap.modifiers.new("Hair_Cap_Thickness", 'SOLIDIFY')
    solidify.thickness, solidify.offset = 0.035, -1
    sphere("Hair_Ponytail_Core", (0, 0.78, 3.25), (1.14, 0.63, 1.76), "Hair", hair)
    sphere("Hair_Ponytail_Attachment", (0, 0.58, 4.70), (0.43, 0.38, 0.44), "Hair", hair)
    for i in range(8):
        t = i/7
        width = 0.54+0.61*math.sin(math.pi*t)**0.75
        for side, label in ((-1, "L"), (1, "R")):
            sphere("Hair_Ponytail_Lobe_{}_{}".format(label, i+1),
                   (side*width, 0.78+0.035*math.cos(i), 4.70-2.90*t),
                   (0.34, 0.48, 0.36), "Hair", hair, 16, 12)
    for i, x in enumerate((-0.56, -0.28, 0, 0.28, 0.56)):
        sphere("Hair_Crown_Curl_{}".format(i+1), (x, 0.45, 4.91+0.10*(1-abs(x))),
               (0.28, 0.32, 0.29), "Hair", hair, 16, 12)
    for side, label in ((-1, "L"), (1, "R")):
        sphere("Hair_Temple_Curl_"+label, (side*0.70, -0.35, 4.33),
               (0.14, 0.15, 0.24), "Hair", hair, 16, 12)

    # Jacket, separately editable sleeves, cylindrical arms and mitten hands.
    bevel(loft("Torso_Jacket", [(0, 0, 2.53, 0.49, 0.31), (0, 0, 2.68, 0.55, 0.35),
          (0, 0, 3.12, 0.54, 0.36), (0, 0, 3.30, 0.44, 0.31), (0, 0, 3.43, 0.23, 0.22)], "Torso", purple))
    for side, label in ((-1, "L"), (1, "R")):
        bevel(tube("Jacket_Sleeve_"+label, (side*0.40, 0, 3.22), (side*0.79, 0, 2.82),
                   0.25, 0.29, "Torso", purple), 0.035)
        tube("Arm_"+label, (side*0.76, 0, 2.84), (side*1.00, -0.025, 2.25), 0.145, 0.12, "Body", skin)
        sphere("Hand_"+label, (side*1.01, -0.035, 2.20), (0.19, 0.15, 0.22), "Body", skin)
        points = [(side*0.035, -0.25, 3.44), (side*0.30, -0.31, 3.33), (side*0.15, -0.395, 3.15)]
        verts = points+[(x, y+0.045, z) for x, y, z in points]
        faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        bevel(mesh("Collar_"+label, verts, faces, "Torso", collar_mat, False), 0.012)
    for i, z in enumerate((3.09, 2.80)):
        sphere("Jacket_Gold_Button_{}".format(i+1), (0.25, -0.342, z),
               (0.074, 0.045, 0.074), "Accessories", gold, 16, 12)

    # Wide trousers and contrasting cords.
    loft("Pants_Hips", [(0, 0, 2.30, 0.50, 0.30), (0, 0, 2.59, 0.49, 0.31)], "Pants", purple)
    bevel(loft("Pants_Waistband", [(0, 0, 2.46, 0.505, 0.325), (0, 0, 2.61, 0.505, 0.325)],
               "Pants", waistband_mat), 0.015)
    for side, label in ((-1, "L"), (1, "R")):
        bevel(loft("Pants_Wide_Leg_"+label,
                   [(side*0.43, 0, 0.46, 0.36, 0.33), (side*0.43, 0, 0.57, 0.40, 0.35),
                    (side*0.36, 0, 1.34, 0.35, 0.32), (side*0.29, 0, 2.12, 0.30, 0.29),
                    (side*0.26, 0, 2.44, 0.29, 0.30)], "Pants", purple))
        curve("Pants_Drawstring_"+label, [(side*0.34, -0.29, 2.43), (side*0.40, -0.33, 1.99),
                                         (side*0.47, -0.35, 1.24)], 0.017, "Accessories", cream)
        sphere("Pants_Cord_Knot_"+label, (side*0.47, -0.35, 1.23), (0.045,)*3, "Accessories", cream, 12, 8)
        tube("Pants_Cord_Tassel_"+label, (side*0.47, -0.35, 1.09), (side*0.47, -0.35, 1.20),
             0.063, 0.027, "Accessories", cream)

    # Oval shoes: closed upper plus separate truly planar sole.
    for side, label in ((-1, "L"), (1, "R")):
        x = side*0.43
        bevel(loft("Shoe_Flat_Sole_"+label,
              [(x, -0.12, 0, 0.37, 0.55), (x, -0.12, 0.12, 0.38, 0.56), (x, -0.12, 0.16, 0.37, 0.55)],
              "Shoes", cream, 24), 0.012)
        bevel(loft("Shoe_Upper_"+label,
              [(x, -0.12, 0.13, 0.365, 0.54), (x, -0.13, 0.25, 0.37, 0.54),
               (x, -0.10, 0.36, 0.32, 0.47), (x, 0.015, 0.44, 0.25, 0.32)], "Shoes", gold, 24))

    # White headband, triangular cat ears, gold center and hanging cords.
    arc = [(0.91*math.cos(a), -0.30, 4.16+0.99*math.sin(a))
           for a in [0.08+(math.pi-0.16)*i/16 for i in range(17)]]
    curve("Headband_Arc", arc, 0.033, "Accessories", cream)
    for side, label in ((-1, "L"), (1, "R")):
        curve("Headband_Cat_Ear_"+label, [(side*0.32, -0.40, 4.99), (side*0.62, -0.34, 5.54),
              (side*0.76, -0.30, 4.96)], 0.035, "Accessories", cream, True, False)
        curve("Headband_Hanging_Cord_"+label,
              [(side*0.66, -0.31, 4.99), (side*0.83, -0.36, 4.26), (side*0.95, -0.37, 3.63),
               (side*1.09, -0.37, 3.13)], 0.020, "Accessories", cream)
        sphere("Headband_Cord_Knot_"+label, (side*1.09, -0.37, 3.13), (0.065,)*3, "Accessories", cream, 12, 8)
        tube("Headband_Tassel_"+label, (side*1.12, -0.37, 2.88), (side*1.09, -0.37, 3.07),
             0.095, 0.035, "Accessories", cream)
    ring = [(0.155*math.cos(math.tau*i/32), -0.39, 5.12+0.155*math.sin(math.tau*i/32)) for i in range(32)]
    curve("Headband_Gold_Ring", ring, 0.047, "Accessories", gold, True, False)

    if ADD_FACE:
        for side, label in ((-1, "L"), (1, "R")):
            x = side*0.30
            sphere("Eye_White_"+label, (x, -0.648, 4.16), (0.175, 0.070, 0.215), "Head", white)
            sphere("Eye_Iris_"+label, (x, -0.706, 4.16), (0.103, 0.035, 0.149), "Head", brown)
            sphere("Eye_Pupil_"+label, (x, -0.735, 4.16), (0.049, 0.017, 0.100), "Head", dark, 16, 12)
            sphere("Eye_Highlight_"+label, (x-0.030, -0.750, 4.215), (0.026, 0.012, 0.033), "Head", white, 12, 8)
            curve("Eyebrow_"+label, [(x-0.13, -0.612, 4.43), (x, -0.632, 4.48),
                                    (x+0.13, -0.612, 4.44)], 0.022, "Head", hair)
        sphere("Nose", (0, -0.674, 3.99), (0.073, 0.090, 0.078), "Head", skin, 16, 12)
        curve("Smile", [(-0.17, -0.661, 3.87), (0, -0.675, 3.82), (0.17, -0.661, 3.87)], 0.011, "Head", dark)

    mesh("Ground", [(-100, -100, -0.016), (100, -100, -0.016), (100, 100, -0.016), (-100, 100, -0.016)],
         [(0, 1, 2, 3)], "Stage", floor_mat, False)
    world = bpy.data.worlds.new("Chibi_Studio_World")
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.16, 0.18, 0.22, 1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.45
    scene.world = world

    def aim(obj, target):
        obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()

    for name, loc, power, size, color in (
        ("Key_Light", (-4, -6, 8), 950, 5, (1, 0.88, 0.76)),
        ("Fill_Light", (5, -3, 5), 650, 4, (0.79, 0.86, 1)),
        ("Hair_Rim_Light", (0, 5, 7), 1100, 3.5, (1, 0.84, 0.67)),
    ):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size, data.color = power, size, color
        data.shape = 'DISK'
        obj = link(name, data, "Stage")
        obj.location = loc
        aim(obj, (0, 0, 2.8))
    camera = link("Character_Camera", bpy.data.cameras.new("Character_Camera"), "Stage")
    camera.location = (5.8, -14, 6.8)
    aim(camera, (0, 0.15, 2.75))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 6.65
    camera.data.clip_end = 300
    scene.camera = camera
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
        try:
            scene.render.engine = engine
            break
        except (TypeError, ValueError):
            pass
    scene.render.resolution_x, scene.render.resolution_y = 900, 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    scene.display.shading.color_type = 'MATERIAL'

    # Pack the supplied drawing so the blend stays self-contained.
    if REFERENCE.is_file():
        image = bpy.data.images.load(str(REFERENCE), check_existing=True)
        image.pack()
        ref = link("Character_Sheet", None, "Reference")
        ref.empty_display_type = 'IMAGE'
        ref.data = image
        ref.empty_display_size = 6
        ref.location = (4.5, 1.5, 2.8)
        ref.rotation_euler.x = math.pi/2
        ref.hide_render = True
    groups["Reference"].hide_viewport = True
    groups["Reference"].hide_render = True

    if bpy.context.window:
        bpy.context.window.scene = scene
        bpy.context.view_layer.objects.active = head
        head.select_set(True)
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    space = area.spaces.active
                    space.shading.type = 'MATERIAL'
                    space.region_3d.view_perspective = 'CAMERA'
                    space.overlay.show_overlays = False
    scene["generator"] = "build_chibi.py"
    scene["reference_style"] = "Chibi base mesh: warm skin, brown ponytail, purple clothing, gold accents."
    return scene


if __name__ == "__main__":
    scene = build_character()
    # Include the editable generator inside the saved Blender project.
    if "__file__" in globals():
        source = bpy.data.texts.new("build_chibi.py")
        source.write(Path(__file__).read_text(encoding="utf-8"))
    output = OUT / "Chibi_Base.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    if "--render" in sys.argv:
        camera = scene.camera
        original_location, original_rotation = camera.location.copy(), camera.rotation_euler.copy()
        scene.render.filepath = str(OUT / "three_quarter.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
        camera.location = (0, -15, 3.5)
        camera.rotation_euler = (Vector((0, 0, 2.77))-camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(OUT / "front.png")
        bpy.ops.render.render(write_still=True, scene=scene.name)
        camera.location, camera.rotation_euler = original_location, original_rotation
        scene.render.filepath = str(OUT / "three_quarter.png")
        bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    print("CHIBI_BASE_COMPLETE:", output)
