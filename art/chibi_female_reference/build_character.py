"""Blender generator for the nine September 17 reference images.
Run: blender -b -t 6 --python-exit-code 1 -P build_character.py
Use -- --no-render to skip previews; -- --face-only to render only the face.
"""
import bpy, bmesh, math, sys, json
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

OUT=Path(__file__).resolve().parent
REFDIR=Path('C:/Users/obran/OneDrive/Área de Trabalho/referencias')
base_source=OUT/'base_geometry.py'
ns={'__file__':str(base_source),'__name__':'base_geometry'}
exec(compile(base_source.read_text(encoding='utf-8'),str(base_source),'exec'),ns)
scene=ns['scene']
scene.name='Chibi Feminina - Nove Referencias'
model_group,stage,reference_group=(ns[n] for n in ('model_group','stage','reference_group'))
verts,faces,regions=ns['verts'],ns['faces'],ns['regions']
neck=ns['body'][-1]
old_head=set(regions.pop('Head'))
faces=[f for f in faces if not old_head.intersection(f)]

def vertex(co,region):
    i=len(verts); verts.append(tuple(co)); regions.setdefault(region,[]).append(i)
    return i
def bridge(a,b):
    assert len(a)==len(b)
    for i in range(len(a)):
        j=(i+1)%len(a); faces.append((a[i],a[j],b[j],b[i]))
def cap(loop):
    center=vertex(sum((Vector(verts[i]) for i in loop),Vector())/len(loop),'Head / caps')
    for i in range(0,len(loop),2): faces.append((center,loop[i],loop[(i+1)%len(loop)],loop[(i+2)%len(loop)]))
def interp(v,knots):
    if v<=knots[0][0]: return knots[0][1]
    for (a,x),(b,y) in zip(knots,knots[1:]):
        if v<=b: return x+(y-x)*(v-a)/(b-a)
    return knots[-1][1]

arm_ids={}; leg_ids=set(); knee_ids=set(); thumb_drop={}; palm_ids=set()
for name,ids in regions.items():
    if name.startswith(('Arm.','Hand /','Finger /')):
        for i in ids: arm_ids[i]=1 if name.endswith('.L') else -1
    if name.startswith(('Leg & foot.','Knee /')): leg_ids.update(ids)
    if name.startswith('Knee /'): knee_ids.update(ids)
    if name.startswith('Hand /'): palm_ids.update(ids)
    if name.startswith('Finger / thumb.'):
        for k,i in enumerate(ids): thumb_drop[i]=.115*(k//8)/max(1,len(ids)//8-1)
height_map=[(0,0),(2.04,1.23),(2.54,1.68),(2.98,1.96),(3.205,2.12),(3.265,2.145),(3.30,2.22),(3.35,2.32)]
for i,(x,y,z) in enumerate(verts):
    if i in old_head: continue
    if i in arm_ids:
        side=arm_ids[i]
        d=Vector((x,y,z))-Vector((side*.321,0,3.130))
        f=Vector((side*.806,0,-.592)); u=Vector((side*.592,0,.806))
        t=d.dot(f)/f.length_squared; h=d.dot(u)/u.length_squared
        length=t*.96 if t<.805 else .805*.96+(t-.805)*1.30
        scale=interp(t,[(.09,1.3),(.20,1.5),(.50,1.85),(.72,2.15),(.805,2.20),(.855,2.0)])
        bump=.022*math.exp(-((t-.985)/.13)**2) if t>.805 else 0
        fullness=1.80 if i in palm_ids else 1.18 if t<.805 else 1.45
        curl=.050*max(0,min(1,(t-1.00)/.28))**1.4 if i not in thumb_drop else 0
        depth_scale=1.10 if t<.805 else interp(t,[(.805,1.10),(.92,1.15),(1.10,1.10)])
        verts[i]=(side*(.260+length),y*scale*depth_scale,2.005+h*scale*fullness+bump-thumb_drop.get(i,0)-curl)
    else:
        if i in leg_ids:
            side=1 if x>0 else -1
            cx=interp(z,sorted((p[0],p[1]) for p in ns['leg_profiles']))
            factor=interp(z,[(0,1),(.19,1),(.43,1.25),(.635,1.45),(1.165,1.50),(1.365,1.42),(1.56,1.3),(1.865,1.15),(1.98,1.10)])
            if i in knee_ids:
                x=side*(cx+(abs(x)-cx)*factor*.70); z=1.365+(z-1.365)*.75
                y+=.017
            else: x=side*(cx+(abs(x)-cx)*factor)
        if i in ns['body'][8]: x*=.54; y*=.80
        verts[i]=(x*.80,y*.90,interp(z,height_map))

sys.path.insert(0,str(OUT))
from refine_body import rebuild_legs
from refine_arms import refine_arms
faces=rebuild_legs(verts,faces,regions,ns)
refine_arms(verts,faces,regions,ns)
# One waist row follows the gentle inward curve visible between top and hips.
a,b=ns['body'][2],ns['body'][3]
middle=[]
for va,vb in zip(a,b):
    co=(Vector(verts[va])+Vector(verts[vb]))*.5
    co.x*=.94
    middle.append(vertex(co,'Torso & neck'))
old_band={frozenset((a[i],a[(i+1)%16],b[(i+1)%16],b[i])) for i in range(16)}
faces=[f for f in faces if frozenset(f) not in old_band]
bridge(a,middle); bridge(middle,b)
from reference_head import build_head
hc,hv,face_y,eye_centers=build_head(verts,faces,regions,neck,interp)
def make_mesh(name,vertices,polygons,collection=model_group):
    data=bpy.data.meshes.new(name+' mesh'); data.from_pydata(vertices,[],polygons); data.update()
    bm=bmesh.new(); bm.from_mesh(data)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(data); bm.free(); data.update()
    obj=bpy.data.objects.new(name,data); collection.objects.link(obj)
    for p in data.polygons: p.use_smooth=True
    return obj
def material(name,color,rough=.78):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    return m
clay=material('Argila cinza',(.44,.47,.46)); eye_mat=material('Olhos - argila',(.46,.49,.48))
wire_mat=material('Topologia',(.025,.033,.031)); garment_mat=material('Roupa - argila',(.45,.48,.47))
body=make_mesh('Chibi - corpo e cabeca',verts,faces); body.data.materials.append(clay)
body.show_wire=True; body.show_all_edges=True
body['description']='Reconstrucao das nove referencias em alta resolucao; frente -Y, cima Z.'
body['rig']='Sem rig. Malha quad, UVs e subdivisao editavel.'
for name,ids in regions.items():
    group=body.vertex_groups.new(name=name); coords={tuple(round(c,6) for c in verts[i]) for i in ids}
    indices=[v.index for v in body.data.vertices if tuple(round(c,6) for c in v.co) in coords]
    if indices: group.add(indices,1,'REPLACE')
parts=[body]
def subdiv(obj,levels=2):
    mod=obj.modifiers.new('Subdivisao editavel','SUBSURF'); mod.levels=levels; mod.render_levels=levels
    mod.show_only_control_edges=True
    mod.use_limit_surface=False
subdiv(body)

# The reference eyeballs are untextured, with radial sphere topology.
for side,center in eye_centers:
    ev=[]; ef=[]; center=Vector(center); axis=Vector((side*.07,-.9975,0)).normalized()
    hor=Vector((.9975,side*.07,0)).normalized(); n=32
    polar=(.026,.40,.78,1.10,1.40,1.70,2.03,2.36,2.70,2.96,3.10)
    for phi in polar:
        for k in range(n):
            a=math.tau*k/n
            ev.append(hc(*(center+axis*(.095*math.cos(phi))+hor*(.175*math.sin(phi)*math.cos(a))+
                           Vector((0,0,.167*math.sin(phi)*math.sin(a))))))
    for r in range(len(polar)-1):
        for k in range(n):
            j=(k+1)%n; ef.append((r*n+k,r*n+j,(r+1)*n+j,(r+1)*n+k))
    for start in (0,(len(polar)-1)*n):
        for k in range(1,n-2,2): ef.append((start,start+k,start+k+1,start+k+2))
    eye=make_mesh('Olho.'+('L' if side>0 else 'R'),ev,ef); eye.data.materials.append(eye_mat); parts.append(eye)

# Brows and the upper eyelid strips, with two small stylized lashes per eye.
def tube_ribbon(name,centers,widths,depth=.006):
    vv=[]; ff=[]
    for (x,y,z),w in zip(centers,widths):
        for dy,dz in ((-depth,-w),(-depth,w),(depth,w),(depth,-w)): vv.append(hc(x,y+dy,z+dz))
    for r in range(len(centers)-1):
        for k in range(4): ff.append((4*r+k,4*r+(k+1)%4,4*(r+1)+(k+1)%4,4*(r+1)+k))
    ff.extend([(3,2,1,0),tuple(4*(len(centers)-1)+k for k in range(4))])
    obj=make_mesh(name,vv,ff); obj.data.materials.append(clay); subdiv(obj); parts.append(obj)
for side,center in eye_centers:
    suffix='L' if side>0 else 'R'; centers=[]; widths=[]
    for i in range(7):
        t=i/6; x=side*(.128+.303*t); z=3.222+.027*math.sin(math.pi*t)-.008*t
        centers.append((x,face_y(x,z)-.011,z)); widths.append(.003+.014*math.sin(math.pi*t)**.7)
    tube_ribbon('Sobrancelha.'+suffix,centers,widths,.004)
    vv=[]; ff=[]
    for i in range(17):
        a=.07+(math.pi-.14)*i/16
        for r in (0,1):
            x=center[0]+(.153+.017*r)*math.cos(a); z=center[2]+(.146+.023*r)*math.sin(a)
            y=-.512+side*.16*(x-center[0])
            vv.append(hc(x,y,z))
    for i in range(16): ff.append((2*i,2*i+1,2*i+3,2*i+2))
    lid=make_mesh('Palpebra superior.'+suffix,vv,ff); lid.data.materials.append(clay)
    sol=lid.modifiers.new('Espessura','SOLIDIFY'); sol.thickness=.005
    subdiv(lid); parts.append(lid)
    for k,(a,length) in enumerate(((.30,.080),(.72,.075))):
        x=center[0]+side*.150*math.cos(a); z=center[2]+.156*math.sin(a)
        y=-.522+side*.16*(x-center[0]); pts=[]; ws=[]
        for t in (0,.25,.55,.8,1):
            pts.append((x+side*length*t,y-.013*t,z+(.034 if k==0 else .055)*t))
            ws.append(.020*math.sin(math.pi*(.18+.82*t))+.001)
        tube_ribbon('Cilio_%d.%s'%(k+1,suffix),pts,ws,.005)

# Separate strapless top and briefs, visible as removable parts in the sheet.
vv=[]; ff=[]; n=16
for r,(z,rx,ry) in enumerate(((1.779,.215,.156),(1.792,.235,.171),(1.876,.253,.185),(1.967,.238,.177),(1.982,.218,.160))):
    for k in range(n):
        a=math.tau*k/n; x=rx*math.cos(a); y=ry*math.sin(a); zz=z
        if y<0:
            y-=.024*math.exp(-((abs(x)-.113)/.070)**2)
            if r>=3: zz+=.012*math.sin(math.pi*abs(x)/rx)-.016*math.exp(-(x/.06)**2)
            if r<=1: zz+=.009*math.exp(-(x/.065)**2)
        vv.append((x,y-.015,zz))
for r in range(4):
    for k in range(n): ff.append((r*n+k,r*n+(k+1)%n,(r+1)*n+(k+1)%n,(r+1)*n+k))
top=make_mesh('Top - peca separada',vv,ff); top.data.materials.append(garment_mat)
sol=top.modifiers.new('Tecido','SOLIDIFY'); sol.thickness=.010; sol.offset=0
subdiv(top); parts.append(top)

body.data.update(); bpy.context.view_layer.update()
evbody=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); surf=evbody.to_mesh()
skin=BVHTree.FromPolygons([v.co for v in surf.vertices],[list(p.vertices) for p in surf.polygons])
evbody.to_mesh_clear()
pv=[]; pf=[]; remap={}
for p in body.data.polygons:
    cs=[body.data.vertices[i].co for i in p.vertices]
    if min(c.z for c in cs)>=1.190 and max(c.z for c in cs)<=1.515:
        face=[]
        for idx in p.vertices:
            if idx not in remap:
                v=body.data.vertices[idx]; co=v.co.copy(); t=max(0,min(1,(co.z-1.194)/.316))
                lower=1.215+.60*abs(co.x); co.z=lower+(1.515-lower)*t
                co.x*=1.025; co.y*=1.09
                near,normal,_,_=skin.find_nearest(co)
                if near is not None: co=near+normal*.012
                remap[idx]=len(pv); pv.append(co)
            face.append(remap[idx])
        pf.append(face)
briefs=make_mesh('Short - peca separada',pv,pf); briefs.data.materials.append(garment_mat)
sol=briefs.modifiers.new('Tecido','SOLIDIFY'); sol.thickness=.008; sol.offset=0
subdiv(briefs); parts.append(briefs)

# UV unwrap each control mesh before export; subdivision stays editable.
root=bpy.data.objects.new('Character_Root',None); model_group.objects.link(root)
root.empty_display_size=.20
root['instructions']='Mova este objeto para mover o personagem inteiro, incluindo olhos e roupas.'
for obj in parts: obj.parent=root
for obj in parts:
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(64),island_margin=.015); bpy.ops.object.mode_set(mode='OBJECT')

ref_sizes={}
for num,path in enumerate(sorted(REFDIR.glob('cartoon-female-chibi-character-base-mesh-*.jpg'))):
    im=bpy.data.images.load(str(path)); im.pack(); im.use_fake_user=True; ref_sizes[path.name]=list(im.size)
    ref=bpy.data.objects.new('Referencia %02d'%(num+1),None); reference_group.objects.link(ref)
    ref.empty_display_type='IMAGE'; ref.data=im; ref.empty_display_size=2
    ref.location=(3+(num%3)*2.2,1,3-(num//3)*1.7); ref.rotation_euler.x=math.pi/2; ref.hide_render=True
reference_group.hide_viewport=True; reference_group.hide_render=True

# Preserve original control-edge density on the actual smooth surface.
from smooth_preview import make_wire_overlay
bpy.context.view_layer.update()
wire=make_wire_overlay(parts,stage,wire_mat)
world=bpy.data.worlds.new('Estudio cinza'); world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.043,.047,.045,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7; scene.world=world
def aim(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('Principal',(-3,-5,6),400,4),('Preenchimento',(4,-3,4),220,4),('Recorte',(2,4,5),400,4)]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.size=size
    obj=bpy.data.objects.new(name,data); stage.objects.link(obj); obj.location=loc; aim(obj,(0,0,2))
camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera')); stage.objects.link(camera)
camera.data.type='ORTHO'; camera.data.clip_end=100; scene.camera=camera
scene.cycles.samples=32; scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='Standard'
def render(name,loc,target=(0,0,1.80),scale=4.10,topology=True):
    camera.location=loc; aim(camera,target); camera.data.ortho_scale=scale
    size=900 if '--quick' in sys.argv else 1400
    scene.render.resolution_x=size; scene.render.resolution_y=size; scene.render.resolution_percentage=100
    scene.cycles.samples=16 if '--quick' in sys.argv else 32
    scene.render.filepath=str(OUT/(name+'.png')); wire.hide_render=not topology
    if '--no-render' not in sys.argv and ('--face-only' not in sys.argv or name in ('face_front','face_three_quarter')) and ('--quick' not in sys.argv or name in ('front','side','face_front','clay')):
        bpy.ops.render.render(write_still=True)
render('front',(0,-10,1.80)); render('side',(-10,0,1.80)); render('back',(0,10,1.80))
render('three_quarter',(5,-9,3.7),scale=4.20)
render('face_front',(0,-8,2.965),target=(0,0,2.965),scale=1.85)
render('face_three_quarter',(4,-8,3.4),target=(0,0,2.965),scale=1.95)
render('clay',(5,-9,3.7),scale=4.20,topology=False); wire.hide_render=False

bpy.ops.object.select_all(action='DESELECT')
for obj in parts: obj.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(OUT/'Chibi_Feminina.glb'),export_format='GLB',use_selection=True,
                         export_apply=True,export_cameras=False,export_lights=False)
bpy.ops.wm.obj_export(filepath=str(OUT/'Chibi_Feminina.obj'),export_selected_objects=True,apply_modifiers=False,
                     export_materials=True,export_triangulated_mesh=False)
for obj in parts: obj.select_set(obj==body)
camera.location=(5,-9,3.7); aim(camera,(0,0,1.80)); camera.data.ortho_scale=4.20
scene.render.filepath=str(OUT/'three_quarter.png')
for obj in stage.objects: obj.hide_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active; sp.shading.type='SOLID'; sp.shading.light='STUDIO'; sp.shading.color_type='MATERIAL'
            sp.shading.show_cavity=True; sp.overlay.show_floor=False; sp.overlay.show_axis_x=False; sp.overlay.show_axis_y=False
            sp.region_3d.view_location=(0,0,1.80); sp.region_3d.view_distance=5.5
            sp.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2); sp.region_3d.view_perspective='ORTHO'
for source in (Path(__file__).resolve(),base_source,OUT/'reference_head.py',OUT/'refine_body.py',OUT/'refine_arms.py',OUT/'smooth_preview.py'):
    bpy.data.texts.load(str(source))
info=bpy.data.texts.new('LEIA-ME.txt')
info.write('CHIBI FEMININA / NOVE REFERENCIAS\n\n'
 'Corpo, cabeca, nariz, labios e orelhas integrados. Olhos, cilios, sobrancelhas e roupas separados.\n'
 'Subdivisao 2 editavel; Tab abre a malha de controle. UVs incluidas. Sem rig.\n'
 'Top e short podem ser ocultados no Outliner. Frente -Y, cima Z.\n'
 'As nove imagens de referencia estao empacotadas no projeto.\n'
 'GLB inclui a subdivisao. OBJ mantem os quads de controle.\n')
scene['reference_sizes']=json.dumps(ref_sizes)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Chibi_Feminina.blend'))
print('CHIBI_FEMININA_COMPLETE',len(body.data.vertices),len(body.data.polygons))
