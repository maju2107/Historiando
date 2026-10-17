"""Build Kai from the existing editable character base. Run with Blender --background --python."""
import bpy, bmesh, math, json, traceback
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
from math import sin, cos, pi
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando')
OUT=ROOT/'art/kai'; WORK=Path('C:/Users/obran/Historiando_Backups/kai_work_2026-10-15')
def log(s):
 print(s,flush=True); (WORK/'progress.txt').write_text(s)
def rgb(h):
 v=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)+(1,)
def mat(name,color,rough=.5,metal=0):
 m=bpy.data.materials.new('Kai / '+name);m.diffuse_color=rgb(color);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=rgb(color);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
def mesh(name,v,f,m,sub=0,bone=None):
 d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update();o=bpy.data.objects.new('KAI_'+name,d);COL.objects.link(o)
 if m:d.materials.append(m)
 bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
 for p in d.polygons:p.use_smooth=True
 if sub:mo=o.modifiers.new('Editable smooth quads','SUBSURF');mo.levels=sub;mo.render_levels=sub
 if bone:bind(o,bone)
 return o
def bind(o,bone):
 g=o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
 mo=o.modifiers.new('Kai deformation','ARMATURE');mo.object=rig
def ball(name,loc,scale,m,bone=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc)
 o=bpy.context.object;o.name='KAI_'+name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 COL.objects.link(o);o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 if bone:bind(o,bone)
 return o
def box(name,loc,scale,m,bone=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name='KAI_'+name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 COL.objects.link(o);o.data.materials.append(m);mo=o.modifiers.new('Soft stitched corners','BEVEL');mo.width=.006;mo.segments=3
 for p in o.data.polygons:p.use_smooth=True
 mo=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 if bone:bind(o,bone)
 return o
def bez(p,n=25):
 a,b,c,d=map(Vector,p)
 return [(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d for t in [i/(n-1) for i in range(n)]]
def tube(name,pts,width,m,bone=None,depth=1,taper=False,normal=(0,-1,0),sub=1):
 pts=list(map(Vector,pts));v=[];f=[];N=10;prev=None
 for i,p in enumerate(pts):
  t=i/(len(pts)-1);tang=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();normalv=Vector(normal)
  if abs(tang.dot(normalv))>.95:normalv=Vector((1,0,0))
  side=tang.cross(normalv).normalized()
  if taper and prev is not None:
   projected=prev-tang*prev.dot(tang)
   if projected.length>.001:side=projected.normalized()
  prev=side.copy();deep=side.cross(tang).normalized()
  r=width*((.45+.65*sin(pi*t))*(1-t)**.45+.006 if taper else 1)
  for j in range(N):v.append(p+side*(r*cos(j*2*pi/N))+deep*(r*depth*sin(j*2*pi/N)))
 for i in range(len(pts)-1):
  for j in range(N):a=i*N+j;b=i*N+(j+1)%N;f.append((a,b,b+N,a+N))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))])
 return mesh(name,v,f,m,sub,bone)
def lathe(name,rings,cx,cy,m,power=2,N=48,sub=1,bone=None,cap=False):
 v=[];f=[]
 for z,rx,ry,dy in rings:
  for i in range(N):
   a=2*pi*i/N;v.append((cx+rx*math.copysign(abs(cos(a))**(2/power),cos(a)),cy+dy+ry*math.copysign(abs(sin(a))**(2/power),sin(a)),z))
 for j in range(len(rings)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;f.append((a,b,b+N,a+N))
 if cap:f.extend([tuple(range(N-1,-1,-1)),tuple((len(rings)-1)*N+i for i in range(N))])
 return mesh(name,v,f,m,sub,bone)
def hair_lock(name,controls,width,material,normal=(0,-1,0)):
 """Broad swept profile with a shallow back, subtle ridges, and a tapered tip.
 Inspired by user-linked path/profile and low-density subdivided-lock tutorials.
 """
 pts=bez(controls,28);v=[];f=[];prev=None;N=20
 for i,p in enumerate(pts):
  t=i/(len(pts)-1);tang=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
  out=Vector(normal);side=tang.cross(out).normalized()
  if tang.cross(out).length<.05 and prev is not None:
   projected=prev-tang*prev.dot(tang)
   if projected.length>.001:side=projected.normalized()
  prev=side.copy();out=side.cross(tang).normalized()
  tail=max(0,min(1,(t-.58)/.42));taper=1-tail*tail*(3-2*tail)
  root=min(1,t/.22);root=.28+.72*root*root*(3-2*root)
  w=width*root*(.94+.06*sin(pi*t))*max(.002,taper)
  for j in range(N):
   a=2*pi*j/N;u=cos(a);h=sin(a)
   if h>=0:
    # Broad central ridge with two gentle longitudinal valleys.
    h=h*(.43-.085*math.exp(-((abs(u)-.47)/.13)**2))
   else:h*=.28
   v.append(p+side*(u*w)+out*(h*w))
 for i in range(len(pts)-1):
  for j in range(N):a=i*N+j;b=i*N+(j+1)%N;f.append((a,b,b+N,a+N))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))])
 o=mesh(name,v,f,material,2,'Head');o.modifiers[0].levels=1
 # A regular UV strip makes each lock straightforward to paint later.
 uv=o.data.uv_layers.new(name='Lock UV')
 for p in o.data.polygons:
  for li in p.loop_indices:
   idx=o.data.loops[li].vertex_index;uv.data[li].uv=((idx%N)/N,(idx//N)/(len(pts)-1))
 return o
def grooved_sole(side,cx,cream,bone):
 N=352;R=71;v=[];f=[];depths=[]
 for j in range(R):
  z=-.005+.035*j/(R-1);rounding=0
  if z<0:rounding=.003*(1-math.sqrt(max(0,1-(z/.005)**2)))
  if z>.025:rounding=.003*(1-math.sqrt(max(0,1-((z-.025)/.005)**2)))
  for i in range(N):
   a=2*pi*i/N;cut=0
   if pi<=a<=2*pi and -.001<z<.026:
    phase=(a-pi)/pi*22;fraction=phase%2;target=.0008+.0232*abs(fraction-1)
    cut=.0015*math.exp(-((z-target)/.00165)**2)
   rx=.081-rounding-cut;ry=.115-rounding-cut
   v.append((cx+rx*math.copysign(abs(cos(a))**(2/3.3),cos(a)),-.035+ry*math.copysign(abs(sin(a))**(2/3.3),sin(a)),z));depths.append(cut)
 for j in range(R-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;f.append((a,b,b+N,a+N))
 f.extend([tuple(range(N-1,-1,-1)),tuple((R-1)*N+i for i in range(N))])
 o=mesh('Cream sole with engraved teeth '+side,v,f,cream,0,bone)
 shade=bpy.data.materials.get('Kai / Cream groove shadow') or mat('Cream groove shadow','D2BC93',.7);o.data.materials.append(shade)
 for p in o.data.polygons:
  if len(p.vertices)==4 and sum(depths[i] for i in p.vertices)/4>.0010:p.material_index=1
 return o
def pattern(m,colors,scale,detail=2):
 nt=m.node_tree;n=nt.nodes;l=nt.links;p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=detail;noise.inputs['Roughness'].default_value=.75
 l.new(tc.outputs['Generated'],noise.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.interpolation='CONSTANT'
 for e in list(r.color_ramp.elements)[1:]:r.color_ramp.elements.remove(e)
 for i,(pos,c) in enumerate(colors):e=r.color_ramp.elements[0] if i==0 else r.color_ramp.elements.new(pos);e.position=pos;e.color=rgb(c)
 l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs['Color'],p.inputs['Base Color'])
def main():
 global COL,rig
 log('Loading donor base')
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/yara/yara.blend'))
 rig=bpy.data.objects['YARA_Rig'];rig.name='KAI_Rig';rig.animation_data_clear()
 for b in rig.pose.bones:b.matrix_basis.identity()
 rig.data.pose_position='REST'
 keep={'CHR_Body','CHR_Ear.L','CHR_Ear.R','CHR_Eye.L','CHR_Eye.R','CHR_Eyebrow.L','CHR_Eyebrow.R','CHR_UpperLashline.L','CHR_UpperLashline.R','CHR_LowerLashline.L','CHR_LowerLashline.R'}
 for o in list(bpy.data.objects):
  if o!=rig and o.name not in keep and o.type!='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
 for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
 def enable(lc):
  lc.exclude=False;lc.hide_viewport=False
  for ch in lc.children:enable(ch)
 enable(bpy.context.view_layer.layer_collection)
 for o in bpy.data.objects:
  o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 COL=bpy.data.collections.new('KAI | Editable character');bpy.context.scene.collection.children.link(COL)
 skin=mat('Warm brown skin','A96A49',.63);dark=mat('Warm dark contours','29160F',.55);hair=mat('Pearl hair with lavender shadows','E2D1D7',.3);cream=mat('Cream rubber and eyes','F6E9C7',.55);white=mat('Ivory cotton laces','FFF4DF',.75)
 purple=mat('Violet cotton','4B2274',.8);boots=mat('Deep purple leather','341246',.37);gold=mat('Gold details','E6AD3F',.32,.25);shorts=mat('Golden camouflage canvas','DCA132',.86);strap=mat('Brown elbow straps','603018',.72);spot=mat('Pad spots','2F1249',.75)
 nt=hair.node_tree;ao=nt.nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.045;ao.only_local=True;ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=rgb('A17E96');ramp.color_ramp.elements[1].color=rgb('F0DFCD');e=ramp.color_ramp.elements.new(.45);e.color=rgb('CDB0C0');nt.links.new(ao.outputs['AO'],ramp.inputs[0]);nt.links.new(ramp.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
 pattern(shorts,[(0,'B8741B'),(.44,'D39226'),(.53,'E3A433'),(.61,'C58120')],7,1)
 # Fine directional textile surface; keep the broad silhouette clean.
 nt=purple.node_tree;n=nt.nodes;l=nt.links;tc=n.new('ShaderNodeTexCoord');wave=n.new('ShaderNodeTexWave');wave.bands_direction='Z';wave.inputs['Scale'].default_value=95;wave.inputs['Distortion'].default_value=4;wave.inputs['Detail Scale'].default_value=2
 l.new(tc.outputs['Generated'],wave.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=rgb('45216C');r.color_ramp.elements[1].color=rgb('512879');l.new(wave.outputs['Color'],r.inputs[0]);l.new(r.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
 for o in list(bpy.data.objects):
  if o.name.startswith('CHR_'):
   if o.name=='CHR_Body' or 'Ear.' in o.name:o.data.materials[0]=skin
   if 'Lashline' in o.name or 'Eyebrow' in o.name:o.data.materials.clear();o.data.materials.append(dark)
 body=bpy.data.objects['CHR_Body']
 for v in body.data.vertices:
  if abs(v.co.x)<.036 and .697<v.co.z<.730 and v.co.y<-.10:v.co.z=.714+(v.co.z-.714)*.36
  if abs(v.co.x)<.026 and .742<v.co.z<.780 and v.co.y<-.142:v.co.y+=.006
 # Extract a full symmetric rest surface for the shorts and transfer donor weights.
 for mo in body.modifiers:
  if mo.type=='MIRROR':mo.show_viewport=True;mo.show_render=True
  if mo.type in {'SUBSURF','ARMATURE'}:mo.show_viewport=False;mo.show_render=False
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());src=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
 vs=[];fs=[];mapping={}
 for p in src.polygons:
  if not all(.19<v.co.z<.445 for v in [src.vertices[i] for i in p.vertices]):continue
  face=[]
  for idx in p.vertices:
   if idx not in mapping:
    co=src.vertices[idx].co.copy();z=max(.23,min(.435,co.z));t=max(0,min(1,(.37-z)/.14));sg=1 if co.x>=0 else -1;center=sg*.074
    co.x=center+(co.x-center)*(1.12+.22*t);co.y*=1.18+.18*t;co.z=z;mapping[idx]=len(vs);vs.append(co)
   face.append(mapping[idx])
  fs.append(face)
 pants=mesh('Cargo shorts / continuous pelvis',vs,fs,shorts,2)
 for g in body.vertex_groups:pants.vertex_groups.new(name=g.name)
 for idx,new in mapping.items():
  for g in src.vertices[idx].groups:pants.vertex_groups[g.group].add([new],g.weight,'REPLACE')
 mo=pants.modifiers.new('Canvas thickness','SOLIDIFY');mo.thickness=.003
 mo=pants.modifiers.new('Base weight transfer','ARMATURE');mo.object=rig
 ev.to_mesh_clear()
 for mo in body.modifiers:mo.show_viewport=True;mo.show_render=True
 # Fit the concealed feet inside the boots while keeping continuous shins.
 for v in body.data.vertices:
  if v.co.z<.205:
   t=min(1,max(0,(.205-v.co.z)/.05));v.co.x=.084+(v.co.x-.084)*(1-.27*t);v.co.y*=1-.35*t
 log('Building tank, cargo pockets and boots')
 # Quad tank panels, open armholes, joined shoulder straps.
 v=[];f=[];nx=17;rows=[.422,.429,.465,.505,.535,.565,.587]
 for back in (False,True):
  for j,z in enumerate(rows):
   for i in range(nx):
    u=-1+2*i/(nx-1);x=u*(.099 if j<4 else .107);y=(.072 if back else -.077)*math.sqrt(max(.20,1-.72*u*u));zz=z
    if j==6:zz=.593-.020*max(0,1-(abs(u)/.48)**2)
    if j==5:zz=.560-.006*max(0,1-(abs(u)/.48)**2)
    v.append((x,y,zz))
  off=(len(rows)*nx if back else 0)
  for j in range(len(rows)-1):
   for i in range(nx-1):a=off+j*nx+i;f.append((a,a+1,a+1+nx,a+nx))
 off=len(rows)*nx
 for j in range(3):
  for i in (0,nx-1):a=j*nx+i;f.append((a,a+nx,a+nx+off,a+off))
 for i in list(range(4))+list(range(12,16)):
  a=6*nx+i;f.append((a,a+1,a+1+off,a+off))
 top=mesh('Sleeveless tank',v,f,purple,2);mo=top.modifiers.new('Cotton thickness','SOLIDIFY');mo.thickness=.003
 for bn in ['Spine','Chest']:top.vertex_groups.new(name=bn)
 for p in top.data.vertices:
  w=max(0,min(1,(p.co.z-.46)/.10));top.vertex_groups['Chest'].add([p.index],w,'REPLACE');top.vertex_groups['Spine'].add([p.index],1-w,'REPLACE')
 mo=top.modifiers.new('Tank weights','ARMATURE');mo.object=rig
 lathe('Waistband',[(.412,.105,.085,0),(.415,.107,.086,0),(.436,.106,.083,0),(.439,.103,.080,0)],0,0,shorts,sub=1,bone='Hips')
 ball('Waist button',(0,-.087,.426),(.009,.003,.009),gold,'Hips')
 tube('Fly seam',[(.003,-.089,.418),(.004,-.092,.389),(.002,-.095,.372)],.0012,gold,'Hips')
 for sg,side in [(1,'L'),(-1,'R')]:
  leg='UpperLeg.'+side;foot='Foot.'+side;arm='UpperArm.'+side
  # Cargo patch wraps around the outer thigh rather than floating in front.
  pocket=box('Cargo pocket '+side,(sg*.137,-.012,.288),(.028,.098,.080),shorts,leg)
  flap=box('Cargo flap '+side,(sg*.150,-.012,.327),(.015,.104,.025),shorts,leg)
  for yy in [-.06,.034]:tube('Pocket stitching '+side,[(sg*.148,yy,.317),(sg*.150,yy,.286),(sg*.147,yy,.253)],.001, gold,leg)
  tube('Slant pocket '+side,[(sg*.030,-.086,.414),(sg*.054,-.091,.395),(sg*.101,-.076,.392)],.0016,gold,'Hips')
  # Arm bands are modeled in the base's T-pose and follow the upper arm.
  pts=[(sg*.179,.036*cos(a),.560+.036*sin(a)) for a in [i*2*pi/48 for i in range(49)]]
  tube('Elbow strap '+side,pts,.012,strap,arm,depth=.65)
  ball('Violet elbow guard '+side,(sg*.189,.035,.560),(.031,.021,.033),purple,arm)
  for dx,dz in [(-.012,-.013),(.012,-.012),(0,.009),(.014,.016),(-.014,.015)]:ball('Pad spot '+side,(sg*(.189+dx),.054,.560+dz),(.004,.0018,.004),spot,arm)
  cx=sg*.084
  sole=grooved_sole(side,cx,cream,foot)
  shoe=lathe('High top boot '+side,[(.026,.077,.110,0),(.030,.079,.111,0),(.056,.080,.108,0),(.081,.075,.097,.005),(.098,.068,.081,.027),(.122,.062,.072,.035),(.157,.061,.073,.035),(.177,.067,.078,.034),(.181,.067,.078,.034),(.181,.063,.074,.034),(.174,.062,.073,.034)],cx,-.035,boots,power=3.0,sub=2,bone=foot)
  # Raised tongue, eyelets, crossed laces and oversize angular bow loops.
  tongue=ball('Boot tongue '+side,(cx,-.069,.144),(.040,.010,.052),boots,foot)
  for k in range(6):
   z=.101+k*.012;y=-.086+(z-.101)*.19;hw=.028-.006*k/5
   for s in [-1,1]:ball('Eyelet '+side,(cx+s*hw,y,z),(.004,.002,.004),gold,foot)
   if k<5:
    for s in [-1,1]:tube('Cross lace '+side,[(cx+s*hw,y-.003,z),(cx,y-.009,z+.006),(cx-s*(hw-.0012),y-.001,z+.012)],.0017,white,foot)
  ball('Lace knot '+side,(cx,-.079,.173),(.006,.004,.005),white,foot)
  for s in [-1,1]:
   tube('Tall triangular bow '+side,[(cx,-.078,.174),(cx+s*.043,-.075,.181),(cx+s*.024,-.063,.224),(cx+s*.008,-.075,.181),(cx,-.078,.174)],.002,white,foot)
   tube('Lace end '+side,bez([(cx,-.079,.173),(cx+s*.020,-.090,.160),(cx+s*.020,-.092,.149),(cx+s*.008,-.094,.140)],15),.0016,white,foot)
  # Angular mischievous eyes projected onto the actual curved toe, not floating disks.
  bpy.context.view_layer.update();shoeBVH=BVHTree.FromObject(shoe,bpy.context.evaluated_depsgraph_get())
  def eye_patch(name,ex,es,span,lower,upper,material,offset):
   vv=[];ff=[];NX=13;NY=4
   for j in range(NY):
    t=j/(NY-1)
    for i in range(NX):
     u=-1+2*i/(NX-1);x=ex+u*span;z=lower(u)*(1-t)+upper(u)*t;hit=shoeBVH.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))[0];y=hit.y-offset if hit else -.140-offset;vv.append((x,y,z))
   for j in range(NY-1):
    for i in range(NX-1):a=j*NX+i;ff.append((a,a+1,a+1+NX,a+NX))
   return mesh(name,vv,ff,material,0,foot)
  for es in [-1,1]:
   ex=cx+es*.036
   eye_patch('Monster dark eye '+side,ex,es,.023,lambda u:.053+.005*abs(u),lambda u:.075+es*u*.006,dark,.0007)
   eye_patch('Monster cream eye '+side,ex,es,.019,lambda u:.056+.005*abs(u),lambda u:.071+es*u*.005,cream,.0010)
   eye_patch('Monster slit pupil '+side,ex+es*.003,es,.004,lambda u:.059,lambda u:.072,dark,.0014)
 log('Building layered pearl hair')
 # Open ellipsoidal scalp cap: quads below a small hidden crown pole.
 v=[];f=[];N=64;rows=20
 for j in range(rows):
  for i in range(N):
   a=2*pi*i/N;front=max(0,-sin(a));bottom=.735+.239*front**.4;thetaMax=math.acos((bottom-.842)/.212);t=.025+(thetaMax-.025)*j/(rows-1)
   v.append((.185*sin(t)*cos(a),.022+.202*sin(t)*sin(a),.842+.212*cos(t)))
 for j in range(rows-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;f.append((a,b,b+N,a+N))
 mesh('Pearl scalp cap',v,f,hair,1,'Head')
 # Broad locks, flattened cross sections and tapered hooked tips.
 locks=[
  ([(.080,.070,1.000),(.040,.090,1.100),(-.100,.055,1.070),(-.190,.020,1.065)],.075),
  ([(.035,-.02,1.035),(-.08,-.075,1.075),(-.18,-.105,1.02),(-.240,-.08,1.058)],.064),
  ([(-.015,-.075,1.033),(-.14,-.150,.992),(-.10,-.180,.835),(-.035,-.180,.865)],.065),
  ([(.02,-.04,1.035),(.09,-.12,1.075),(.17,-.12,1.00),(.240,-.08,1.055)],.060),
  ([(.055,-.105,.993),(.137,-.140,.968),(.106,-.155,.865),(.176,-.115,.896)],.052),
  ([(-.13,-.095,.965),(-.21,-.14,.91),(-.20,-.15,.795),(-.137,-.14,.787)],.046),
  ([(.145,-.09,.949),(.213,-.10,.884),(.185,-.13,.799),(.136,-.14,.786)],.045),
 ]
 for i,(p,w) in enumerate(locks):
  normal=(0,0,1) if i==0 else ((0,-.7,.7) if i in (1,3) else (0,-1,0))
  hair_lock('Flowing fringe %02d'%i,p,w,hair,normal)
 # Layered side and rear waves, arranged in staggered rows around the skull.
 for row in range(4):
  z=1.025-row*.073;radius=[.103,.164,.182,.163][row]
  for j in range(7):
   a=-.10+(pi+.20)*j/6
   a+=(.15 if row%2 else -.10);root=Vector((radius*cos(a),.025+radius*sin(a),z));out=Vector((cos(a),sin(a),0));tan=Vector((-sin(a),cos(a),0));flow=1 if j<4 else -1
   p=[root-out*.013,root+out*.028-tan*.025*flow+Vector((0,0,-.040)),root+out*.024+tan*.065*flow+Vector((0,0,-.145)),root+out*.052+tan*.105*flow+Vector((0,0,-.095))]
   hair_lock('Layer %d wave %02d'%(row,j),p,.061 if row<3 else .048,hair,normal=tuple(out))
 # Soft nape feathering.
 for j in range(7):
  a=.10+(pi-.2)*j/6;r=Vector((.100*cos(a),.035+.12*sin(a),.746));out=Vector((cos(a),sin(a),0))
  hair_lock('Nape feather %02d'%j,[r,r+out*.035+Vector((0,0,-.045)),r+out*.045+Vector((0,0,-.115)),r+out*.075+Vector((0,0,-.089))],.033,hair,normal=tuple(out))
 # Kai's flatter, relaxed upper eyelids; the donor eyeballs and facial mesh remain editable.
 bpy.context.view_layer.update();faceBVH=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
 for sg,side in [(1,'L'),(-1,'R')]:
  cx=sg*.079
  eyeBVH=BVHTree.FromObject(bpy.data.objects['CHR_Eye.'+side],bpy.context.evaluated_depsgraph_get())
  def lid_y(x,z,u,t):
   hit=faceBVH.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))[0];surface=hit.y if hit else -.117
   eyehit=eyeBVH.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))[0];eyeY=eyehit.y if eyehit else surface
   target=min(eyeY-.0025,surface-.001);w=(1-abs(u)**12)*(1-t**12)
   return surface+.0008+(target-surface-.0008)*w
  vv=[];ff=[];N=25
  for row in range(7):
   t=row/6
   for i in range(N):
    u=-1+2*i/(N-1);x=cx+.048*u;low=.798+.003*u*sg;high=.842-.010*abs(u);z=low*(1-t)+high*t
    y=lid_y(x,z,u,t)
    vv.append((x,y,z))
  for j in range(6):
   for i in range(N-1):a=j*N+i;ff.append((a,a+1,a+1+N,a+N))
  lid=mesh('Relaxed upper lid '+side,vv,ff,skin,1,'Head')
  old=bpy.data.objects.get('CHR_UpperLashline.'+side)
  if old:bpy.data.objects.remove(old,do_unlink=True)
  tube('Relaxed upper eye contour '+side,[(cx+.048*u,lid_y(cx+.048*u,.798+.003*u*sg,u,0)-.001,.798+.003*u*sg) for u in [-1+2*i/24 for i in range(25)]],.0018,dark,'Head')
  brow=bpy.data.objects['CHR_Eyebrow.'+side]
  for v in brow.data.vertices:v.co.z=.847+(v.co.z-.856)*2.7
 # Retain the base rig and weight assignments, display with relaxed arms.
 rig.data.pose_position='POSE'
 for sg,side in [(1,'L'),(-1,'R')]:
  pb=rig.pose.bones['UpperArm.'+side];q=pb.bone.matrix_local.to_quaternion();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q.inverted()@Quaternion((0,1,0),sg*1.12)@q
 bpy.context.scene['cartoon_eye_details']=True
 # Remove inherited animation data from unused source objects and make the asset easy to navigate.
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith('CHR_'):o.name=o.name.replace('CHR_','KAI_Base_')
 bpy.context.scene.name='Kai | Character authoring'
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=8
 scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
 scene.world=bpy.data.worlds.new('Kai studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.18,.18,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 scene.view_settings.view_transform='AgX'
 def area(name,pos,power,size):
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
 area('Key',(-1.8,-2.4,3),160,2.1);area('Fill',(2,-1.3,1.5),90,2);area('Rim',(0,2,2.5),180,1.7)
 camd=bpy.data.cameras.new('Kai turnaround');cam=bpy.data.objects.new('Kai turnaround',camd);scene.collection.objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.ortho_scale=1.27
 for o in bpy.context.selected_objects:o.select_set(False)
 rig.select_set(True);bpy.context.view_layer.objects.active=rig
 # Pack the reference for an independent editable .blend.
 ref=bpy.data.images.load(str(OUT/'references/kai_turnaround.png'),check_existing=True);ref.pack();ref.use_fake_user=True
 scene['kai_source']='Existing user-authored chibi base, cloned from art/yara/yara.blend; Kai reference supplied by user.'
 scene['kai_status']='Appearance model with inherited base rig. Kai clothing and motion require gameplay deformation review before integration.'
 # Retain only Kai's live authoring dependencies and a clean collection hierarchy.
 for action in list(bpy.data.actions):bpy.data.actions.remove(action)
 needed_empty=set()
 for o in bpy.data.objects:
  if o.parent and o.parent.type=='EMPTY':needed_empty.add(o.parent)
 for ma in bpy.data.materials:
  if ma.users and ma.use_nodes:
   for node in ma.node_tree.nodes:
    if hasattr(node,'object') and node.object and node.object.type=='EMPTY':needed_empty.add(node.object)
 for o in list(bpy.data.objects):
  if o.type=='EMPTY' and o not in needed_empty:bpy.data.objects.remove(o,do_unlink=True)
 for o in list(bpy.data.objects):
  if o.type in {'MESH','ARMATURE','EMPTY'}:
   for c in list(o.users_collection):c.objects.unlink(o)
   COL.objects.link(o)
 for c in list(bpy.data.collections):
  if c!=COL and len(c.objects)==0 and len(c.children)==0:bpy.data.collections.remove(c)
 for tx in list(bpy.data.texts):bpy.data.texts.remove(tx)
 bpy.data.orphans_purge(do_recursive=True)
 scene.render.filepath=str(OUT/'previews/front.png');cam.location=(0,-3,.57);cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.preferences.filepaths.save_version=0
 log('Saving Kai source');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 for name,pos in [('front',(0,-3,.57)),('three_quarter',(1.8,-3,1.0)),('side',(3,0,.57)),('back',(0,3,.57))]:
  log('Rendering '+name);cam.location=pos;cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True)
 log('Kai source and four review renders complete')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'error.txt').write_text(traceback.format_exc());raise
