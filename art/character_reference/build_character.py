import bpy, math, random, os
from mathutils import Vector
from math import sin, cos, pi, sqrt
random.seed(24)
OUT = os.path.join(os.getcwd(), 'art', 'character_reference')
REF = r'C:\Users\20240054\Downloads\WhatsApp Image 2026-09-10 at 11.06.43.jpeg'
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):
    if col.name != 'Collection' and col.users == 0: bpy.data.collections.remove(col)
root = bpy.data.collections.get('Collection')
root.name = 'CHARACTER'
COLS = {}
for name in ['01_BODY','02_FACE','03_HAIR','04_OUTFIT','05_SHOES','06_RIBBON','REFERENCES','STUDIO']:
    c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); COLS[name]=c

def move(obj, group):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    COLS[group].objects.link(obj)
    return obj

def mat(name, color, rough=.45, metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metallic
    return m
skin=mat('Skin | warm caramel',(.56,.275,.135),.48)
skin.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.065
inner=mat('Ear and cheek warmth',(.48,.17,.10),.6)
dark=mat('Lashes and mouth | deep cocoa',(.055,.016,.012),.55)
white=mat('Eye whites | warm ivory',(.89,.80,.65),.24)
highlight=mat('Eye catchlight',(.98,.97,.9),.15)
bs=highlight.node_tree.nodes.get('Principled BSDF'); bs.inputs['Emission Color'].default_value=(1,.94,.79,1); bs.inputs['Emission Strength'].default_value=.25
iris_outer=mat('Iris | dark honey rim',(.21,.065,.012),.25)
iris=mat('Iris | amber',(.66,.25,.026),.25)
iris_light=mat('Iris | golden inner ring',(.95,.54,.09),.3)
pupil=mat('Pupils',(.014,.005,.003),.18)
purple=mat('Jumpsuit | aubergine cotton',(.105,.032,.22),.68)
nodes=purple.node_tree.nodes; links=purple.node_tree.links; bs=nodes.get('Principled BSDF')
noise=nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=155; noise.inputs['Detail'].default_value=2
bump=nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.14; bump.inputs['Distance'].default_value=.012
links.new(noise.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs['Normal'],bs.inputs['Normal'])
seam=mat('Purple seams',(.16,.065,.29),.7)
gold=mat('Antique gold hardware',(.72,.40,.085),.28,.65)
ribbon=mat('Ribbon | warm white satin',(.88,.855,.74),.32)
shoe=mat('Shoes | golden ochre leather',(.69,.37,.075),.38)
sole=mat('Soles | warm cream rubber',(.76,.61,.35),.65)
hairs=[mat('Curls | chestnut %02d'%i,(.16+i*.013,.047+i*.0058,.019+i*.0028),.57) for i in range(7)]
hair_line=mat('Hair grooves',(.09,.023,.012),.5)
slick=mat('Swept hair | copper brown',(.22,.062,.024),.43)

# Modeling helpers: named mesh objects and curves remain independently editable.
def finish(obj,name,material,group):
    obj.name=name; move(obj,group)
    if material: obj.data.materials.append(material)
    if obj.type=='MESH':
        for f in obj.data.polygons: f.use_smooth=True
    return obj

def uv(name, loc, scale, material, group='01_BODY', seg=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    ob=bpy.context.object; ob.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(ob,name,material,group)

def mesh(name, verts, faces, material, group, sub=0):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); COLS[group].objects.link(obj)
    if material: data.materials.append(material)
    for f in data.polygons: f.use_smooth=True
    if sub:
        m=obj.modifiers.new('Soft subdivision','SUBSURF');m.levels=sub;m.render_levels=sub
    return obj

def curve(name, points, radius, material, group, radii=None, cyclic=False):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=16
    data.bevel_depth=radius;data.bevel_resolution=3
    sp=data.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for i,(bp,p) in enumerate(zip(sp.bezier_points,points)):
        bp.co=p;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
        if radii: bp.radius=radii[i]
    sp.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(name,data);COLS[group].objects.link(ob);data.materials.append(material)
    return ob

def tube_between(name,a,b,r1,r2,material,group):
    d=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))*.5
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r1, radius2=r2, depth=d.length, location=mid)
    ob=bpy.context.object;ob.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    finish(ob,name,material,group)
    mod=ob.modifiers.new('Rounded ends','BEVEL');mod.width=.055;mod.segments=3
    return ob

def loft(name, sections, material,group,sub=2,n=32):
    # Each section: z, center_x, center_y, half_width, half_depth.
    v=[]
    for z,x,y,w,d in sections:
        for j in range(n):
            t=2*pi*j/n;v.append((x+w*cos(t),y+d*sin(t),z))
    f=[]
    for i in range(len(sections)-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f += [tuple(reversed(range(n))),tuple((len(sections)-1)*n+j for j in range(n))]
    return mesh(name,v,f,material,group,sub)

def torus(name,loc,major,minor,material,group,rotation=(pi/2,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=10,location=loc,major_radius=major,minor_radius=minor,rotation=rotation)
    return finish(bpy.context.object,name,material,group)

# Head: rounded forehead, soft cheek volume, gently narrowed chin.
HEAD_Z=3.61
v=[]; f=[];n=64;nr=40
for i in range(nr+1):
    ph=pi*i/nr; z=cos(ph);jaw=1-.18*max(0,-z)
    for j in range(n):
        th=2*pi*j/n
        v.append((.70*sin(ph)*cos(th)*jaw,.49*sin(ph)*sin(th),HEAD_Z+.72*z))
for i in range(nr):
    for j in range(n):
        a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
mesh('Head | shaped cheeks and chin',v,f,skin,'01_BODY',1)
uv('Neck',(0,0,2.99),(.155,.155,.25),skin)
for sign,side in [(-1,'L'),(1,'R')]:
    uv('Ear '+side,(sign*.665,.012,3.57),(.14,.10,.205),skin)
    uv('Ear inset '+side,(sign*.701,-.07,3.57),(.065,.036,.117),inner,'02_FACE')
    tube_between('Upper arm '+side,(sign*.45,0,2.80),(sign*.65,-.015,2.42),.135,.16,skin,'01_BODY')
    tube_between('Forearm '+side,(sign*.65,-.015,2.44),(sign*.76,-.055,2.17),.137,.14,skin,'01_BODY')
    uv('Hand nub '+side,(sign*.785,-.065,2.105),(.185,.16,.20),skin)
    uv('Thumb nub '+side,(sign*.665,-.13,2.16),(.076,.078,.105),skin)
    uv('Leg base '+side,(sign*.265,0,1.28),(.205,.205,.90),skin)
uv('Torso base',(0,0,2.53),(.43,.255,.51),skin)

# Face components conform to the head surface.
def fy(x,z):
    zn=(z-HEAD_Z)/.72; jaw=1-.18*max(0,-zn)
    return -.49*sqrt(max(.035,1-(x/(.70*jaw))**2-zn**2))
def face_curve(name,xzs,r,material,radii=None):
    return curve(name,[(x,fy(x,z)-.032,z) for x,z in xzs],r,material,'02_FACE',radii)
for sign,side in [(-1,'L'),(1,'R')]:
    cx=sign*.295;cz=3.70;hw=.235;hh=.154
    verts=[(cx,fy(cx,cz)-.053,cz)];boundary=[]
    for j in range(64):
        t=2*pi*j/64;x=cx+hw*cos(t);z=cz+hh*sin(t)*(.85+.15*abs(sin(t)))+sign*(x-cx)*.11
        boundary.append((x,fy(x,z)-.034,z));verts.append(boundary[-1])
    mesh('Almond eye white '+side,verts,[(0,j+1,(j+1)%64+1) for j in range(64)],white,'02_FACE')
    # Slightly protruding lenses sit inside the almond outline.
    iy=fy(cx,cz)-.066
    uv('Amber iris rim '+side,(cx,iy,cz),(.117,.037,.147),iris_outer,'02_FACE')
    uv('Amber iris '+side,(cx,iy-.027,cz),(.099,.019,.131),iris,'02_FACE')
    uv('Golden iris lower glow '+side,(cx,iy-.043,cz-.039),(.079,.012,.083),iris_light,'02_FACE')
    uv('Pupil '+side,(cx,iy-.055,cz+.008),(.055,.013,.102),pupil,'02_FACE')
    uv('Main eye glint '+side,(cx-.029,iy-.070,cz+.068),(.032,.009,.043),highlight,'02_FACE',24,16)
    uv('Small eye glint '+side,(cx+.038,iy-.065,cz-.06),(.016,.009,.022),highlight,'02_FACE',20,12)
    top=[];bot=[]
    for j in range(13):
        t=pi*j/12;x=cx+hw*cos(t)
        top.append((x,cz+hh*sin(t)*(.85+.15*sin(t))+sign*(x-cx)*.11))
        bot.append((x,cz-hh*sin(t)*(.85+.15*sin(t))+sign*(x-cx)*.11))
    face_curve('Upper eyelid '+side,top,.025,dark,[.4]+[1]*11+[.4])
    face_curve('Lower eyelid '+side,bot,.010,dark,[.2]+[.7]*11+[.2])
    outer=cx+sign*hw
    for k in range(3):
        x=outer-sign*k*.033;z=cz+.015+k*.033
        face_curve('Eyelash '+side+str(k),[(x,z),(x+sign*.058,z+.036),(x+sign*.087,z+.073)],.020,dark,[.9,.7,.04])
    face_curve('Expressive brow '+side,[(sign*.13,3.962),(sign*.28,4.007),(sign*.46,4.009),(sign*.53,3.982)],.036,slick,[.45,1,.75,.1])
    # Two short warm cheek marks, kept understated.
    for k in range(2):
        x=sign*(.435+k*.042);face_curve('Cheek accent '+side+str(k),[(x,3.468),(x+sign*.014,3.44)],.009,inner)
uv('Small button nose',(0,fy(0,3.48)-.005,3.48),(.047,.062,.059),skin,'02_FACE')
face_curve('Small smiling mouth',[(-.195,3.322),(-.11,3.293),(0,3.282),(.105,3.29),(.194,3.327)],.012,dark,[.2,.7,.8,.7,.2])

# Keep the anime eye layers close to the sculpted facial surface in profile.
# Their shapes and ordering are preserved, with less depth between layers.
from math import sqrt
from mathutils import Vector
def face_surface(x,z):
    zn=(z-3.61)/.72;jaw=1-.18*max(0,-zn)
    return -.49*sqrt(max(.035,1-(x/(.70*jaw))**2-zn**2))
for ob in bpy.data.collections['02_FACE'].objects:
    inv=ob.matrix_world.inverted()
    if ob.type=='MESH':
        for vertex in ob.data.vertices:
            p=ob.matrix_world@vertex.co;y=face_surface(p.x,p.z)
            if p.y<y:
                p.y=y+(p.y-y)*.48;vertex.co=inv@p
    elif ob.type=='CURVE':
        for spline in ob.data.splines:
            for point in spline.bezier_points:
                p=ob.matrix_world@point.co;y=face_surface(p.x,p.z)
                if p.y<y:
                    p.y=y+(p.y-y)*.48;point.co=inv@p

# Short-sleeved jumpsuit with a shaped torso and separate wide trouser legs.
loft('Jumpsuit | short torso',[(2.17,0,0,.36,.24),(2.20,0,0,.43,.28),(2.40,0,0,.435,.28),(2.68,0,0,.45,.275),(2.83,0,0,.52,.26),(2.94,0,0,.37,.215),(3.01,0,0,.18,.155)],purple,'04_OUTFIT')
for sign,side in [(-1,'L'),(1,'R')]:
    tube_between('Short sleeve '+side,(sign*.45,0,2.80),(sign*.625,-.002,2.49),.195,.235,purple,'04_OUTFIT')
    # A soft piping line follows each sleeve hem.
    center=Vector((sign*.625,-.002,2.49));axis=Vector((sign*.175,-.002,-.31)).normalized()
    u=axis.cross(Vector((0,1,0))).normalized();w=axis.cross(u)
    pts=[center+.197*(u*cos(t)+w*sin(t)) for t in [2*pi*j/24 for j in range(24)]]
    curve('Sleeve hem '+side,pts,.012,seam,'04_OUTFIT',cyclic=True)
    x=sign*.264
    loft('Wide trouser leg '+side,[(.47,x,0,.224,.235),(.51,x,0,.26,.267),(.65,x,0,.272,.272),(1.2,x,0,.253,.245),(1.80,x,0,.212,.224),(2.15,x,0,.211,.245),(2.21,x,0,.208,.24)],purple,'04_OUTFIT')
    curve('Pressed trouser fold '+side,[(x+sign*.10,-.249,.61),(x+sign*.086,-.244,1.20),(x+sign*.06,-.225,1.85)],.008,seam,'04_OUTFIT',[.1,.6,.1])
loft('Jumpsuit | joined hip section',[(1.91,0,0,.28,.215),(1.97,0,0,.40,.26),(2.13,0,0,.433,.276),(2.25,0,0,.423,.27)],purple,'04_OUTFIT')
# Merge the hip section and trouser legs into a continuous garment surface.
# Evaluate subdivision before the voxel union, then retain a smoothing modifier.
bpy.ops.object.select_all(action='DESELECT')
parts=[bpy.data.objects.get('Jumpsuit | joined hip section'),bpy.data.objects.get('Wide trouser leg L'),bpy.data.objects.get('Wide trouser leg R')]
for ob in parts:
    ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.convert(target='MESH')
bpy.ops.object.join()
trousers=bpy.context.object
trousers.name='Jumpsuit | continuous trousers'
remesh=trousers.modifiers.new('Continuous garment union','REMESH')
remesh.mode='VOXEL';remesh.voxel_size=.014;remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=trousers.modifiers.new('Soft garment joins','SMOOTH');smooth.factor=1.2;smooth.iterations=5
bpy.ops.object.modifier_apply(modifier=smooth.name)
for face in trousers.data.polygons: face.use_smooth=True

# Belt seam and an asymmetrical button placket.
pts=[(.422*cos(2*pi*j/40),.28*sin(2*pi*j/40),2.23) for j in range(40)]
curve('Waist seam',pts,.025,seam,'04_OUTFIT',cyclic=True)
curve('Asymmetric front closure',[(.15,-.222,2.93),(.215,-.275,2.79),(.225,-.284,2.35)],.012,seam,'04_OUTFIT')
for z in [2.77,2.49]:
    uv('Gold button base '+str(z),(.225,-.299,z),(.073,.028,.073),gold,'04_OUTFIT')
    torus('Button raised rim '+str(z),(.225,-.326,z),.050,.008,sole,'04_OUTFIT')
    uv('Button inset '+str(z),(.225,-.33,z),(.026,.006,.026),purple,'04_OUTFIT',20,12)
for sign in [-1,1]:
    verts=[(sign*.03,-.167,3.017),(sign*.17,-.20,3.01),(sign*.29,-.243,2.91),(sign*.13,-.285,2.83)]
    ob=mesh('Folded collar '+str(sign),verts,[(0,1,2,3)],purple,'04_OUTFIT')
    m=ob.modifiers.new('Collar thickness','SOLIDIFY');m.thickness=.028
    m=ob.modifiers.new('Soft collar edge','BEVEL');m.width=.025;m.segments=3
    x=sign*.345
    curve('White waist drawstring '+str(sign),[(x,-.235,2.24),(x+sign*.025,-.276,2.09),(x+sign*.018,-.281,1.6),(x+sign*.016,-.299,1.09)],.018,ribbon,'04_OUTFIT')
    uv('Cord knot '+str(sign),(x+sign*.016,-.299,1.075),(.035,.027,.036),ribbon,'04_OUTFIT',20,12)
    tube_between('Cord aglet '+str(sign),(x+sign*.016,-.30,1.06),(x+sign*.028,-.30,1.0),.025,.023,ribbon,'04_OUTFIT')

# Chunky shoes: sculpted uppers, thick platforms and raised triangular teeth.
for sign,side in [(-1,'L'),(1,'R')]:
    x=sign*.285
    loft('Platform sole '+side,[(.04,x,-.105,.245,.345),(.06,x,-.105,.27,.36),(.18,x,-.105,.27,.36),(.23,x,-.10,.267,.35)],sole,'05_SHOES',2)
    loft('Golden shoe upper '+side,[(.20,x,-.105,.266,.35),(.25,x,-.10,.274,.353),(.40,x,-.09,.25,.32),(.50,x,.025,.19,.22),(.54,x,.035,.18,.205)],shoe,'05_SHOES',2)
    # Eye-shaped shoe appliques from the drawing.
    for q in [-1,1]:
        xx=x+q*.115
        ob=uv('Shoe eye outline '+side+str(q),(xx,-.394,.37),(.071,.020,.087),dark,'05_SHOES');ob.rotation_euler.y=q*.4
        ob=uv('Shoe eye ivory '+side+str(q),(xx,-.411,.375),(.048,.010,.065),ribbon,'05_SHOES');ob.rotation_euler.y=q*.4
    pts=[]
    for j in range(25):
        t=pi+pi*j/24;pts.append((x+.27*cos(t),-.105+.36*sin(t),.218))
    curve('Sole upper piping '+side,pts,.010,dark,'05_SHOES')
    for j in range(7):
        t1=pi+(j+.06)*pi/7;t2=pi+(j+.94)*pi/7;tm=(t1+t2)/2
        verts=[(x+.273*cos(t1),-.105+.365*sin(t1),.197),(x+.273*cos(t2),-.105+.365*sin(t2),.197),(x+.273*cos(tm),-.105+.365*sin(tm),.062)]
        tooth=mesh('Platform tooth '+side+str(j),verts,[(0,1,2)],ribbon,'05_SHOES')
        solid=tooth.modifiers.new('Raised tooth','SOLIDIFY');solid.thickness=.008
        curve('Tooth outline '+side+str(j),verts+[verts[0]],.007,dark,'05_SHOES')

# Pulled-back scalp cap, with a curved hairline and broad combed locks.
verts=[];faces=[];n=80;nr=20
for i in range(nr+1):
    for j in range(n):
        t=2*pi*j/n
        front=max(0,-sin(t));edge=1.88-.86*front
        ph=.015+(edge-.015)*i/nr
        verts.append((.718*sin(ph)*cos(t),.515*sin(ph)*sin(t)+.025,HEAD_Z+.752*cos(ph)))
for i in range(nr):
    for j in range(n):
        a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
mesh('Swept-back scalp cap',verts,faces,slick,'03_HAIR',1)
for k in range(-5,6):
    x=k*.108
    z=4.045+.08*(1-abs(k)/5)
    y=fy(x,z)-.025
    pts=[(x,y,z),(x*.98,-.37,4.24),(x*.77,-.13,4.36),(x*.49,.17,4.32),(x*.25,.40,4.23)]
    curve('Sculpted swept lock %02d'%(k+5),pts,.035,slick,'03_HAIR',[.05,.85,1,.8,.05])
    curve('Combed groove %02d'%(k+5),[(p[0]+.031,p[1]-.007,p[2]+.007) for p in pts],.006,hair_line,'03_HAIR',[.2,.8,1,.7,.1])
for sign,side in [(-1,'L'),(1,'R')]:
    for k in range(2):
        cx=sign*(.49+k*.067);cz=3.985-k*.16
        pts=[]
        for j in range(18):
            t=j/17*1.6*pi;r=.07*(1-j/22)
            x=cx+sign*r*cos(t);z=cz-r*sin(t);pts.append((x,fy(x,z)-.026,z))
        curve('Baby-hair curl '+side+str(k),pts,.018,slick,'03_HAIR',[1-j/20 for j in range(18)])

# Ponytail volume and individually editable curl clumps.
# Surface curls are meshes; no particle simulation or external add-ons are needed.
uv('Ponytail | main volume',(0,.65,3.06),(1.25,.57,1.55),hairs[2],'03_HAIR',48,32)
# Crown silhouette comes from the curl clumps.
N=285;golden=pi*(3-sqrt(5))
for i in range(N):
    zz=1-2*(i+.5)/N;r=sqrt(1-zz*zz);theta=i*golden
    normal=Vector((r*cos(theta),r*sin(theta),zz))
    loc=Vector((1.23*normal.x,.65+.55*normal.y,3.06+1.49*normal.z))
    s=random.uniform(.135,.19)
    ob=uv('Pony curl clump %03d'%i,loc,(s*1.16,s*.88,s*1.18),random.choice(hairs),'03_HAIR',20,14)
    ob.rotation_euler=(random.uniform(-.4,.4),random.uniform(-.4,.4),theta)
    # Coiled ridges sit on the outward-facing side of each clump.
    norm=Vector((normal.x/1.23,normal.y/.55,normal.z/1.49)).normalized()
    u=norm.cross(Vector((0,0,1)))
    if u.length<.1:u=norm.cross(Vector((0,1,0)))
    u.normalize();w=norm.cross(u).normalized()
    pts=[]
    for j in range(17):
        t=j/16*2*pi*1.25;rr=s*(.76-.48*j/16)
        pts.append(loc+norm*s*.74+u*(rr*cos(t))+w*(rr*sin(t)))
    curve('Curl ridge %03d'%i,pts,.018,hairs[(i+4)%7],'03_HAIR',[.4]+[1]*15+[.2])
# Gold tie at the crown, with a white, high-loop bow.
torus('Ponytail gold tie',(0,.39,4.28),.205,.051,gold,'06_RIBBON')
uv('Bow center',(0,.245,4.40),(.105,.078,.077),ribbon,'06_RIBBON')
for sign,side in [(-1,'L'),(1,'R')]:
    curve('White bow loop '+side,[(sign*.04,.25,4.40),(sign*.19,.27,4.66),(sign*.38,.28,4.81),(sign*.405,.26,4.53),(sign*.27,.25,4.35),(sign*.06,.24,4.39)],.035,ribbon,'06_RIBBON',cyclic=True)
    pts=[(sign*.12,.28,4.36),(sign*.43,.10,3.91),(sign*.61,-.005,3.37),(sign*.72,-.025,2.97),(sign*.91,-.04,2.60)]
    curve('Long white hair ribbon '+side,pts,.018,ribbon,'06_RIBBON')
    uv('Ribbon end knot '+side,(sign*.91,-.04,2.60),(.045,.035,.046),ribbon,'06_RIBBON',20,12)
    x=sign*.93
    verts=[(x,-.038,2.59),(x+sign*.055,-.042,2.56),(x+sign*.12,-.065,2.45),(x+sign*.035,-.08,2.44),(x-sign*.015,-.05,2.51)]
    ob=mesh('Ribbon folded tip '+side,verts,[(0,1,2,3,4)],ribbon,'06_RIBBON')
    m=ob.modifiers.new('Satin thickness','SOLIDIFY');m.thickness=.015
    m=ob.modifiers.new('Soft edges','BEVEL');m.width=.015;m.segments=3

# Packed front/side reference planes, hidden initially to show the model cleanly.
image=bpy.data.images.load(REF,check_existing=True);image.pack()
for name,rotation,location in [('Reference FRONT',(pi/2,0,0),(2.954,1.65,2.336)),('Reference SIDE',(pi/2,0,pi/2),(-1.65,.65,2.336))]:
    ob=bpy.data.objects.new(name,None);COLS['REFERENCES'].objects.link(ob)
    ob.empty_display_type='IMAGE';ob.data=image;ob.empty_display_size=9.2
    ob.rotation_euler=rotation;ob.location=location;ob.color[3]=.3
    ob.empty_image_depth='BACK';ob.show_empty_image_orthographic=True;ob.show_empty_image_perspective=False
    ob.hide_render=True
COLS['REFERENCES'].hide_viewport=True

# Studio presentation.
floor=mat('Studio | muted plum',(.12,.095,.135),.78)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,.006));finish(bpy.context.object,'Studio floor',floor,'STUDIO')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40
scene.cycles.use_denoising=True
scene.world.color=(.25,.25,.25)
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.20,.18,.23,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.45

def area(name,loc,energy,color,size,target=(0,0,2.5)):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);COLS['STUDIO'].objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
area('Key softbox',(-3,-5,7),650,(1,.82,.65),4)
area('Fill softbox',(4,-2,4.8),450,(.74,.83,1),3)
area('Hair rim',(0,3,6.5),850,(1,.72,.46),3)
camdata=bpy.data.cameras.new('Portrait camera');cam=bpy.data.objects.new('Portrait camera',camdata);COLS['STUDIO'].objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=5.65;camdata.lens=60
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'

def view(loc,target=(0,.15,2.43)):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
view((6,-12,6))
# Store a clean, useful opening view in Blender.
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_distance=7.5
            a.spaces.active.region_3d.view_location=(0,0,2.4)
            a.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
            a.spaces.active.clip_end=300
bpy.ops.object.select_all(action='DESELECT')
head=bpy.data.objects.get('Head | shaped cheeks and chin');head.select_set(True);bpy.context.view_layer.objects.active=head
# Helpful in-file notes, including the limits of this asset.
notes=bpy.data.texts.new('READ ME - Character')
notes.write('Character modeled from the supplied front/side/back reference.\nCollections separate body, face, mesh curls, clothing, shoes, and ribbons.\nReference images are packed; enable REFERENCES in the Outliner to see them.\nThis is an editable static character model, not a rigged animation-ready asset.\nCurves remain editable; no particle hair, plugins, or external textures required.\nBody parts under clothing are separate blockout meshes. Retopology and rigging are future steps.\n')
blend=os.path.join(OUT,'Character_Reference.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
for name,loc in [('three_quarter',(6,-12,6)),('front',(0,-14,5.0)),('side',(14,0,5.0)),('back',(0,14,5.0))]:
    view(loc)
    scene.render.filepath=os.path.join(OUT,name+'.png')
    bpy.ops.render.render(write_still=True)
view((6,-12,6));scene.render.filepath=os.path.join(OUT,'three_quarter.png')
bpy.ops.wm.save_as_mainfile(filepath=blend)
print('CHARACTER_COMPLETE', blend)




