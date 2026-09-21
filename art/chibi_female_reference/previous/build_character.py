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

# Work in a convenient facial coordinate frame, then scale the head to the
# measured front elevation: width 1.28, height 1.30, total height 3.60.
def hc(x,y,z): return (x*1.09,y*1.03,2.30+(z-2.465)*(1.30/1.135))
def hv(co,region): return vertex(hc(*co),region)
profiles=[(2.465,.205,.174,-.04),(2.49,.293,.24,-.035),(2.54,.384,.324,-.015),
 (2.60,.454,.398,-.006),(2.67,.498,.438,-.006),(2.73,.533,.468,-.007),
 (2.79,.555,.489,-.008),(2.85,.570,.507,-.008),(2.91,.578,.518,-.006),
 (2.97,.582,.522,-.005),(3.03,.584,.523,-.003),(3.09,.586,.523,.001),
 (3.15,.585,.522,.006),(3.22,.576,.513,.012),(3.30,.550,.493,.018),
 (3.38,.501,.452,.026),(3.45,.439,.398,.032),(3.51,.361,.328,.038),
 (3.555,.271,.250,.04),(3.585,.170,.164,.041),(3.60,.060,.064,.041)]
def face_y(x,z):
    rx=interp(z,[(p[0],p[1]) for p in profiles]); ry=interp(z,[(p[0],p[2]) for p in profiles])
    cy=interp(z,[(p[0],p[3]) for p in profiles]); c=min(.9999,abs(x)/rx)**(1/.92)
    y=cy-ry*(max(0,1-c*c)**.5)**.65
    y-=.092*math.exp(-(x/.070)**2-((z-2.805)/.063)**2)
    y-=.024*math.exp(-((abs(x)-.30)/.18)**2-((z-2.73)/.11)**2)
    return y
head=[]
raw_head={}
for z,rx,ry,cy in profiles:
    ring=[]
    for j in range(48):
        a=math.tau*j/48; sy=math.sin(a)
        x=rx*math.copysign(abs(math.cos(a))**.92,math.cos(a))
        y=cy+ry*math.copysign(abs(sy)**.65,sy)
        if sy<-.65: y=face_y(x,z)
        idx=hv((x,y,z),'Head / cranium'); raw_head[idx]=(x,y,z); ring.append(idx)
    head.append(ring)
cuts=[('Eye.L',5,12,37,43),('Eye.R',5,12,29,35),('Mouth',3,5,34,38),('Nose',5,8,35,37),
      ('Ear.L',5,9,47,49),('Ear.R',5,9,23,25)]
for r in range(len(head)-1):
    for c in range(48):
        skip=any(r0<=r<r1 and c in [k%48 for k in range(c0,c1)] for _,r0,r1,c0,c1 in cuts)
        if not skip: faces.append((head[r][c],head[r][(c+1)%48],head[r+1][(c+1)%48],head[r+1][c]))
for i in range(16):
    ids=[head[0][(3*i+k-1)%48] for k in range(3)]
    faces.append((neck[i],neck[(i+1)%16],head[0][(3*(i+1)-1)%48],ids[-1]))
    faces.append((neck[i],*ids))
cap(head[-1])
def boundary(r0,r1,c0,c1):
    return ([head[r0][c%48] for c in range(c0,c1+1)]+[head[r][c1%48] for r in range(r0+1,r1+1)]+
            [head[r1][c%48] for c in range(c1-1,c0-1,-1)]+[head[r][c0%48] for r in range(r1-1,r0,-1)])
eye_centers=[]
for name,r0,r1,c0,c1 in cuts:
    previous=boundary(r0,r1,c0,c1)
    if name.startswith('Eye'):
        side=1 if name.endswith('L') else -1; cx=side*.268; cz=2.945
        angles=[math.atan2((raw_head[i][2]-cz)/.19,(raw_head[i][0]-cx)/.20) for i in previous]
        for rx,rz,mode,off in ((.171,.175,'face',-.001),(.162,.164,'face',-.012),
                (.148,.151,'rim',0),(.144,.147,'rim',.008),(.187,.187,'bowl',-.315),
                (.116,.116,'bowl',-.170),(.038,.038,'bowl',-.145)):
            ring=[]
            for a in angles:
                x=cx+rx*math.cos(a); z=cz+rz*math.sin(a)
                y=face_y(x,z)+off if mode=='face' else (-.522+side*.16*(x-cx)+off if mode=='rim' else off+side*.16*(x-cx))
                ring.append(hv((x,y,z),'Head / eyelids & sockets.'+name[-1]))
            bridge(previous,ring); previous=ring
        cap(previous); eye_centers.append((side,(cx,-.461,cz)))
    elif name=='Mouth':
        angles=[math.atan2((raw_head[i][2]-2.688)/.07,raw_head[i][0]/.17) for i in previous]
        for rx,rz,yy in ((.146,.036,None),(.112,.025,-.486),(.092,.009,-.489),
                         (.086,.007,-.465),(.064,.014,-.406),(.022,.007,-.395)):
            ring=[]
            for a in angles:
                x=rx*math.cos(a); z=2.688+rz*math.sin(a)+.003*(x/rx)**2
                y=face_y(x,z)-.004 if yy is None else yy
                ring.append(hv((x,y,z),'Head / lips & mouth'))
            bridge(previous,ring); previous=ring
        cap(previous)
    elif name=='Nose':
        angles=[math.atan2((raw_head[i][2]-2.807)/.10,raw_head[i][0]/.086) for i in previous]
        for rx,rz,yy in ((.080,.066,-.531),(.068,.050,-.568),(.047,.031,-.600),(.020,.014,-.610)):
            ring=[]
            for a in angles: ring.append(hv((rx*math.cos(a),yy,2.800+rz*math.sin(a)),'Head / nose'))
            bridge(previous,ring); previous=ring
        cap(previous)
    else:
        side=1 if name.endswith('L') else -1
        center=Vector((side*.632,0,2.847)); axis=Vector((side*.65,.760,0)); normal=Vector((side*.760,-.65,0))
        angles=[math.atan2((raw_head[i][2]-2.847)/.12,raw_head[i][1]/.09) for i in previous]
        for rx,rz,depth in ((.112,.181,0),(.102,.170,.031),(.077,.143,.049),
                             (.057,.109,-.004),(.037,.068,-.039),(.015,.027,-.044)):
            ring=[]
            for a in angles:
                # A fuller upper helix, tapered lobule and recessed concha
                # create the C-shaped ear seen in the reference closeups.
                upper=math.sin(a)
                u=rx*math.cos(a)*(1+.10*upper)+.09*rz*upper
                co=center+axis*u+Vector((0,0,rz*upper))+normal*depth
                if rx<=.057:
                    angle=math.atan2(math.sin(a-math.pi),math.cos(a-math.pi))
                    tragus=math.exp(-(angle/.70)**2)*(rx/.057)
                    co+=normal*(.078*tragus)+axis*(.023*tragus)
                ring.append(hv(co,'Head / ears.'+name[-1]))
            bridge(previous,ring); previous=ring
        cap(previous)

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
def subdiv(obj,levels=1):
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
            ev.append(hc(*(center+axis*(.100*math.cos(phi))+hor*(.181*math.sin(phi)*math.cos(a))+
                           Vector((0,0,.181*math.sin(phi)*math.sin(a))))))
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
    for i in range(11):
        t=i/10; x=side*(.128+.303*t); z=3.222+.027*math.sin(math.pi*t)-.008*t
        centers.append((x,face_y(x,z)-.011,z)); widths.append(.003+.014*math.sin(math.pi*t)**.7)
    tube_ribbon('Sobrancelha.'+suffix,centers,widths,.004)
    vv=[]; ff=[]
    for i in range(17):
        a=.07+(math.pi-.14)*i/16
        for r in (0,1):
            x=center[0]+(.147+.015*r)*math.cos(a); z=center[2]+(.149+.026*r)*math.sin(a)
            y=-.533+side*.16*(x-center[0])
            vv.append(hc(x,y,z))
    for i in range(16): ff.append((2*i,2*i+1,2*i+3,2*i+2))
    lid=make_mesh('Palpebra superior.'+suffix,vv,ff); lid.data.materials.append(clay)
    sol=lid.modifiers.new('Espessura','SOLIDIFY'); sol.thickness=.005
    subdiv(lid); parts.append(lid)
    for k,(a,length) in enumerate(((.30,.080),(.72,.075))):
        x=center[0]+side*.150*math.cos(a); z=center[2]+.156*math.sin(a)
        y=-.543+side*.16*(x-center[0]); pts=[]; ws=[]
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

# Draw only the original edge paths on the Catmull-Clark surface. Each control
# edge becomes two segments, omitting the extra face-center edges in preview.
bpy.context.view_layer.update(); curves=bpy.data.curves.new('Arestas de preview','CURVE')
curves.dimensions='3D'; curves.bevel_depth=.00065; curves.bevel_resolution=0
for obj in parts:
    bm=bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    smooth=any(m.type=='SUBSURF' for m in obj.modifiers)
    offset=.0065 if any(m.type=='SOLIDIFY' for m in obj.modifiers) else .0008
    fc={f:f.calc_center_median() for f in bm.faces}
    vc={}
    for v in bm.verts:
        if not smooth: vc[v]=v.co.copy(); continue
        borders=[e.other_vert(v).co for e in v.link_edges if e.is_boundary]
        if len(borders)==2: vc[v]=v.co*.75+(borders[0]+borders[1])*.125
        else:
            n=len(v.link_edges); fav=sum((fc[f] for f in v.link_faces),Vector())/len(v.link_faces)
            rav=sum(((v.co+e.other_vert(v).co)/2 for e in v.link_edges),Vector())/n
            vc[v]=(fav+2*rav+(n-3)*v.co)/n
    for e in bm.edges:
        a,b=e.verts
        mid=(a.co+b.co+sum((fc[f] for f in e.link_faces),Vector()))/4 if smooth and len(e.link_faces)==2 else (a.co+b.co)/2
        sp=curves.splines.new('POLY'); sp.points.add(2 if smooth else 1)
        positions=[vc[a]+a.normal*offset,mid+(a.normal+b.normal)*offset/2,vc[b]+b.normal*offset] if smooth else [vc[a]+a.normal*offset,vc[b]+b.normal*offset]
        for p,co in zip(sp.points,positions): p.co=(*co,1)
    bm.free()
wire=bpy.data.objects.new('Topologia - apenas render',curves); stage.objects.link(wire); curves.materials.append(wire_mat)
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
    scene.render.resolution_x=1400; scene.render.resolution_y=1400; scene.render.resolution_percentage=100
    scene.render.filepath=str(OUT/(name+'.png')); wire.hide_render=not topology
    if '--no-render' not in sys.argv and ('--face-only' not in sys.argv or name in ('face_front','face_three_quarter')):
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
for source in (Path(__file__).resolve(),base_source): bpy.data.texts.load(str(source))
info=bpy.data.texts.new('LEIA-ME.txt')
info.write('CHIBI FEMININA / NOVE REFERENCIAS\n\n'
 'Corpo, cabeca, nariz, labios e orelhas integrados. Olhos, cilios, sobrancelhas e roupas separados.\n'
 'Subdivisao 1 editavel; Tab abre a malha de controle. UVs incluidas. Sem rig.\n'
 'Top e short podem ser ocultados no Outliner. Frente -Y, cima Z.\n'
 'As nove imagens de referencia estao empacotadas no projeto.\n'
 'GLB inclui a subdivisao. OBJ mantem os quads de controle.\n')
scene['reference_sizes']=json.dumps(ref_sizes)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Chibi_Feminina.blend'))
print('CHIBI_FEMININA_COMPLETE',len(body.data.vertices),len(body.data.polygons))
