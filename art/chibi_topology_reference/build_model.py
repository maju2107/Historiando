"""Rebuild the reference base in Blender: blender -b -t 6 -P build_model.py.

One closed, symmetric, editable mesh. Front = -Y, up = Z.
The sheet is a visual guide, not a source of exact hidden topology.
"""
import bpy
import bmesh
import math
import json
from pathlib import Path
from mathutils import Vector, Quaternion

OUT = Path(__file__).resolve().parent
REFERENCE = Path(r'C:\Users\obran\Downloads\WhatsApp Image 2026-09-12 at 12.03.20.jpeg')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = 'Chibi Base — Reference Study'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
scene.render.film_transparent = False

model_group = bpy.data.collections.new('01 · MODEL')
scene.collection.children.link(model_group)
stage = bpy.data.collections.new('02 · PREVIEW STUDIO')
scene.collection.children.link(stage)
reference_group = bpy.data.collections.new('03 · REFERENCE (packed)')
scene.collection.children.link(reference_group)

verts, faces = [], []
regions = {}

def vertex(co, region):
    i = len(verts)
    verts.append(tuple(co))
    regions.setdefault(region, []).append(i)
    return i

def bridge(a, b):
    assert len(a) == len(b)
    for i in range(len(a)):
        j = (i + 1) % len(a)
        faces.append((a[i], a[j], b[j], b[i]))

def cap(loop):
    # Quad fan without adding a high-valence center point.
    assert len(loop) % 2 == 0
    for i in range(1, len(loop)-2, 2):
        faces.append((loop[0], loop[i], loop[i+1], loop[i+2]))

def horizontal(cx, cy, z, rx, ry, n, region):
    return [vertex((cx+rx*math.cos(math.tau*i/n),
                    cy+ry*math.sin(math.tau*i/n), z), region) for i in range(n)]

# Heights and widths measured against the front elevation (4.05 units tall).
body_profiles = [
    (2.09, .390, .205, .012),
    (2.18, .375, .220, .025),
    (2.28, .340, .222, .020),
    (2.54, .250, .170, .005),
    (2.76, .245, .150, .000),
    (2.98, .272, .169, -.010),
    (3.105,.315, .175, -.005),
    (3.205,.310, .160, .000),
    (3.265,.185, .115, .000),
    (3.300,.100, .093, .000),
    (3.350,.100, .095, .000),
]
body = [horizontal(0, cy, z, rx, ry, 16, 'Torso & neck')
        for z, rx, ry, cy in body_profiles]
for row, dip in ((0,.070),(1,.040),(2,.010)):
    for i, index in enumerate(body[row]):
        x,y,z=verts[index]
        verts[index]=(x,y,z-dip*math.sin(math.tau*i/16)**2)
for row in range(len(body)-1):
    for i in range(16):
        # Two-by-two openings on each side are the shared shoulder sockets.
        if row in (5, 6) and i in (15, 0, 7, 8):
            continue
        j = (i+1) % 16
        faces.append((body[row][i], body[row][j], body[row+1][j], body[row+1][i]))

# Rounded cranium, gently squared facial plane, small rounded chin. No features
# are invented: the reference is an intentionally featureless modeling base.
head_profiles = [
    (3.385, .115, .118, -.090),
    (3.420, .170, .178, -.063),
    (3.490, .235, .238, -.023),
    (3.590, .276, .277, .002),
    (3.710, .298, .296, .008),
    (3.840, .294, .289, .010),
    (3.940, .259, .257, .013),
    (4.010, .187, .189, .012),
    (4.040, .089, .091, .010),
]
previous = body[-1]
for z, rx, ry, cy in head_profiles:
    ring = []
    for i in range(16):
        a = math.tau*i/16
        # Exponent < 1 gives the soft rectangular outline visible in the sheet.
        x = rx*math.copysign(abs(math.cos(a))**.84, math.cos(a))
        y = cy+ry*math.copysign(abs(math.sin(a))**.86, math.sin(a))
        ring.append(vertex((x, y, z), 'Head'))
    bridge(previous, ring)
    previous = ring
cap(previous)

# One shared saddle joins both legs to the pelvis; no overlapping hip spheres.
base = body[0]
saddle = [vertex((0, y+.012, 1.993+.042*(abs(y)/.205)), 'Pelvis / crotch')
          for y in (.103, 0, -.103)]
right_hip = [base[i % 16] for i in range(12, 21)] + saddle
left_hip = [base[i] for i in range(4, 13)] + list(reversed(saddle))
leg_section = [(-.80,-.85),(-.35,-1),(.35,-1),(.85,-.80),(1,0),(.85,.80),
               (.35,1),(-.35,1),(-.80,.85),(-1,.45),(-1,0),(-1,-.45)]
leg_profiles = [
    (1.985,.224,.178,.180,.006),
    (1.890,.238,.169,.165,.004),
    (1.465,.271,.151,.143,-.006),
    (1.365,.278,.155,.145,-.005),
    (1.280,.283,.157,.150,.000),
    (.635,.332,.175,.145,.022),
    (.430,.348,.211,.199,-.025),
    (.190,.380,.320,.385,-.145),
    (.000,.380,.320,.385,-.145),
]
for side, label, start in ((1,'L',right_hip),(-1,'R',left_hip)):
    previous = start
    for z,cx,rx,ry,cy in leg_profiles:
        coords = [(side*(cx+rx*x),cy+ry*y,z) for x,y in leg_section]
        # Left socket begins at the back. Reflect with reversed circulation.
        if side < 0:
            coords = [coords[(8-i)%12] for i in range(12)]
        ring = [vertex(co, 'Leg & foot.'+label) for co in coords]
        bridge(previous, ring)
        previous = ring
    cap(previous)

# Eight-sided arms, lowered 36 degrees, palms edge-on in the front elevation.
for side, label, j0 in ((1,'L',0),(-1,'R',8)):
    jm, jp = (j0-1)%16, (j0+1)%16
    if side < 0:
        jm, jp = jp, jm
    socket = [body[5][jm],body[5][j0],body[5][jp],body[6][jp],
              body[7][jp],body[7][j0],body[7][jm],body[6][jm]]
    # Socket traversal changes on the mirrored side; both palms face alike.
    forward = Vector((side*.806,0,-.592))
    up = Vector((side*.592,0,.806))
    depth = Vector((0,1,0))
    root = Vector((side*.321,0,3.130))
    previous = socket
    profiles = [(.090,.080,.088),(.200,.068,.074),(.410,.054,.059),
                (.505,.054,.057),(.560,.048,.051),(.720,.039,.045),
                (.805,.032,.041)]
    for dist,thick,width in profiles:
        center = root+forward*dist
        ring = []
        for k in range(8):
            a = (k-1)*math.pi/4
            ring.append(vertex(center-up*(thick*math.cos(a))+depth*(width*math.sin(a)), 'Arm.'+label))
        bridge(previous,ring)
        previous = ring

    # A broad palm, a separate thumb, and two low-poly finger groups reproduce
    # the simplified hand inset. These surfaces share vertices with the wrist.
    palm_rows = [previous]
    for dist,width,thick in ((.865,.069,.032),(.955,.081,.030),(1.060,.079,.026)):
        center = root+forward*dist
        section = [(-1,-1),(-1,-.30),(-1,1),(0,1),(1,1),(1,-.30),(1,-1),(0,-1)]
        ring = [vertex(center+up*(u*thick)+depth*(v*width), 'Hand.'+label) for u,v in section]
        palm_rows.append(ring)
    for row in range(3):
        for k in range(8):
            if row == 1 and k in (6,7):
                continue
            j = (k+1)%8
            faces.append((palm_rows[row][k],palm_rows[row][j],palm_rows[row+1][j],palm_rows[row+1][k]))

    thumb_base = [palm_rows[1][6],palm_rows[1][7],palm_rows[1][0],
                  palm_rows[2][0],palm_rows[2][7],palm_rows[2][6]]
    previous = thumb_base
    thumb_dir = (forward*.90-depth*.436).normalized()
    thumb_across = (forward*.436+depth*.90).normalized()
    thumb_root = root+forward*.913-depth*.100
    # Match the boundary's winding and thick/thin cross-section.
    thumb_section = [(1,-.55),(0,-1),(-1,-.55),(-1,.55),(0,1),(1,.55)]
    for dist,wide,thick in ((.047,.030,.024),(.102,.025,.021),(.145,.017,.016)):
        center = thumb_root+thumb_dir*dist
        ring = [vertex(center+up*(u*thick)+thumb_across*(v*wide),'Hand.'+label)
                for u,v in thumb_section]
        bridge(previous,ring)
        previous = ring
    cap(previous)

    end = palm_rows[-1]
    middle = vertex(root+forward*1.073+depth*(-.30*.079),'Hand.'+label)
    finger_roots = [([end[i] for i in (5,6,7,0,1)]+[middle],-.059,.021, .153),
                    ([end[i] for i in (1,2,3,4,5)]+[middle], .029,.049, .170)]
    for finger_index,(loop,lateral,wide,length) in enumerate(finger_roots):
        previous=loop
        for dist,factor in ((.065,1), (length-.020,.94),(length,.66)):
            center=root+forward*(1.060+dist)+depth*lateral
            # Orient the six-sided outline to the corresponding split opening.
            if finger_index == 0:
                uv=[(1,1),(1,-.65),(0,-1),(-1,-.65),(-1,1),(0,1)]
            else:
                uv=[(-1,-1),(-1,.65),(0,1),(1,.65),(1,-1),(0,-1)]
            ring=[vertex(center+up*(u*.025*factor)+depth*(v*wide*factor),'Hand.'+label) for u,v in uv]
            bridge(previous,ring)
            previous=ring
        cap(previous)

mesh=bpy.data.meshes.new('Chibi_Base_QuadTopology')
mesh.from_pydata(verts,[],faces)
mesh.update()
bm=bmesh.new()
bm.from_mesh(mesh)
# Socket center vertices have no faces and are deliberately removed.
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
mesh.update()
model=bpy.data.objects.new('Chibi Base · editable mesh',mesh)
model_group.objects.link(model)
model.show_wire=True
model.show_all_edges=True
model['source']='Reconstructed from the supplied front, side, back and hand reference.'
model['orientation']='Front -Y, up Z; total height 4.04 Blender units.'
model['topology']='Closed continuous surface, all quad faces, bilateral symmetry.'
model['rigging']='Unrigged base mesh. Arm and knee loops retained for further editing.'

# Rebuild selection groups after removing loose shoulder vertices.
for name in regions:
    group=model.vertex_groups.new(name=name)
    source_coords={tuple(round(c,6) for c in verts[i]) for i in regions[name]}
    indices=[v.index for v in mesh.vertices if tuple(round(c,6) for c in v.co) in source_coords]
    if indices:
        group.add(indices,1,'REPLACE')

def material(name,color,roughness=1):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=roughness
    return m

clay=material('Neutral gray clay',(.57,.59,.60))
ink=material('Topology lines',(.045,.058,.065))
mesh.materials.append(clay)
model.color=(.64,.66,.68,1)
for p in mesh.polygons:
    p.use_smooth=False
sub=model.modifiers.new('Optional smooth preview — disabled', 'SUBSURF')
sub.levels=2
sub.render_levels=2
sub.show_viewport=False
sub.show_render=False

# UVs make this immediately usable for subsequent texturing.
bpy.context.view_layer.objects.active=model
model.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.025)
bpy.ops.object.mode_set(mode='OBJECT')

# Real edge tubes for the renders, kept separate from the editable/exported mesh.
wire_data=bpy.data.curves.new('Preview edge lines','CURVE')
wire_data.dimensions='3D'
wire_data.bevel_depth=.0020
wire_data.bevel_resolution=0
wire_data.resolution_u=1
for edge in mesh.edges:
    spline=wire_data.splines.new('POLY')
    spline.points.add(1)
    for p,idx in zip(spline.points,edge.vertices):
        v=mesh.vertices[idx]
        p.co=(*(v.co+v.normal*.0008),1)
wire=bpy.data.objects.new('Topology overlay · render only',wire_data)
stage.objects.link(wire)
wire_data.materials.append(ink)

world=bpy.data.worlds.new('Neutral studio')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.52,.54,.56,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
scene.world=world
def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,loc,energy,size in [('Key',(-3,-5,8),350,5),('Fill',(4,-2,5),180,4),('Rim',(1,4,6),260,4)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    stage.objects.link(obj)
    obj.location=loc
    aim(obj,(0,0,2))
camera=bpy.data.objects.new('Orthographic Preview',bpy.data.cameras.new('Orthographic Preview'))
stage.objects.link(camera)
camera.data.type='ORTHO'
camera.data.ortho_scale=4.55
camera.data.clip_end=100
scene.camera=camera

if REFERENCE.exists():
    img=bpy.data.images.load(str(REFERENCE))
    img.pack()
    ref=bpy.data.objects.new('Supplied model sheet',None)
    reference_group.objects.link(ref)
    ref.empty_display_type='IMAGE'
    ref.data=img
    ref.empty_display_size=7.84
    ref.rotation_euler.x=math.pi/2
    ref.location=(0,1,2.03)
    ref.hide_render=True
reference_group.hide_viewport=True
reference_group.hide_render=True

readme=bpy.data.texts.new('START HERE.txt')
readme.write('CHIBI BASE / REFERENCE STUDY\n\n'
    'One continuous quad mesh reconstructed from the supplied model sheet.\n'
    'Front is -Y. Numpad 1 / 3 / Ctrl+1: front / side / back.\n'
    'Tab: edit the mesh. Vertex groups select head, torso, limbs and hands.\n'
    'The optional subdivision modifier is off to preserve the reference.\n'
    'Preview edge curves, cameras and lights live in the studio collection.\n'
    'The source image is packed in the hidden reference collection.\n'
    'The model is unrigged, UV unwrapped, and bilaterally symmetric.\n'
    'The image does not reveal every hidden edge; topology is reconstructed.\n')
bpy.data.texts.load(str(Path(__file__).resolve()))

def view(name,loc,target=(0,0,2.02),scale=4.55,width=1000,height=1100):
    camera.location=loc
    aim(camera,target)
    camera.data.ortho_scale=scale
    scene.render.resolution_x=width
    scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)

view('front',(0,-12,2.02))
view('side',(-12,0,2.02))
view('back',(0,12,2.02))
view('three_quarter',(6,-10,5.0),scale=4.80)
camera.data.clip_end=.95
view('hand_detail',(1.6296,0,3.1648),target=(1.156,0,2.52),scale=.58,width=900,height=900)
camera.data.clip_end=100

# Export only the actual base, with no topology overlay or studio objects.
bpy.ops.object.select_all(action='DESELECT')
model.select_set(True)
bpy.context.view_layer.objects.active=model
bpy.ops.export_scene.gltf(filepath=str(OUT/'Chibi_Reference_Base.glb'),
    export_format='GLB',use_selection=True,export_apply=False,export_cameras=False,export_lights=False)
bpy.ops.wm.obj_export(filepath=str(OUT/'Chibi_Reference_Base.obj'),export_selected_objects=True,
    apply_modifiers=False,export_materials=True,export_triangulated_mesh=False)

camera.location=(6,-10,4.7)
aim(camera,(0,0,2.02))
camera.data.ortho_scale=4.8
scene.render.resolution_x=1000
scene.render.resolution_y=1100
scene.render.filepath=str(OUT/'three_quarter.png')
wire.hide_set(True)
for obj in stage.objects:
    obj.hide_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.shading.type='SOLID'
            space.shading.light='STUDIO'
            space.shading.color_type='MATERIAL'
            space.shading.show_cavity=True
            space.shading.cavity_type='BOTH'
            space.overlay.show_floor=False
            space.overlay.show_axis_x=False
            space.overlay.show_axis_y=False
            space.region_3d.view_distance=6.6
            space.region_3d.view_location=(0,0,2.02)
            space.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2)
            space.region_3d.view_perspective='ORTHO'
scene.tool_settings.mesh_select_mode=(False,True,False)
scene['reference_notes']='Silhouette and proportions prioritized. Original edge layout is only partially visible.'
scene['mesh_faces']=len(mesh.polygons)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Chibi_Reference_Base.blend'))
print('MODEL COMPLETE',len(mesh.vertices),'vertices',len(mesh.polygons),'faces')
