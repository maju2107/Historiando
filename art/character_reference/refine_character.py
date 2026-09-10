"""Reference-fidelity revision. Keeps the first model untouched; generates refined/ outputs."""
import bpy, os, math, random
from mathutils import Vector, noise as mnoise
from math import sin, cos, pi, sqrt
ROOT=os.path.join(os.getcwd(),'art','character_reference')
# Reuse only the named primitive/mesh helpers, not the earlier model geometry.
with open(os.path.join(ROOT,'build_character.py'),encoding='utf-8-sig') as f:
    base=f.read().split('# Head: rounded forehead')[0]
exec(compile(base,'shared_modeling_helpers','exec'))
OUT=os.path.join(ROOT,'refined');os.makedirs(OUT,exist_ok=True)
random.seed(81)

def tune(m,color,rough,spec=.25):
    m.diffuse_color=(*color,1);p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    p.inputs['Specular IOR Level'].default_value=spec

tune(skin,(.72,.325,.175),.69,.22)
tune(inner,(.50,.18,.105),.75,.15)
tune(dark,(.056,.021,.013),.78,.1)
tune(white,(.78,.65,.42),.59,.15)
tune(slick,(.24,.080,.034),.49,.28)
tune(ribbon,(.94,.92,.84),.63,.2)
tune(shoe,(.66,.36,.063),.60,.25)
tune(sole,(.77,.61,.34),.78,.1)
tune(gold,(.76,.46,.09),.4,.3)
gold.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.35
tune(seam,(.053,.01,.13),.82,.1)
tune(iris_outer,(.105,.036,.008),.53,.12)
tune(iris,(.46,.14,.015),.45,.18)
tune(iris_light,(.95,.44,.044),.5,.15)
# Fine, horizontal, irregular fabric bands like the reference jumpsuit.
ns=purple.node_tree.nodes;ls=purple.node_tree.links;p=ns.get('Principled BSDF')
p.inputs['Roughness'].default_value=.85;p.inputs['Specular IOR Level'].default_value=.15
tex=ns.new('ShaderNodeTexCoord');wave=ns.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Z'
wave.inputs['Scale'].default_value=21;wave.inputs['Distortion'].default_value=7;wave.inputs['Detail'].default_value=4;wave.inputs['Detail Scale'].default_value=2.4
ls.new(tex.outputs['Generated'],wave.inputs['Vector'])
ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.13;ramp.color_ramp.elements[0].color=(.031,.005,.091,1)
ramp.color_ramp.elements[1].position=.88;ramp.color_ramp.elements[1].color=(.049,.010,.138,1)
ls.new(wave.outputs['Color'],ramp.inputs['Fac']);ls.new(ramp.outputs['Color'],p.inputs['Base Color'])
# One continuous ponytail surface, with subtle curl-scale relief and a vertical color gradient.
afro=mat('Afro | dense chestnut with copper crown',(.14,.043,.014),.88)
ns=afro.node_tree.nodes;ls=afro.node_tree.links;p=ns.get('Principled BSDF');p.inputs['Specular IOR Level'].default_value=.16
geo=ns.new('ShaderNodeNewGeometry');sep=ns.new('ShaderNodeSeparateXYZ');ls.new(geo.outputs['Position'],sep.inputs[0])
mp=ns.new('ShaderNodeMapRange');mp.inputs['From Min'].default_value=1.2;mp.inputs['From Max'].default_value=4.85
ls.new(sep.outputs['Z'],mp.inputs['Value'])
gr=ns.new('ShaderNodeValToRGB');gr.color_ramp.elements[0].position=.15;gr.color_ramp.elements[0].color=(.079,.018,.005,1)
gr.color_ramp.elements[1].position=1.0;gr.color_ramp.elements[1].color=(.40,.155,.069,1)
mid=gr.color_ramp.elements.new(.72);mid.color=(.16,.047,.014,1)
ls.new(mp.outputs['Result'],gr.inputs['Fac']);ls.new(gr.outputs['Color'],p.inputs['Base Color'])
nt=ns.new('ShaderNodeTexNoise');nt.inputs['Scale'].default_value=62;nt.inputs['Detail'].default_value=3;nt.inputs['Roughness'].default_value=.7
ls.new(geo.outputs['Position'],nt.inputs['Vector'])
bu=ns.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.10;bu.inputs['Distance'].default_value=.009
ls.new(nt.outputs['Fac'],bu.inputs['Height']);ls.new(bu.outputs['Normal'],p.inputs['Normal'])

# Anatomical envelope measured against the sheet, with soles at Z=0.
HZ=3.785;HX=.632;HY=.475;HH=.713

def jaw(z): return 1-.11*max(0,-(z-HZ)/HH)
def fy(x,z):
    zz=(z-HZ)/HH
    return -.02-HY*sqrt(max(.025,1-(x/(HX*jaw(z)))**2-zz**2))*(1-.16*max(0,-zz))
verts=[];faces=[];n=72;nr=48
for i in range(nr+1):
    ph=pi*i/nr;zz=cos(ph);z=HZ+HH*zz
    for j in range(n):
        t=2*pi*j/n;y=HY*sin(ph)*sin(t)*(1-.16*max(0,-zz))-.02
        verts.append((HX*sin(ph)*cos(t)*jaw(z),y,z))
for i in range(nr):
    for j in range(n):
        a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
mesh('Head | reference proportions',verts,faces,skin,'01_BODY',1)
uv('Neck',(0,.03,3.02),(.125,.13,.18),skin)
uv('Torso underneath outfit',(0,.025,2.56),(.34,.20,.46),skin)
for s,side in [(-1,'L'),(1,'R')]:
    uv('Ear '+side,(s*.613,.025,3.46),(.095,.075,.141),skin)
    uv('Ear concha '+side,(s*.641,-.031,3.47),(.041,.025,.082),inner,'02_FACE')
    tube_between('Arm '+side,(s*.485,.015,2.65),(s*.638,-.005,2.015),.118,.128,skin,'01_BODY')
    uv('Rounded hand '+side,(s*.655,-.022,1.954),(.167,.137,.172),skin)
    uv('Concealed leg '+side,(s*.275,.02,1.20),(.19,.18,.84),skin)

# Graphic anime eyes: warm sclera, partially hooded amber iris, curved surface.
def fc(name,points,r,material,radii=None):
    return curve(name,[(x,fy(x,z)-.013,z) for x,z in points],r,material,'02_FACE',radii)

def patch(name,cx,cz,rx,rz,material,depth=.022,limits=None):
    v=[(cx,fy(cx,cz)-depth,cz)];n=64
    for j in range(n):
        t=2*pi*j/n;x=cx+rx*cos(t);z=cz+rz*sin(t)
        if limits:
            lo,hi=limits(x);z=max(lo,min(hi,z))
        v.append((x,fy(x,z)-depth,z))
    return mesh(name,v,[(0,j+1,(j+1)%n+1) for j in range(n)],material,'02_FACE')
for s,side in [(-1,'L'),(1,'R')]:
    cx=s*.285;cz=3.590;hw=.193
    def eye_bounds(x,cx=cx,s=s):
        q=max(-1,min(1,(x-cx)/hw));h=sqrt(max(0,1-q*q))
        slope=s*(x-cx)*.08
        return cz-.096*h+slope,cz+.116*h**.55+slope
    points=[]
    for j in range(65):
        t=2*pi*j/64;x=cx+hw*cos(t);lo,hi=eye_bounds(x);points.append((x,hi if sin(t)>=0 else lo))
    v=[(cx,fy(cx,cz)-.018,cz)]+[(x,fy(x,z)-.018,z) for x,z in points[:-1]]
    mesh('Hooded almond eye '+side,v,[(0,j+1,(j+1)%64+1) for j in range(64)],white,'02_FACE')
    patch('Iris dark edge '+side,cx,cz,.108,.119,iris_outer,.024,eye_bounds)
    patch('Rich amber iris '+side,cx,cz-.002,.097,.108,iris,.028,eye_bounds)
    patch('Iris gold lower light '+side,cx,cz-.032,.080,.068,iris_light,.031,eye_bounds)
    patch('Deep pupil '+side,cx,cz+.007,.039,.079,pupil,.037,eye_bounds)
    for k in range(13):
        t=pi*1.04+pi*.92*k/12
        pts=[(cx+r*cos(t),cz+r*1.08*sin(t)) for r in [.06,.086]]
        fc('Amber iris filament '+side+str(k),pts,.0025,iris_outer)
    patch('Eye highlight '+side,cx-.025,cz+.054,.022,.033,highlight,.043,eye_bounds)
    patch('Small eye highlight '+side,cx+.040,cz-.047,.009,.014,highlight,.044,eye_bounds)
    top=[];bottom=[]
    for k in range(17):
        x=cx-hw+2*hw*k/16;lo,hi=eye_bounds(x);top.append((x,hi));bottom.append((x,lo))
    fc('Upper lid '+side,top,.017,dark,[.2]+[.9]*15+[.2])
    fc('Lower lid '+side,bottom,.006,dark,[.1]+[.7]*15+[.1])
    outer=cx+s*hw
    for k in range(3):
        x=outer-s*.021*k;lo,z=eye_bounds(x)
        fc('Short lash '+side+str(k),[(x,z),(x+s*.038,z+.025),(x+s*.060,z+.055)],.013,dark,[.9,.55,.03])
    fc('Confident angled brow '+side,[(s*.12,3.782),(s*.19,3.814),(s*.31,3.846),(s*.405,3.851)],.027,slick,[.6,1,.70,.03])
    fc('Smirk '+side,[(s*.09,3.244),(s*.19,3.255),(s*.265,3.291),(s*.282,3.272)],.008,dark,[.05,.7,.9,.1])
# Tiny nose wedge, kept nearly flush to the face.
uv('Minimal nose',(0,fy(0,3.405)-.006,3.405),(.023,.027,.035),skin,'02_FACE',24,16)

# Fitted short torso, diagonal V-neck, flared short sleeves.
loft('Jumpsuit torso',[(2.25,0,.02,.335,.208),(2.28,0,.02,.395,.242),(2.46,0,.02,.385,.233),(2.74,0,.02,.416,.23),(2.87,0,.02,.437,.215),(2.94,0,.02,.255,.17),(3.005,0,.02,.12,.10)],purple,'04_OUTFIT',2)
for s,side in [(-1,'L'),(1,'R')]:
    tube_between('Short flared sleeve '+side,(s*.404,.02,2.812),(s*.560,.008,2.385),.158,.20,purple,'04_OUTFIT')
    center=Vector((s*.56,.008,2.385));axis=Vector((s*.156,-.012,-.427)).normalized();u=axis.cross(Vector((0,1,0))).normalized();w=axis.cross(u)
    curve('Sleeve stitched edge '+side,[center+.195*(u*cos(t)+w*sin(t)) for t in [2*pi*k/32 for k in range(32)]],.007,seam,'04_OUTFIT',cyclic=True)
    loft('Flared trouser leg '+side,[(.51,s*.335,.02,.279,.254),(.54,s*.335,.02,.305,.284),(.65,s*.334,.02,.31,.277),(1.13,s*.299,.02,.277,.25),(1.70,s*.249,.02,.234,.218),(2.20,s*.214,.02,.204,.23),(2.29,s*.208,.02,.201,.229)],purple,'04_OUTFIT',2)
loft('Hip bridge',[(2.01,0,.02,.26,.20),(2.08,0,.02,.381,.22),(2.24,0,.02,.39,.232),(2.285,0,.02,.383,.23)],purple,'04_OUTFIT')
bpy.ops.object.select_all(action='DESELECT')
parts=[bpy.data.objects['Hip bridge'],bpy.data.objects['Flared trouser leg L'],bpy.data.objects['Flared trouser leg R']]
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
ob=bpy.context.object;ob.name='Jumpsuit | continuous flared trousers'
m=ob.modifiers.new('Seamless hips','REMESH');m.mode='VOXEL';m.voxel_size=.014;m.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=m.name)
m=ob.modifiers.new('Fabric smoothing','SMOOTH');m.factor=1;m.iterations=4;bpy.ops.object.modifier_apply(modifier=m.name)
curve('Waist seam',[(.388*cos(t),.02+.234*sin(t),2.277) for t in [2*pi*k/40 for k in range(40)]],.012,seam,'04_OUTFIT',cyclic=True)
# Collar follows the short crossover V seen on the sheet.
for s in [-1,1]:
    v=[(s*.02,-.10,3.022),(s*.115,-.106,3.025),(s*.29,-.18,2.928),(s*.095,-.218,2.832)]
    ob=mesh('Crossover collar '+str(s),v,[(0,1,2,3)],purple,'04_OUTFIT')
    m=ob.modifiers.new('Collar thickness','SOLIDIFY');m.thickness=.018
    m=ob.modifiers.new('Rounded cloth edge','BEVEL');m.width=.008;m.segments=2
curve('Diagonal placket',[(.12,-.203,2.91),(.194,-.225,2.79),(.202,-.226,2.36)],.007,seam,'04_OUTFIT')
for i,z in enumerate([2.776,2.517]):
    uv('Filled gold button '+str(i),(.201,-.231,z),(.058,.019,.058),gold,'04_OUTFIT',32,16)
    torus('Button engraved rim '+str(i),(.201,-.250,z),.041,.0035,iris_outer,'04_OUTFIT')
    for dx in [-.010,.010]:
        curve('Button hole '+str(i)+str(dx),[(.201+dx,-.251,z-.012),(.201+dx,-.251,z+.012)],.0035,iris_outer,'04_OUTFIT')
for s in [-1,1]:
    x=s*.282
    curve('Long white waist cord '+str(s),[(x,-.206,2.275),(x+s*.003,-.245,2.14),(x+s*.009,-.259,1.59),(x+s*.012,-.274,.993)],.014,ribbon,'04_OUTFIT')
    torus('Drawstring knot '+str(s),(x+s*.012,-.274,.999),.022,.009,ribbon,'04_OUTFIT')
    tube_between('Drawstring tip '+str(s),(x+s*.012,-.274,.98),(x+s*.010,-.274,.942),.019,.026,ribbon,'04_OUTFIT')

# Broad golden platform shoes; printed eye motifs and flush teeth.
for s,side in [(-1,'L'),(1,'R')]:
    x=s*.328
    loft('Cream platform '+side,[(.025,x,-.13,.265,.409),(.04,x,-.13,.285,.43),(.17,x,-.13,.289,.432),(.20,x,-.13,.287,.43)],sole,'05_SHOES',2)
    loft('Golden shoe '+side,[(.174,x,-.13,.287,.426),(.22,x,-.13,.295,.437),(.36,x,-.115,.29,.422),(.47,x,.00,.258,.289),(.535,x,.04,.23,.232)],shoe,'05_SHOES',2)
    # Flush, continuous zigzag on the platform front and sides.
    pts=[]
    for j in range(17):
        t=pi+pi*j/16;pts.append((x+.289*cos(t),-.13+.438*sin(t),.052 if j%2 else .169))
    curve('Printed tooth zigzag '+side,pts,.0065,dark,'05_SHOES')
    # Straight segments instead of smoothed spikes.
    for bp in bpy.data.objects['Printed tooth zigzag '+side].data.splines[0].bezier_points:
        bp.handle_left_type='VECTOR';bp.handle_right_type='VECTOR'
    for q in [-1,1]:
        xx=x+q*.123;y=-.489
        ob=uv('Dark shoe eye '+side+str(q),(xx,y,.361),(.074,.009,.086),dark,'05_SHOES',28,16);ob.rotation_euler.y=q*.40
        ob=uv('Cream crescent '+side+str(q),(xx-q*.008,y-.010,.357),(.055,.006,.066),ribbon,'05_SHOES',28,16);ob.rotation_euler.y=q*.40
        ob=uv('Shoe eye pupil '+side+str(q),(xx-q*.022,y-.017,.391),(.041,.006,.053),dark,'05_SHOES',24,16);ob.rotation_euler.y=q*.40

# Rounded, continuous scalp with seven gently fluted swept-back rolls.
verts=[];faces=[];n=160;nr=72
for i in range(nr+1):
    for j in range(n):
        t=2*pi*j/n;front=max(0,-sin(t))
        lobe=(.5+.5*cos(7*pi*cos(t)))**2
        edge=1.97-.83*front+.023*front*lobe
        ph=.003+(edge-.003)*i/nr
        lift=.013+.046*lobe*front*(sin(ph)**.8)*math.exp(-((ph-.83)/.67)**2)
        # Rolls grow out of the scalp; there are no floating flat-ended strips.
        verts.append(((HX+lift)*sin(ph)*cos(t),-.006+(HY+lift)*sin(ph)*sin(t),HZ+(HH+lift)*cos(ph)))
for i in range(nr):
    for j in range(n):
        a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
ob=mesh('Slicked-back rounded rolls',verts,faces,slick,'03_HAIR',1)
m=ob.modifiers.new('Soft hairline thickness','SOLIDIFY');m.thickness=.023
m=ob.modifiers.new('Rounded hairline','BEVEL');m.width=.011;m.segments=3

# Baby hairs: tapered S curls along the temples and a small forehead swoop.
for s,side in [(-1,'L'),(1,'R')]:
    for k in range(3):
        cx=s*(.414+.060*k);cz=4.045-.142*k
        pts=[]
        for j in range(24):
            t=j/23*1.78*pi;r=.055*(1-.70*j/23)
            x=cx+s*r*cos(t);z=cz-r*sin(t);pts.append((x,fy(x,z)-.013,z))
        curve('Tapered baby curl '+side+str(k),pts,.014,slick,'03_HAIR',[1-.94*j/23 for j in range(24)])

# Dense afro ponytail: reference-shaped envelope, scalloped on a fine scale.
sections=[(1.20,.018,.025,1.06),(1.32,.40,.33,1.07),(1.58,.76,.53,1.10),(2.05,1.10,.69,1.12),(2.66,1.33,.76,1.14),(3.25,1.395,.765,1.15),(3.86,1.26,.70,1.16),(4.31,1.02,.59,1.16),(4.63,.61,.40,1.14),(4.82,.015,.022,1.12)]
def profile(z):
    if z>4.31:
        dome=sqrt(max(.0001,1-((z-4.12)/.70)**2))
        return (1.06*dome,.612*dome,1.14)
    if z<1.58:
        dome=sqrt(max(.0001,1-((z-1.90)/.70)**2))
        return (.85*dome,.59*dome,1.085)
    for i in range(len(sections)-1):
        if sections[i][0]<=z<=sections[i+1][0]:
            a=sections[i];b=sections[i+1];t=(z-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple(a[k]*(1-t)+b[k]*t for k in [1,2,3])
    return sections[-1][1:]
vs=[];fs=[];nz=160;nt=240
for i in range(nz+1):
    z=1.20+3.62*i/nz;rx,ry,cy=profile(z)
    for j in range(nt):
        t=2*pi*j/nt;base=Vector((rx*cos(t),cy+ry*sin(t),z))
        nv=mnoise.noise_vector(base*24)
        perturb=.018*nv.x+.008*mnoise.noise_vector(base*47).y
        edgefade=min(1,rx/.18)
        vs.append((base.x+perturb*cos(t)*edgefade,base.y+perturb*sin(t)*edgefade,z+.016*nv.z*edgefade))
for i in range(nz):
    for j in range(nt):
        a=i*nt+j;b=i*nt+(j+1)%nt;fs.append((a,b,b+nt,a+nt))
fs.extend([tuple(reversed(range(nt))),tuple(nz*nt+j for j in range(nt))])
mesh('Afro | unified fine curl volume',vs,fs,afro,'03_HAIR',1)
# Tiny silhouette curls sparingly break the dense outline.
for s in [-1,1]:
    for i in range(20):
        z=1.5+i*.151;rx,ry,cy=profile(z);pts=[]
        for j in range(14):
            t=j/13*1.8*pi;r=.028*(1-j/20)
            pts.append((s*(rx+.008+r*cos(t)),cy-.065,z+r*sin(t)))
        curve('Afro edge curl %s %02d'%(s,i),pts,.007,afro,'03_HAIR',[1-j/16 for j in range(14)])

# Angular white ribbon loops at the tie, lower than the afro's crown.
# Flat ribbon strips with softly rounded edges, rather than tubular cat ears.
def strip(name,pts,width,material,group='06_RIBBON',cyclic=False):
    vs=[];fs=[]
    for i,p in enumerate(pts):
        before=Vector(pts[max(0,i-1)]);after=Vector(pts[min(len(pts)-1,i+1)])
        tangent=(after-before).normalized();perp=Vector((-tangent.z,0,tangent.x)).normalized()*width/2
        vs.extend([Vector(p)-perp,Vector(p)+perp])
    for i in range(len(pts)-1):fs.append((2*i,2*i+1,2*i+3,2*i+2))
    ob=mesh(name,vs,fs,material,group)
    m=ob.modifiers.new('Ribbon thickness','SOLIDIFY');m.thickness=.012
    m=ob.modifiers.new('Ribbon soft edge','BEVEL');m.width=.008;m.segments=3
    return ob
# Gold band wraps the root and presents a small gold center above the scalp.
torus('Gold ponytail band',(0,.48,4.36),.145,.041,gold,'06_RIBBON')
uv('Visible gold tie',(0,.045,4.50),(.105,.067,.088),gold,'06_RIBBON')
for s,side in [(-1,'L'),(1,'R')]:
    strip('Angular white bow '+side,[(s*.038,.085,4.46),(s*.20,.10,4.62),(s*.365,.12,4.739),(s*.390,.14,4.697),(s*.382,.15,4.385),(s*.12,.085,4.44)],.041,ribbon)
    strip('White trailing hair ribbon '+side,[(s*.09,.37,4.38),(s*.28,.27,3.87),(s*.42,.14,3.30),(s*.55,.04,2.70),(s*.695,-.001,2.36)],.027,ribbon)
    uv('Hair ribbon knot '+side,(s*.695,-.012,2.36),(.034,.024,.035),ribbon,'06_RIBBON',20,12)
    strip('Folded ribbon tip '+side,[(s*.695,-.012,2.34),(s*.738,-.025,2.272),(s*.79,-.035,2.259)],.086,ribbon)

# Packed orthographic references calibrated to 0.0075 Blender units per image pixel.
im=bpy.data.images.load(REF,check_existing=True);im.pack()
for name,rot,loc in [('FRONT reference',(pi/2,0,0),(3.084,2.6,2.438)),('SIDE reference',(pi/2,0,pi/2),(-2.0,.622,2.438))]:
    ob=bpy.data.objects.new(name,None);COLS['REFERENCES'].objects.link(ob);ob.empty_display_type='IMAGE';ob.data=im;ob.empty_display_size=9.6
    ob.rotation_euler=rot;ob.location=loc;ob.color[3]=.32;ob.empty_image_depth='BACK';ob.show_empty_image_perspective=False;ob.hide_render=True
COLS['REFERENCES'].hide_viewport=True

# Neutral studio; exact orthographic front/side views are also provided for comparison.
floor=mat('Studio | warm gray',(.24,.225,.21),.85)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));finish(bpy.context.object,'Studio floor',floor,'STUDIO')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=28;scene.cycles.use_denoising=True;scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2
scene.world.use_nodes=True;world=scene.world.node_tree.nodes.get('Background');world.inputs[0].default_value=(.28,.26,.25,1);world.inputs[1].default_value=.55
# A cylinder wall provides a neutral background in every orthographic direction.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=20,depth=30,location=(0,0,14.98))
wall=finish(bpy.context.object,'Studio surround',floor,'STUDIO')
wall.visible_diffuse=False;wall.visible_glossy=False;wall.visible_shadow=False
# remove cylinder caps, so they do not obstruct studio lights
me=wall.data
import bmesh
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.delete(bm,geom=[f for f in bm.faces if len(f.verts)>4],context='FACES');bm.to_mesh(me);bm.free()
def area(name,loc,energy,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);COLS['STUDIO'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,.4,2.6))-o.location).to_track_quat('-Z','Y').to_euler()
area('Soft key',(-3.8,-5.5,7),500,(1,.90,.79),5)
area('Soft fill',(4,-3,5),320,(.85,.91,1),4)
area('Copper hair rim',(0,4,7),430,(1,.84,.68),4)
d=bpy.data.cameras.new('Portrait camera');cam=bpy.data.objects.new('Portrait camera',d);COLS['STUDIO'].objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=5.40
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
def view(loc,target):cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
view((6,-12,5.3),(0,.45,2.45))
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_distance=7.4;a.spaces.active.region_3d.view_location=(0,.3,2.45);a.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
notes=bpy.data.texts.new('READ ME | Reference fidelity revision')
notes.write('Refined against the supplied front/side/back sheet.\nContinuous finely scalloped afro, broad swept locks, narrow chibi head, hooded amber eyes, flared indigo jumpsuit, gold tie and flat angular ribbons.\nReference image is packed; enable REFERENCES in the Outliner.\nStatic editable model: not rigged, UV-unwrapped, or optimized for gameplay. Concealed body is simplified.\nThe original model is preserved one directory above.\n')
bpy.ops.object.select_all(action='DESELECT');head=bpy.data.objects['Head | reference proportions'];head.select_set(True);bpy.context.view_layer.objects.active=head
bpy.context.preferences.filepaths.save_version=0
blend=os.path.join(OUT,'Character_Refined.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
views=[('three_quarter',(6,-12,5.3),(0,.45,2.45)),('front',(0,-14,2.45),(0,0,2.45)),('side',(14,0,2.45),(0,0,2.45)),('back',(0,14,2.45),(0,0,2.45))]
for name,loc,target in views:
    view(loc,target)
    clean=name!='three_quarter'
    bpy.data.objects['Studio floor'].hide_render=clean;wall.hide_render=clean;scene.render.film_transparent=clean
    scene.render.image_settings.color_mode='RGBA'
    scene.render.filepath=os.path.join(OUT,name+'.png');bpy.ops.render.render(write_still=True)
bpy.data.objects['Studio floor'].hide_render=False;wall.hide_render=False;scene.render.film_transparent=False
view((6,-12,5.3),(0,.45,2.45));scene.render.filepath=os.path.join(OUT,'three_quarter.png');bpy.ops.wm.save_as_mainfile(filepath=blend)
print('REFINED_MODEL_COMPLETE',blend)

