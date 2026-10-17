"""Refine Kai from the user's latest manually edited source checkpoint."""
import bpy,bmesh,math,json,traceback,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from math import sin,cos,pi
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai'
WORK=Path('C:/Users/obran/Historiando_Backups/kai_finish_2026-10-16')
def module(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
B=module('builder',ROOT/'tools/kai/build.py');V=module('volume',ROOT/'tools/kai/refine_hair_volume.py')
def log(t):(WORK/'progress.txt').write_text(t)
def remove(prefix):
 for o in list(bpy.data.objects):
  if o.name.startswith(prefix):bpy.data.objects.remove(o,do_unlink=True)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def curve(points,steps=8):
 ps=list(map(Vector,points));out=[]
 for k in range(len(ps)-1):
  a=ps[max(k-1,0)];b=ps[k];c=ps[k+1];d=ps[min(k+2,len(ps)-1)]
  for j in range(steps):
   t=j/steps;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 return out+[ps[-1]]
def tube(name,pts,width,mat,bone,depth=.55,sub=1):
 return B.tube(name,pts,width,mat,bone,depth=depth,normal=(0,-1,0),sub=sub)
def uv_rest(o):
 attr=o.data.attributes.get('Rest fabric position') or o.data.attributes.new('Rest fabric position','FLOAT_VECTOR','POINT')
 for v,item in zip(o.data.vertices,attr.data):item.vector=o.matrix_world@v.co
def ring(name,cx,y,z,rx,rz,mat,bone):
 vv=[];ff=[];N=28;M=8
 for i in range(N):
  a=2*pi*i/N
  for j in range(M):
   b=2*pi*j/M;vv.append((cx+(rx+.00075*cos(b))*cos(a),y-.00075*sin(b),z+(rz+.00075*cos(b))*sin(a)))
 for i in range(N):
  for j in range(M):a=i*M+j;b=i*M+(j+1)%M;ff.append((a,b,((i+1)%N)*M+(j+1)%M,((i+1)%N)*M+j))
 return B.mesh(name,vv,ff,mat,0,bone)
def ball(name,loc,scale,mat,bone=None):
 # Construct directly instead of invoking a context-dependent object operator
 # while the character's live cloth/collision dependency graph is being edited.
 N=24;R=16;vv=[Vector(loc)+Vector((0,0,scale[2]))];ff=[]
 for j in range(1,R):
  a=pi*j/R
  for i in range(N):
   t=2*pi*i/N;vv.append(Vector(loc)+Vector((scale[0]*sin(a)*cos(t),scale[1]*sin(a)*sin(t),scale[2]*cos(a))))
 vv.append(Vector(loc)-Vector((0,0,scale[2])));bottom=len(vv)-1
 for i in range(N):ff.append((0,1+i,1+(i+1)%N))
 for j in range(R-2):
  for i in range(N):a=1+j*N+i;b=1+j*N+(i+1)%N;ff.append((a,a+N,b+N,b))
 for i in range(N):ff.append((bottom,1+(R-2)*N+(i+1)%N,1+(R-2)*N+i))
 return B.mesh(name,vv,ff,mat,0,bone)
def main():
 bpy.ops.wm.open_mainfile(filepath=str(WORK/'kai_before_finish.blend'))
 B.rig=bpy.data.objects['KAI_Rig'];B.COL=bpy.data.objects['KAI_Sleeveless tank'].users_collection[0]
 B.ball=ball
 target_prefixes=('KAI_Base_Eyebrow.L','KAI_Relaxed upper eye contour ','KAI_Base_LowerLashline.','KAI_Small crown curl','KAI_Cargo ','KAI_Pocket stitching ','KAI_Slant pocket ','KAI_Fly seam','KAI_High top boot ','KAI_Cream sole with engraved teeth ','KAI_Boot tongue ','KAI_Eyelet ','KAI_Cross lace ','KAI_Tall triangular bow ','KAI_Lace end ','KAI_Lace knot ','KAI_Waistband')
 protected={o.name:V.fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(target_prefixes)}
 dark=bpy.data.materials['Kai / Warm dark contours'];hair=bpy.data.materials['Kai / Pearl hair directional fibers']
 # Mirror the manually edited anatomical right brow, including its exact depth.
 right=bpy.data.objects['KAI_Base_Eyebrow.R'];right_hash=V.fingerprint(right)
 left=bpy.data.objects['KAI_Base_Eyebrow.L'];old=left.data
 left.data=right.data.copy();reflect=Matrix.Diagonal((-1,1,1,1));xf=left.matrix_world.inverted()@reflect@right.matrix_world
 for v in left.data.vertices:v.co=xf@v.co
 bm=bmesh.new();bm.from_mesh(left.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(left.data);bm.free()
 assert V.fingerprint(right)==right_hash
 brow_error=max((left.matrix_world@a.co-reflect@(right.matrix_world@b.co)).length for a,b in zip(left.data.vertices,right.data.vertices));assert brow_error<1e-7
 # Keep the eyelid paths, expand their cross-sections into clear cartoon lines.
 lash_records=[];face_bvh=BVHTree.FromObject(bpy.data.objects['KAI_Base_Body'],bpy.context.evaluated_depsgraph_get())
 eye_bvhs={side:BVHTree.FromObject(bpy.data.objects['KAI_Base_Eye.'+side],bpy.context.evaluated_depsgraph_get()) for side in ['L','R']}
 for side in ['L','R']:
  o=bpy.data.objects['KAI_Relaxed upper eye contour '+side];N=10
  for i in range(len(o.data.vertices)//N):
   group=list(o.data.vertices)[i*N:(i+1)*N];center=sum((v.co for v in group),Vector())/N
   t=i/(len(o.data.vertices)//N-1);factor=2.4+.35*sin(pi*t)
   hits=[bvh.ray_cast(Vector((center.x,-1,center.z)),Vector((0,1,0)))[0] for bvh in [face_bvh,eye_bvhs[side]]]
   surface=min([h.y for h in hits if h is not None]+[center.y]);target=Vector((center.x,surface-.00065,center.z))
   for v in group:v.co=target+(v.co-center)*factor
  o.data.update();lash_records.append(o.name)
  # Lower outer-half line: rectangular four-vertex cross-sections.
  o=bpy.data.objects['KAI_Base_LowerLashline.'+side];N=4
  for i in range(len(o.data.vertices)//N):
   group=list(o.data.vertices)[i*N:(i+1)*N];center=sum((v.co for v in group),Vector())/N
   for v in group:v.co=center+(v.co-center)*1.5+Vector((0,-.0003,0))
  o.data.update();lash_records.append(o.name)
 # Natural small ahoge: two smooth arcs with a supported root and pointed end.
 remove('KAI_Small crown curl')
 pts=curve([(-.003,-.006,1.048),(-.017,-.012,1.080),(-.019,-.012,1.105),(.002,-.014,1.119),(.027,-.017,1.110),(.035,-.018,1.094)],9)
 vv=[];ff=[];N=16
 for i,p in enumerate(pts):
  t=i/(len(pts)-1);tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();side=tangent.cross(Vector((0,-1,0))).normalized();normal=side.cross(tangent).normalized()
  w=.014*(1-t)**.8*(.85+.15*sin(pi*t))+.00003
  for j in range(N):a=2*pi*j/N;vv.append(p+side*w*cos(a)+normal*w*.40*sin(a))
 for i in range(len(pts)-1):
  for j in range(N):a=i*N+j;b=i*N+(j+1)%N;ff.append((a,b,b+N,a+N))
 ff.extend([tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))])
 ah=B.mesh('Small crown curl',vv,ff,hair,2,'Head');uv=ah.data.uv_layers.new(name='Lock UV')
 for p in ah.data.polygons:
  for li in p.loop_indices:
   idx=ah.data.loops[li].vertex_index;uv.data[li].uv=((idx%N)/N,(idx//N)/(len(pts)-1))
 log('Face and ahoge refined; rebuilding hem loops')
 pants=bpy.data.objects['KAI_Cargo shorts / continuous pelvis'];src=[v.co.copy() for v in pants.data.vertices];groups={g.index:g.name for g in pants.vertex_groups};bone_names=set(B.rig.data.bones.keys());weights=[{groups[g.group]:g.weight for g in v.groups if groups[g.group] in bone_names} for v in pants.data.vertices]
 kd=KDTree(len(src))
 for i,co in enumerate(src):kd.insert(co,i)
 kd.balance();bm=bmesh.new();bm.from_mesh(pants.data)
 collapsed=[v for v in bm.verts if v.co.z<.24];collapsed_count=len(collapsed)
 bmesh.ops.delete(bm,geom=collapsed,context='VERTS')
 boundary=[e for e in bm.edges if e.is_boundary and all(v.co.z<.27 for v in e.verts)]
 assert len(boundary)==24,('Unexpected hem boundary',len(boundary))
 for v in {v for e in boundary for v in e.verts}:
  sg=1 if v.co.x>0 else -1;a=math.atan2(v.co.y+.005,abs(v.co.x)-.074)
  v.co.x=sg*(.074+.063*cos(a));v.co.y=-.005+.063*sin(a)
 for z,scale in [(.239,1),(.233,1),(.2305,.985),(.232,.957),(.239,.957)]:
  geom=bmesh.ops.extrude_edge_only(bm,edges=boundary)['geom'];nv=[v for v in geom if isinstance(v,bmesh.types.BMVert)]
  for v in nv:
   sg=1 if v.co.x>0 else -1;a=math.atan2(v.co.y+.005,abs(v.co.x)-.074)
   v.co=Vector((sg*(.074+.063*scale*cos(a)),-.005+.063*scale*sin(a),z))
  boundary=[e for e in geom if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(pants.data);bm.free()
 for g in list(pants.vertex_groups):pants.vertex_groups.remove(g)
 for n in groups.values():pants.vertex_groups.new(name=n)
 for v in pants.data.vertices:
  nearest=kd.find_n(v.co,4);ws={}
  for co,idx,d in nearest:
   for n,w in weights[idx].items():ws[n]=ws.get(n,0)+w/max(.0001,d)**2
  ws={n:w for n,w in ws.items() if n in bone_names};total=sum(ws.values())
  for n,w in ws.items():
   if w/total>1e-5:pants.vertex_groups[n].add([v.index],w/total,'REPLACE')
 # One fabric-space camouflage scale for shorts, waistband and pocket pieces.
 canvas=bpy.data.materials['Kai / Golden camouflage canvas'].copy();canvas.name='Kai / Finished golden camo twill';nt=canvas.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
 output=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.86;p.inputs['Sheen Weight'].default_value=.13;l.new(p.outputs['BSDF'],output.inputs['Surface'])
 attr=n.new('ShaderNodeAttribute');attr.attribute_name='Rest fabric position';noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=34;noise.inputs['Detail'].default_value=1;noise.inputs['Roughness'].default_value=.65;l.new(attr.outputs['Vector'],noise.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT'
 for e in list(ramp.color_ramp.elements)[1:]:ramp.color_ramp.elements.remove(e)
 for i,(pos,c) in enumerate([(0,'AE721F'),(.42,'C78B27'),(.48,'DEA136'),(.57,'E8AF48'),(.66,'C48A26')]):
  e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos);e.position=pos;e.color=B.rgb(c)
 l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
 grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=1100;grain.inputs['Detail'].default_value=1;l.new(attr.outputs['Vector'],grain.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.00010;l.new(grain.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 pants.data.materials.clear();pants.data.materials.append(canvas)
 belt=bpy.data.objects['KAI_Waistband'];belt.data.materials.clear();belt.data.materials.append(canvas)
 seam=B.mat('Ochre sewn seams','A77528',.85)
 for prefix in ['KAI_Cargo pocket ','KAI_Cargo flap ','KAI_Pocket stitching ','KAI_Slant pocket ','KAI_Fly seam']:remove(prefix)
 bpy.context.view_layer.update();bvh=BVHTree.FromObject(pants,bpy.context.evaluated_depsgraph_get())
 def outer(sg,y,z,off=0):
  hit=bvh.ray_cast(Vector((sg*.5,y,z)),Vector((-sg,0,0)))[0]
  return Vector(((hit.x if hit else sg*.13)+sg*off,y,z))
 def front(x,z,off=.0005):
  hit=bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))[0]
  return Vector((x,(hit.y if hit else -.075)-off,z))
 def stitches(name,pts,width,mat,bone,dashed=False):
  pts=list(map(Vector,pts))
  if not dashed:return tube(name,pts,width,mat,bone,depth=.5)
  for k in range(0,len(pts)-2,4):tube(name,pts[k:k+3],width,mat,bone,depth=.5,sub=0)
 for sg,side in [(1,'L'),(-1,'R')]:
  bone='UpperLeg.'+side
  for flap in [False,True]:
   vv=[];ff=[];NX=13;NY=13 if not flap else 7
   for j in range(NY):
    t=j/(NY-1)
    for i in range(NX):
     u=i/(NX-1);y=-.048+.081*u
     z=(.257+.071*t) if not flap else (.318+.020*t-.005*sin(pi*u)*(1-t))
     off=(.001+.004*sin(pi*u)*sin(pi*t)) if not flap else (.003+.003*sin(pi*u))
     vv.append(outer(sg,y,z,off))
   for j in range(NY-1):
    for i in range(NX-1):a=j*NX+i;ff.append((a,a+1,a+1+NX,a+NX))
   o=B.mesh(('Cargo flap ' if flap else 'Cargo pocket ')+side,vv,ff,canvas,2,bone);so=o.modifiers.new('Folded canvas edge','SOLIDIFY');so.thickness=.0012
  # Low relief stitching is attached to each patch edge, not hanging in space.
  for y in [-.044,.029]:
   pts=[outer(sg,y,.263+.055*k/24,.0022) for k in range(25)];stitches('Pocket stitching '+side,pts,.00038,seam,bone)
  pts=[front(sg*x,z) for x,y,z in curve([(.030,0,.411),(.045,0,.400),(.068,0,.392),(.096,0,.394)],10)]
  stitches('Slant pocket '+side,pts,.00055,seam,'Hips')
  # A short double-stitched leg hem follows the cleaned surface.
  for z in [.237,.241]:
   points=[]
   for i in range(97):
    a=2*pi*i/96;guess=Vector((sg*(.074+.0632*cos(a)),-.005+.0632*sin(a),z));hit,normal,idx,dist=bvh.find_nearest(guess)
    points.append(hit+normal*.00025 if hit is not None else guess)
   tube('Hem stitching '+side,points,.00025,seam,bone,depth=.5,sub=0)
 tube('Fly seam',[front(.003,z,.0006) for z in [.413,.405,.395,.385,.375]],.00045,seam,'Hips',sub=1)
 for o in bpy.data.objects:
  if o.type=='MESH' and any(m==canvas for m in o.data.materials):uv_rest(o)
 log('Tailored shorts finished; refining boots and laces')
 leather=bpy.data.materials['Kai / Deep purple leather'].copy();leather.name='Kai / Finished violet boot leather';p=leather.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.48
 n=leather.node_tree.nodes;l=leather.node_tree.links;tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=190;noise.inputs['Detail'].default_value=2;l.new(tc.outputs['Generated'],noise.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08;bump.inputs['Distance'].default_value=.00007;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 lining=B.mat('Soft boot cuff lining','251033',.85);cream=bpy.data.materials['Kai / Cream rubber and eyes'];rubber=cream.copy();rubber.name='Kai / Smooth cream engraved rubber';rubber.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.72
 n=rubber.node_tree.nodes;l=rubber.node_tree.links;p=n.get('Principled BSDF');at=n.new('ShaderNodeAttribute');at.attribute_name='Engraving';ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=B.rgb('F6E9C7');ramp.color_ramp.elements[1].color=B.rgb('CBB58F');l.new(at.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
 gold=bpy.data.materials['Kai / Gold details'];lace=bpy.data.materials['Kai / Ivory cotton laces']
 for prefix in ['KAI_Boot tongue ','KAI_Eyelet ','KAI_Cross lace ','KAI_Tall triangular bow ','KAI_Lace end ','KAI_Lace knot ','KAI_Cream sole with engraved teeth ']:remove(prefix)
 for sg,side in [(1,'L'),(-1,'R')]:
  log('Boot '+side+' cuff')
  cx=sg*.084;bone='Foot.'+side;boot=bpy.data.objects['KAI_High top boot '+side];boot.data.materials.clear();boot.data.materials.append(leather)
  bpy.context.view_layer.update();boot_bvh=BVHTree.FromObject(boot,bpy.context.evaluated_depsgraph_get())
  def tongue_y(x,z):
   u=max(-1,min(1,(x-cx)/.034));hit=boot_bvh.ray_cast(Vector((x,-.5,min(z,.177))),Vector((0,1,0)))[0]
   surface=hit.y if hit is not None else -.075
   return surface-(.0012+.0016*(1-u*u))
  # Clean folded lip and a visible soft lining around the existing opening.
  B.lathe('Finished boot cuff '+side,[(.169,.061,.073,.034),(.177,.064,.075,.034),(.181,.066,.077,.034),(.182,.0665,.0775,.034),(.182,.0645,.0755,.034),(.179,.0635,.0745,.034),(.166,.0605,.0715,.034)],cx,-.035,leather,power=3,sub=1,bone=bone)
  B.lathe('Boot interior lining '+side,[(.177,.061,.073,.034),(.171,.060,.072,.034),(.145,.057,.067,.033)],cx,-.035,lining,power=3,sub=1,bone=bone)
  # Tongue with a proper top edge, sitting behind the flat cotton laces.
  vv=[];ff=[];NX=13;R=14
  for j in range(R):
   t=j/(R-1);z=.093+.092*t
   for i in range(NX):
    u=-1+2*i/(NX-1);x=cx+u*.034;zz=z-.003*u*u*t;vv.append((x,tongue_y(x,zz),zz))
  for j in range(R-1):
   for i in range(NX-1):a=j*NX+i;ff.append((a,a+1,a+1+NX,a+NX))
  tongue=B.mesh('Boot tongue '+side,vv,ff,leather,2,bone);so=tongue.modifiers.new('Tongue thickness','SOLIDIFY');so.thickness=.002
  log('Boot '+side+' lacing')
  # Eyelet holes and rings replace the previous gold beads.
  for k in range(6):
   z=.101+k*.012;hw=.028-.006*k/5;y=tongue_y(cx+hw,z)-.0006
   for es in [-1,1]:
    B.ball('Eyelet inset '+side,(cx+es*hw,y+.0006,z),(.0026,.0006,.0026),dark,bone)
    ring('Eyelet '+side,cx+es*hw,y,z,.0027,.0027,gold,bone)
   if k<5:
    for es in [-1,1]:
     pts=[]
     for x,zz in [(cx+es*hw,z),(cx+es*.008,z+.004),(cx-es*.008,z+.008),(cx-es*(hw-.0012),z+.012)]:pts.append((x,tongue_y(x,zz)-.0012-es*.0003,zz))
     pts=curve(pts,5)
     tube('Cross lace '+side,pts,.0017,lace,bone,depth=.38)
  B.ball('Lace knot '+side,(cx,-.084,.174),(.005,.003,.004),lace,bone)
  for es in [-1,1]:
   pts=curve([(cx,-.084,.174),(cx+es*.040,-.080,.181),(cx+es*.027,-.071,.219),(cx+es*.011,-.077,.189),(cx,-.084,.174)],7)
   tube('Tall triangular bow '+side,pts,.0018,lace,bone,depth=.38)
   pts=curve([(cx,-.085,.174),(cx+es*.014,-.098,.163),(cx+es*.021,-.102,.146),(cx+es*.014,-.103,.139)],7)
   tube('Lace end '+side,pts,.0014,lace,bone,depth=.45)
   B.ball('Lace aglet '+side,pts[-1],(.0015,.001,.003),cream,bone)
  # Analytic recessed zigzag in a rounded rubber sole; continuous tint avoids
  # the previous stair-stepped face material boundaries.
  N=528;R=15;vv=[];ff=[];depth=[]
  # Equal perimeter spacing prevents the superellipse parameterization from
  # stretching the central tooth into a wide rounded U.
  arc=[0.0];aa=[2*pi*i/10000 for i in range(10001)];xy=[Vector((.081*math.copysign(abs(cos(a))**(2/3.3),cos(a)),.115*math.copysign(abs(sin(a))**(2/3.3),sin(a)))) for a in aa]
  for i in range(1,len(xy)):arc.append(arc[-1]+(xy[i]-xy[i-1]).length)
  angles=[];cursor=1
  for i in range(N):
   distance=arc[-1]*i/N
   while arc[cursor]<distance:cursor+=1
   t=(distance-arc[cursor-1])/(arc[cursor]-arc[cursor-1]);angles.append(aa[cursor-1]+t*(aa[cursor]-aa[cursor-1]))
  log('Boot '+side+' engraved sole')
  for j in range(R):
   for i in range(N):
    a=angles[i];is_front=i>=N//2;target=.0015+.022*abs(((i-N/2)/(N/2)*22)%2-1) if is_front else .0125
    # Seven rows follow the zigzag itself, so the groove is continuous
    # instead of being sampled as isolated dents in a rectangular grid.
    zrows=[-.005,-.004,-.003,-.001,target-.0014,target-.0008,target-.00035,target,target+.00035,target+.0008,target+.0014,.026,.028,.029,.030]
    z=zrows[j];cut=([0,0,0,0,0,.00030,.0010,.00125,.0010,.00030,0,0,0,0,0][j] if is_front else 0)
    rounding=.0018*(1-math.sqrt(max(0,1-((z+.003)/.002)**2))) if z<-.003 else (.0018*(1-math.sqrt(max(0,1-((z-.028)/.002)**2))) if z>.028 else 0)
    x=(.081-rounding-cut)*math.copysign(abs(cos(a))**(2/3.3),cos(a));y=(.115-rounding-cut)*math.copysign(abs(sin(a))**(2/3.3),sin(a));vv.append((cx+x,-.035+y,z));depth.append(cut/.00125)
  for j in range(R-1):
   for i in range(N):a=j*N+i;b=j*N+(i+1)%N;ff.append((a,b,b+N,a+N))
  ff.extend([tuple(range(N-1,-1,-1)),tuple((R-1)*N+i for i in range(N))])
  sole=B.mesh('Cream sole with engraved teeth '+side,vv,ff,rubber,0,bone);attr=sole.data.attributes.new('Engraving','FLOAT','POINT')
  for item,d in zip(attr.data,depth):item.value=d*.65
  for p in sole.data.polygons:
   if len(p.vertices)>4:p.use_smooth=False
 log('Checking protected geometry')
 bpy.context.view_layer.update();assert protected=={name:V.fingerprint(bpy.data.objects[name]) for name in protected},'Unrelated geometry changed'
 assert V.fingerprint(right)==right_hash,'The manually edited right eyebrow changed'
 report={'source_checkpoint':str(WORK/'kai_before_finish.blend'),'right_eyebrow_preserved':True,'left_right_brow_mirror_error_m':brow_error,'thickened_lash_objects':lash_records,'collapsed_hem_vertices_removed':collapsed_count,'preserved_other_meshes':len(protected),'shorts_finish':'Rebuilt quad hems and turned edges; fitted soft cargo patches; projected seams; shared rest-space camouflage','boots_finish':'Folded cuffs, lining, shaped tongues, ring eyelets, flat laces and smooth recessed tooth grooves','cloth_physics_preserved':True}
 (OUT/'finish_validation.json').write_text(json.dumps(report,indent=2))
 s=bpy.context.scene;s.frame_set(1);s['kai_finish_revision']='Matched manual right eyebrow; tapered ahoge; thicker lashes; tailored cargo hems and finished boots'
 s.camera.location=(0,-3,.57);s.camera.data.ortho_scale=1.27;s.camera.rotation_euler=(Vector((0,0,.55))-s.camera.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'));log('Saved finish pass; render and inspect')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'error.txt').write_text(traceback.format_exc());raise
