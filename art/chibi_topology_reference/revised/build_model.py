"""Rebuild the reference base in Blender: blender -b -t 6 -P build_model.py.

One closed, symmetric, editable mesh. Front = -Y, up = Z.
The sheet is a visual guide, not a source of exact hidden topology.
"""
import bpy
import bmesh
import math
import json
import sys
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
face_regions={}

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
    (2.155,.390, .205, .012),
    (2.250,.375, .220, .025),
    (2.350,.340, .222, .020),
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
for row, dip in ((0,.030),(1,.020),(2,.010)):
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

# Pelvic transition: expand the front/back center to three vertices each.
# This creates a two-quad-wide perineal bridge instead of a shared point/edge.
base=body[0]
pelvic={}
for i in range(16):
    a=math.tau*i/16
    y=.012+.203*math.sin(a)
    z=2.105-.035*math.sin(a)**2
    if i in (4,12):
        xs=(.058,0,-.058) if i==4 else (-.058,0,.058)
        pelvic[i]=[vertex((x,y,z),'Pelvis / crotch') for x in xs]
    else:
        pelvic[i]=[vertex((.395*math.cos(a),y,z),'Pelvis / crotch')]
for i in range(16):
    j=(i+1)%16
    faces.append((base[i],base[j],pelvic[j][0],pelvic[i][-1]))
    if len(pelvic[i])==3:
        faces.append((base[i],*pelvic[i]))
gusset=[list(reversed(pelvic[4]))]
for y in (.100,0,-.100):
    z=2.040+.025*abs(y)/.203
    gusset.append([vertex((x,y+.012,z-(.008 if x==0 else 0)),'Pelvis / crotch')
                   for x in (-.050,0,.050)])
gusset.append(pelvic[12])
face_regions['Perineum bridge']=[]
for row in range(4):
    for col in range(2):
        face_regions['Perineum bridge'].append(len(faces))
        faces.append((gusset[row][col],gusset[row][col+1],
                      gusset[row+1][col+1],gusset[row+1][col]))
right_hip=([pelvic[12][2]]+[pelvic[i][0] for i in (13,14,15,0,1,2,3)]+
           [pelvic[4][0]]+[gusset[r][2] for r in (1,2,3)])
left_hip=([pelvic[4][2]]+[pelvic[i][0] for i in range(5,12)]+
          [pelvic[12][0]]+[gusset[r][0] for r in (3,2,1)])
leg_section = [(-.80,-.85),(-.35,-1),(.35,-1),(.85,-.80),(1,0),(.85,.80),
               (.35,1),(-.35,1),(-.80,.85),(-1,.45),(-1,0),(-1,-.45)]
leg_profiles = [
    (1.980,.235,.175,.180,.006),
    (1.865,.245,.167,.165,.004),
    (1.560,.266,.152,.147,-.002),
    (1.490,.271,.151,.143,-.006),
    (1.365,.278,.155,.145,-.005),
    (1.240,.284,.158,.147,.000),
    (1.165,.290,.161,.153,.007),
    (.635,.332,.175,.145,.022),
    (.430,.348,.211,.199,-.025),
    (.190,.380,.320,.385,-.145),
    (.000,.380,.320,.385,-.145),
]
for side, label, start in ((1,'L',right_hip),(-1,'R',left_hip)):
    # Same local indexing on both sides keeps the patella patch symmetric.
    if side<0:
        start=[start[(8-i)%12] for i in range(12)]
    rings=[]
    for row,(z,cx,rx,ry,cy) in enumerate(leg_profiles):
        coords=[]
        for x,y in leg_section:
            zz=z
            if row in (3,5):
                # Rear crease receives less spacing; the front can stretch.
                t=(y+1)/2
                zz=1.365+(z-1.365)*(1-.72*t)
            coords.append((side*(cx+rx*x),cy+ry*y,zz))
        ring=[vertex(co,'Leg & foot.'+label) for co in coords]
        rings.append(ring)
    bridge(start,rings[0])
    for row in range(len(rings)-1):
        for col in range(12):
            if row in (3,4) and col in (0,1,2):
                continue
            j=(col+1)%12
            faces.append((rings[row][col],rings[row][j],rings[row+1][j],rings[row+1][col]))
    cap(rings[-1])
    # Closed oval edge loop surrounding a two-by-three quad patella patch.
    outer=([rings[3][i] for i in (0,1,2,3)]+[rings[4][3]]+
           [rings[5][i] for i in (3,2,1,0)]+[rings[4][0]])
    patch=[]
    for r in range(3):
        line=[]
        for c in range(4):
            xn=(-1,-.36,.36,1)[c]
            zoff=(1,0,-1)[r]
            x=.278+xn*(.090 if r==1 else .068)
            z=1.365+zoff*(.080 if c in (1,2) else .064)
            y=-.175+.016*abs(xn)+(.006 if r!=1 else 0)
            line.append(vertex((side*x,y,z),'Knee / patella.'+label))
        patch.append(line)
    inner=patch[0]+[patch[1][3]]+list(reversed(patch[2]))+[patch[1][0]]
    face_regions['Knee contour.'+label]=list(range(len(faces),len(faces)+10))
    bridge(outer,inner)
    face_regions['Knee patella.'+label]=[]
    for r in range(2):
        for c in range(3):
            face_regions['Knee patella.'+label].append(len(faces))
            faces.append((patch[r][c],patch[r][c+1],patch[r+1][c+1],patch[r+1][c]))

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

    # Twenty-vertex palm section: nine vertices across each surface, plus
    # side midpoints. Quad-only fans distribute the eight wrist edges.
    wrist=previous
    section=([(-1,-1+i*.25) for i in range(9)]+[(0,1)]+
             [(1,1-i*.25) for i in range(9)]+[(0,-1)])
    palm_rows=[]
    for row,(dist,width,thick) in enumerate(((.855,.047,.030),(.920,.072,.033),
                                          (1.000,.090,.031),(1.075,.085,.026))):
        ring=[]
        for u,v in section:
            dd=dist
            if row==3:
                dd+=.012-.035*((v+.15)/1.15)**2
            bulge=1-.13*abs(v)
            co=root+forward*dd+up*(u*thick*bulge)+depth*(v*width)
            ring.append(vertex(co,'Hand / palm.'+label))
        palm_rows.append(ring)
    mapping=[(0,1,2),(3,4,5),(6,7,8),(9,),
             (10,11,12),(13,14,15),(16,17,18),(19,)]
    first=palm_rows[0]
    for k,ids in enumerate(mapping):
        j=(k+1)%8
        faces.append((wrist[k],wrist[j],first[mapping[j][0]],first[ids[-1]]))
        if len(ids)==3:
            faces.append((wrist[k],first[ids[0]],first[ids[1]],first[ids[2]]))
    for row in range(3):
        for k in range(20):
            # An eight-edge socket routes the thenar loops into the thumb.
            if row in (0,1) and k in (18,19):
                continue
            j=(k+1)%20
            faces.append((palm_rows[row][k],palm_rows[row][j],palm_rows[row+1][j],palm_rows[row+1][k]))

    thumb_base=[palm_rows[0][18],palm_rows[0][19],palm_rows[0][0],palm_rows[1][0],
                palm_rows[2][0],palm_rows[2][19],palm_rows[2][18],palm_rows[1][18]]
    previous=thumb_base
    thumb_dir=(forward*.62-depth*.785).normalized()
    thumb_across=(forward*.785+depth*.62).normalized()
    thumb_root=root+forward*.931-depth*.065
    for dist,width,thick in ((.070,.032,.027),(.095,.028,.026),(.112,.027,.025),
                             (.131,.025,.023),(.163,.024,.022),(.180,.024,.022),
                             (.202,.022,.020),(.214,.016,.015),(.220,.006,.006)):
        center=thumb_root+thumb_dir*dist
        ring=[]
        for k in range(8):
            a=(k+1)*math.pi/4
            co=center+up*(thick*math.cos(a))-thumb_across*(width*math.sin(a))
            ring.append(vertex(co,'Finger / thumb.'+label))
        bridge(previous,ring)
        previous=ring
    cap(previous)

    # Four individual finger roots share web edges with the palm. Each finger
    # receives MCP/PIP/DIP support loops and a rounded quad tip.
    end=palm_rows[-1]
    web={0:end[19],4:end[9]}
    for boundary in (1,2,3):
        lower,upper=Vector(verts[end[2*boundary]]),Vector(verts[end[18-2*boundary]])
        web[boundary]=vertex((lower+upper)/2+forward*.005,'Hand / webs.'+label)
    finger_specs=[('index',.183,.020,-.24),('middle',.211,.022,-.055),
                  ('ring',.194,.021,.12),('little',.150,.018,.32)]
    for f,(name,length,radius,splay) in enumerate(finger_specs):
        a=2*f
        loop=([end[a],end[a+1],end[a+2],web[f+1],
               end[18-a-2],end[18-a-1],end[18-a],web[f]])
        center=sum((Vector(verts[i]) for i in loop),Vector())/8
        tangent=(forward+depth*splay).normalized()
        lateral=(depth-forward*splay).normalized()
        previous=loop
        for t,factor in ((.12,1),(.31,.96),(.40,.96),(.48,.94),
                         (.63,.88),(.72,.88),(.80,.84),(.92,.78),(.98,.55),(1.0,.18)):
            # Subtle natural curl in the open-hand pose.
            pos=center+tangent*(length*t)-up*(.006*t*t)
            ring=[]
            for k in range(8):
                angle=(k-1)*math.pi/4
                co=pos-up*(radius*.88*factor*math.cos(angle))+lateral*(radius*factor*math.sin(angle))
                ring.append(vertex(co,'Finger / '+name+'.'+label))
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
model['revision']='Five fingers per hand, oval patella loops, two-column perineal bridge.'
model['region_faces']=json.dumps(face_regions)

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

# An optional, zero-valued shape key provides a repeatable 60-degree bend
# inspection. This is a geometry check, not a substitute for a character rig.
model.shape_key_add(name='Basis')
bend=model.shape_key_add(name='Teste_joelho_L_60graus')
pivot=Vector((.278,.010,1.365))
for v,p in zip(mesh.vertices,bend.data):
    if v.co.x>0 and v.co.z<1.54:
        t=max(0,min(1,(1.54-v.co.z)/.36))
        w=t*t*(3-2*t)
        p.co=pivot+Quaternion((1,0,0),math.radians(60)*w)@(v.co-pivot)
bend.value=0

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
for name in ('download (5).jpg','download (4).jpg','Modeling hips on characters_.jpg'):
    img=bpy.data.images.load(str(REFERENCE.parent/name))
    img.pack()
    img.use_fake_user=True
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
readme.write('\nREVISAO DE TOPOLOGIA\n'
    'Maos: cinco dedos, loops nas articulacoes, polegar conectado a palma.\n'
    'Joelhos: contorno fechado da patela e espaco menor na dobra posterior.\n'
    'Virilha: faixa de duas colunas de quads separa as raizes das pernas.\n'
    'Teste_joelho_L_60graus e uma shape key de inspecao, salva em zero.\n'
    'Ainda nao existe um rig de animacao. As tres novas imagens estao empacotadas.\n')
bpy.data.texts.load(str(Path(__file__).resolve()))

def view(name,loc,target=(0,0,2.02),scale=4.55,width=1000,height=1100):
    camera.location=loc
    aim(camera,target)
    camera.data.ortho_scale=scale
    scene.render.resolution_x=width
    scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene.render.filepath=str(OUT/(name+'.png'))
    if '--no-render' not in sys.argv and ('--bend-only' not in sys.argv or name=='knee_bent'):
        bpy.ops.render.render(write_still=True)

view('front',(0,-12,2.02))
view('side',(-12,0,2.02))
view('back',(0,12,2.02))
view('three_quarter',(6,-10,5.0),scale=4.80)
camera.data.clip_end=.95
view('hand_detail',(1.6296,0,3.1648),target=(1.156,0,2.52),scale=.68,width=1100,height=1100)
camera.data.clip_end=100
# Color the review images to expose the same flow discussed in the references.
for name,color in [('Patella study',(.28,.22,.65)),('Contour study',(.06,.64,.36)),
                   ('Perineum study',(.92,.46,.10))]:
    mesh.materials.append(material(name,color))
for name,indices in face_regions.items():
    index=1 if name.startswith('Knee patella') else 2 if name.startswith('Knee contour') else 3
    for i in indices:
        mesh.polygons[i].material_index=index
view('knee_front',(.278,-3,1.365),target=(.278,0,1.365),scale=.62,width=1000,height=1000)
view('knee_side',(3,0,1.365),target=(.278,0,1.365),scale=.62,width=1000,height=1000)
view('hips_front',(0,-3,2.05),target=(0,0,2.05),scale=1.10,width=1100,height=1000)
view('hips_under',(0,-3,.9),target=(0,0,2.07),scale=1.15,width=1100,height=1000)
bend.value=1
for spline,edge in zip(wire_data.splines,mesh.edges):
    for p,idx in zip(spline.points,edge.vertices):
        p.co=(*(bend.data[idx].co+mesh.vertices[idx].normal*.0008),1)
camera.data.clip_end=3.0
view('knee_bent',(3,0,1.365),target=(.278,0,1.365),scale=.80,width=1000,height=1000)
camera.data.clip_end=100
bend.value=0
for spline,edge in zip(wire_data.splines,mesh.edges):
    for p,idx in zip(spline.points,edge.vertices):
        v=mesh.vertices[idx]
        p.co=(*(v.co+v.normal*.0008),1)
for polygon in mesh.polygons:
    polygon.material_index=0

# Export only the actual base, with no topology overlay or studio objects.
bpy.ops.object.select_all(action='DESELECT')
model.select_set(True)
bpy.context.view_layer.objects.active=model
bpy.ops.export_scene.gltf(filepath=str(OUT/'Chibi_Topology_Corrigida.glb'),
    export_format='GLB',use_selection=True,export_apply=False,export_cameras=False,export_lights=False,
    export_morph=False)
bpy.ops.wm.obj_export(filepath=str(OUT/'Chibi_Topology_Corrigida.obj'),export_selected_objects=True,
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
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Chibi_Topology_Corrigida.blend'))
print('MODEL COMPLETE',len(mesh.vertices),'vertices',len(mesh.polygons),'faces')
