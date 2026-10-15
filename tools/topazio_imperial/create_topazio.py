"""Create an original stylized imperial topaz prop with Blender, no providers.

Run with Blender --background --factory-startup --python this_file.py.
The reference photos guide silhouette and color; no photo pixels are reused.
"""
from pathlib import Path
import sys
import json
import math
import hashlib
import traceback

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art' / 'topazio_imperial'
OUT.mkdir(parents=True, exist_ok=True)
log = (OUT / 'build.log').open('w', encoding='utf-8', buffering=1)
sys.stdout = log
sys.stderr = log

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Quaternion


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    asset = bpy.data.collections.new('PROP | Topazio imperial')
    studio = bpy.data.collections.new('STUDIO | apenas previa')
    scene.collection.children.link(asset)
    scene.collection.children.link(studio)

    # Painted atlas. Eight vertical strips correspond to the rectangular prism
    # and its clipped corners; the upper band supplies terminal/basal facets.
    size = 1024
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    u, v = xx / (size - 1), yy / (size - 1)
    sector = np.minimum((u * 8).astype(int), 7)
    local_u = u * 8 - sector
    h = np.clip(v / .80, 0, 1)
    stops = np.array([0, .12, .40, .64, .86, 1], dtype=np.float32)
    colors = np.array([[.48, .085, .009], [.84, .25, .018], [1, .49, .040],
                       [1, .61, .10], [.89, .28, .025], [.71, .13, .015]])
    pixels = np.stack([np.interp(h, stops, colors[:, c]) for c in range(3)], axis=-1)
    facet_tint = np.array([1.02, .84, .93, .80, .97, .88, 1.08, .91])[sector]
    pixels *= facet_tint[..., None]
    # Broad golden inner vein with only a few clean growth lines, deliberately
    # graphic rather than noisy photorealism. Everything is opaque for runtime.
    core = np.exp(-((local_u - .42 - .045*np.sin(h*5 + sector))/.25)**2)
    core *= np.clip(np.sin(np.pi*h), 0, 1)**.8
    pixels += core[..., None] * np.array([.04, .13, .08])
    for pos, width, amount in [(.10, .010, -.09), (.17, .005, .15),
                               (.76, .006, -.11), (.81, .012, .12), (.92, .004, -.07)]:
        line = np.exp(-((local_u - pos - .007*np.sin(h*9 + sector))/width)**2)
        fade = np.clip(np.sin(h*math.pi), 0, 1)
        pixels += (line*fade*amount)[..., None]*np.array([.35, .75, .55])
    # Two understated irregular mineral inclusions per face.
    for k in range(2):
        path = .29 + k*.25 + .03*np.sin(sector*2.6) + (local_u-.5)*(.11 if k else -.13)
        fissure = np.exp(-((h-path)/.0035)**2) * np.exp(-((local_u-.52)/.23)**6)
        pixels += fissure[..., None] * np.array([.01, .035, .025])
    capmask = v > .82
    caps = np.array([.91, .34, .035])[None,None,:] * ( .85 + .10*np.sin(u*20))[...,None]
    pixels = np.where(capmask[...,None], caps, pixels)
    rgba = np.concatenate((np.clip(pixels, 0, 1), np.ones((size,size,1))),axis=-1).astype(np.float32)
    image = bpy.data.images.new('Topazio_Imperial_BaseColor_1024', width=size, height=size, alpha=True)
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(OUT / 'topazio_imperial_basecolor.png')
    image.file_format = 'PNG'
    image.save()
    image.pack()

    mat = bpy.data.materials.new('Topazio | Mel e laranja | PBR opaco')
    mat.use_nodes = True
    mat.diffuse_color = (1, .48, .06, 1)
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value = .29
    p.inputs['Metallic'].default_value = 0
    p.inputs['IOR'].default_value = 1.62
    p.inputs['Coat Weight'].default_value = .35
    p.inputs['Coat Roughness'].default_value = .22
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = image
    mat.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    mat.node_tree.links.new(tex.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = .035

    # Topaz-inspired orthogonal prism with eight faces, uneven growth, clipped
    # corners and a blunt oblique termination, rather than a pointed gem cut.
    outline = [(-.105,-.115),(.105,-.115),(.147,-.073),(.147,.073),
               (.098,.116),(-.100,.116),(-.145,.073),(-.145,-.074)]
    fractions = [0, .10, .14, .18, .76, .80, .91, 1]
    ring_specs = [(0,.83,-.010),(.037,1,0),(.23,1.015,.003),
                  (.51,.97,.014),(.65,.95,.017),(.713,.60,-.007)]
    verts, faces, uvfaces = [], [], []
    count = 8 * (len(fractions)-1)
    for ri,(z,scale,lean) in enumerate(ring_specs):
        for side in range(8):
            a = Vector(outline[side]); b = Vector(outline[(side+1)%8])
            tangent = (b-a).normalized(); inward = Vector((-tangent.y,tangent.x))
            for f in fractions[:-1]:
                xy = a.lerp(b, f)*scale
                groove = .0009 if f in (.14,.80) and 0 < ri < 5 else 0
                xy += inward*groove
                zz = z
                if ri == 0:
                    zz = 0
                elif ri == 4:
                    zz += .013*math.sin(side*1.3) + .010*f
                elif ri == 5:
                    zz += .038*(xy.x/.147) + .010*(xy.y/.116)
                verts.append((xy.x+lean, xy.y+.005*ri, zz))
    for ri in range(len(ring_specs)-1):
        for j in range(count):
            nj = (j+1)%count
            faces.append((ri*count+j,ri*count+nj,(ri+1)*count+nj,(ri+1)*count+j))
            side, slot = divmod(j, len(fractions)-1)
            left = (side+fractions[slot])/8
            right = (side+fractions[slot+1])/8
            # Padding at sector borders prevents atlas bleed.
            left = max(left,(side+.004)/8); right = min(right,(side+.996)/8)
            lo = ring_specs[ri][0]/.713*.79+.005
            hi = ring_specs[ri+1][0]/.713*.79+.005
            uvfaces.append([(left,lo),(right,lo),(right,hi),(left,hi)])
    # Fan caps keep the heavily subdivided borders manifold.
    base_center = len(verts); verts.append((-.010,0,0))
    top_center = len(verts); verts.append((-.017,.022,.725))
    for j in range(count):
        nj=(j+1)%count
        faces.append((base_center,nj,j))
        uvfaces.append([(.50,.91),(.5+verts[nj][0],.91+verts[nj][1]*.5),(.5+verts[j][0],.91+verts[j][1]*.5)])
        faces.append((top_center,(len(ring_specs)-1)*count+j,(len(ring_specs)-1)*count+nj))
        uvfaces.append([(.5,.92),(.5+verts[(len(ring_specs)-1)*count+j][0],.92+verts[(len(ring_specs)-1)*count+j][1]*.4),(.5+verts[(len(ring_specs)-1)*count+nj][0],.92+verts[(len(ring_specs)-1)*count+nj][1]*.4)])
    mesh = bpy.data.meshes.new('Topazio_Imperial_lowpoly')
    mesh.from_pydata(verts, [], faces); mesh.update()
    obj = bpy.data.objects.new('Topazio_Imperial', mesh)
    asset.objects.link(obj); obj.data.materials.append(mat)
    uv = mesh.uv_layers.new(name='UVMap')
    for poly, coords in zip(mesh.polygons, uvfaces):
        for li, co in zip(poly.loop_indices,coords): uv.data[li].uv = co
    for poly in mesh.polygons: poly.use_smooth = False
    obj['asset_name'] = 'topazio_imperial_cartoon'
    obj['description'] = 'Cristal bruto cartoon inspirado no topazio imperial; prisma ortogonal e terminacao irregular.'
    obj['pivot'] = 'Centro da base; Blender Z-up / GLB Y-up'
    obj['reference_use'] = 'Silhueta e cores das tres fotos fornecidas; nenhuma foto usada como textura.'
    obj['height_m'] = round(max(v[2] for v in verts),4)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # Recalculate normals, verify manifold topology and positive volume.
    bm=bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    volume=bm.calc_volume(signed=True)
    assert nonmanifold == 0 and volume > 0
    bm.free(); mesh.calc_loop_triangles()
    assert len(mesh.loop_triangles) <= 1500
    bpy.ops.export_scene.gltf(filepath=str(OUT/'topazio_imperial.glb'), export_format='GLB',
        use_selection=True,export_apply=True,export_yup=True,export_animations=False,
        export_cameras=False,export_lights=False,export_extras=True)
    # Collision shape is optional, simple, and excluded from the visible mesh.
    collision_points = [verts[r*count+s*(len(fractions)-1)] for r in (0,1,4,5) for s in range(8)]
    # GLB axis mapping (x,y,z) -> (x,z,-y).
    godot_points=', '.join(f'{x:.6f}, {z:.6f}, {-y:.6f}' for x,y,z in collision_points)
    (OUT/'topazio_imperial_prop.tscn').write_text(
        '[gd_scene load_steps=3 format=3]\n\n'
        '[ext_resource type="PackedScene" path="topazio_imperial.glb" id="1_mesh"]\n\n'
        '[sub_resource type="ConvexPolygonShape3D" id="Shape_topazio"]\n'
        f'points = PackedVector3Array({godot_points})\n\n'
        '[node name="TopazioImperial" type="StaticBody3D"]\n\n'
        '[node name="Visual" parent="." instance=ExtResource("1_mesh")]\n\n'
        '[node name="CollisionShape3D" type="CollisionShape3D" parent="."]\n'
        'shape = SubResource("Shape_topazio")\n',encoding='utf-8')

    # Studio is deliberately excluded from export and easy to hide in Blender.
    floor_mat=bpy.data.materials.new('Studio | ardósia'); floor_mat.diffuse_color=(.031,.049,.064,1)
    floor_mat.use_nodes=True
    floor_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.031,.049,.064,1)
    floor_mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.82
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.002))
    floor=bpy.context.object; floor.name='Studio_floor'
    for col in list(floor.users_collection): col.objects.unlink(floor)
    studio.objects.link(floor); floor.data.materials.append(floor_mat)
    def light(name,position,power,color,size):
        data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.color=color; data.shape='DISK'; data.size=size
        ob=bpy.data.objects.new(name,data); studio.objects.link(ob); ob.location=position; aim(ob,(0,0,.35))
    light('Key | softbox',(.6,-.85,1.5),48,(1,.86,.66),.85)
    light('Fill | neutral',(-.9,-.4,.6),20,(.72,.85,1),.8)
    light('Rim | gold',(.5,.7,1.05),65,(1,.62,.30),.65)
    data=bpy.data.cameras.new('Camera_preview'); cam=bpy.data.objects.new('Camera_preview',data)
    studio.objects.link(cam); cam.location=(1.15,-1.75,1.02); aim(cam,(0,0,.35)); data.type='ORTHO'; data.ortho_scale=1.02; scene.camera=cam
    scene.world=bpy.data.worlds.new('Studio_world'); scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.08,.11,.16,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
    scene.render.resolution_x=1100; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.35
    scene.render.film_transparent=False
    scene.render.filepath=str(OUT/'topazio_imperial_preview.png')
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_distance=1.3
                area.spaces.active.region_3d.view_location=(0,0,.35)
                area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
                area.spaces.active.shading.type='MATERIAL'
                area.spaces.active.clip_end=100
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'topazio_imperial.blend'))
    print('SAVED_AND_EXPORTED',flush=True)
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=800; scene.render.resolution_y=1000; scene.cycles.samples=32
    for name,pos in [('front',(0,-2,.82)),('back',(-1.2,1.7,.94))]:
        cam.location=pos; aim(cam,(0,0,.35)); scene.render.filepath=str(OUT/f'topazio_imperial_{name}.png')
        bpy.ops.render.render(write_still=True)
    # Restore saved hero configuration; avoid an additional .blend backup.
    cam.location=(1.15,-1.75,1.02); aim(cam,(0,0,.35))
    stats={'blender_version':bpy.app.version_string,'generator':'tools/topazio_imperial/create_topazio.py',
        'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),
        'mesh_objects':1,'materials':1,'texture_resolution':[1024,1024],
        'nonmanifold_edges':nonmanifold,'positive_volume_m3':volume,
        'dimensions_m':list(obj.dimensions),'origin':'bottom center','alpha_mode':'OPAQUE',
        'transmission':0,'runtime_export':'glTF 2.0 binary; Y up; embedded texture',
        'reference_provenance':'Three user-supplied photographs used for visual guidance only.',
        'prompt':'Um cristal de topazio imperial em natura no estilo cartoon, modelado no Blender, para prop de jogo.',
        'negative_prompt':'Sem lapidacao de joia, sem ponta de quartzo, sem ruido fotorealista, sem pedestal exportado.',
        'checks':{'manifold_mesh':True,'triangle_budget_1500':True},
        'license':'Original procedural asset; follows repository MIT license.'}
    stats['files']={}
    for file in sorted(OUT.iterdir()):
        if file.suffix in ('.blend','.glb','.png','.tscn'):
            stats['files'][file.name]={'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
    (OUT/'manifest.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(stats,indent=2),flush=True)
    print('BUILD_COMPLETE',flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    (OUT/'FAILED.txt').write_text(traceback.format_exc(),encoding='utf-8')
    raise
finally:
    log.flush()
