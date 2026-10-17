"""Apply the user's marked thick locks to the current Kai source, preserving other edits."""
import bpy, math, json, hashlib, struct, shutil, traceback
from pathlib import Path
from datetime import datetime
from mathutils import Vector
from math import sin, cos, pi
import importlib.util
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando')
OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_work_2026-10-15')
spec=importlib.util.spec_from_file_location('kai_builder',ROOT/'tools/kai/build.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
TARGETS={'KAI_Flowing fringe %02d'%i for i in range(7)}|{'KAI_Nape feather %02d'%i for i in range(7)}
TARGETS|={'KAI_Layer %d wave %02d'%(r,j) for r in range(4) for j in (0,6)}
TARGETS|={'KAI_Layer 0 wave %02d'%j for j in (1,5)}
TARGETS|={'KAI_Jaw curl '+s for s in ('L','R')}|{'KAI_Neck curl '+s for s in ('L','R')}
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:
  h.update(struct.pack('<3f',*v.co))
  for g in v.groups:h.update(struct.pack('<if',g.group,g.weight))
 for p in o.data.polygons:h.update(str(tuple(p.vertices)).encode())
 h.update(str([m.name for m in o.data.materials]).encode());h.update(str(list(o.matrix_world)).encode())
 return h.hexdigest()
def lock(name,controls,width,normal,roundness=.88):
 pts=B.bez(controls,36);N=24;v=[];f=[];cross_sections=[]
 for i,p in enumerate(pts):
  t=i/(len(pts)-1);tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
  outward=Vector(normal).normalized();side=tangent.cross(outward)
  if side.length<.02:side=tangent.cross(Vector((1,0,0)))
  side.normalize();outward=side.cross(tangent).normalized()
  root=min(1,t/.20);root=.36+.64*root*root*(3-2*root)
  tail=min(1,max(0,(t-.62)/.38));tail=1-tail*tail*(3-2*tail)
  w=width*root*(.96+.04*sin(pi*t))*max(.001,tail)
  cross_sections.append({'t':t,'width':2*w,'depth':(roundness+.58)*w})
  for j in range(N):
   a=2*pi*j/N;u=cos(a);h=sin(a)
   if h>=0:
    # A nearly round section, with restrained longitudinal strand definition.
    h*=roundness*(1-.045*math.exp(-((abs(u)-.55)/.16)**2))
   else:h*=.58
   v.append(p+side*(u*w)+outward*(h*w))
 for i in range(len(pts)-1):
  for j in range(N):a=i*N+j;b=i*N+(j+1)%N;f.append((a,b,b+N,a+N))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))])
 o=B.mesh(name,v,f,HAIR,2,'Head');o.modifiers[0].levels=1
 uv=o.data.uv_layers.new(name='Lock UV')
 for p in o.data.polygons:
  for li in p.loop_indices:
   idx=o.data.loops[li].vertex_index;uv.data[li].uv=((idx%N)/N,(idx//N)/(len(pts)-1))
 o['hair_revision']='User-marked rounded volume and curled silhouette'
 o['cross_section_depth_width_ratio']=(roundness+.58)/2
 return o,cross_sections
def main():
 global HAIR
 backup=WORK/'kai_before_marked_thicker_hair.blend'
 if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
 # Always derive iterations from the backed-up current source, keeping non-hair edits intact.
 bpy.ops.wm.open_mainfile(filepath=str(backup))
 B.COL=bpy.data.collections['KAI | Editable character'];B.rig=bpy.data.objects['KAI_Rig']
 HAIR=bpy.data.materials['Kai / Pearl hair with lavender shadows']
 before={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in TARGETS}
 for name in TARGETS:
  o=bpy.data.objects.get(name)
  if o:bpy.data.objects.remove(o,do_unlink=True)
 locks=[
  ([(.080,.070,.998),(.025,.090,1.047),(-.120,.055,1.025),(-.217,.020,.975)],.076,(0,0,1),.88),
  ([(.035,-.025,1.025),(-.060,-.095,1.055),(-.180,-.125,1.003),(-.234,-.080,.951)],.065,(0,-.7,.7),.88),
  ([(.012,-.084,1.033),(-.139,-.180,.992),(-.145,-.200,.800),(-.010,-.175,.875)],.066,(0,-1,0),.92),
  ([(.020,-.045,1.025),(.080,-.110,1.055),(.170,-.130,1.003),(.232,-.085,.955)],.063,(0,-.7,.7),.88),
  ([(.040,-.115,.998),(.132,-.182,.980),(.110,-.185,.846),(.195,-.190,.905)],.054,(0,-1,0),.92),
  ([(-.130,-.100,.965),(-.212,-.155,.910),(-.208,-.153,.790),(-.112,-.180,.805)],.049,(0,-1,0),.92),
  ([(.145,-.095,.950),(.214,-.125,.882),(.203,-.148,.786),(.122,-.180,.803)],.048,(0,-1,0),.92),
 ]
 records=[]
 for i,(p,w,n,r) in enumerate(locks):
  o,sections=lock('Flowing fringe %02d'%i,p,w,n,r);records.append({'name':o.name,'sections':sections})
 for row in range(4):
  for j in (0,6):
   a=-.10+(pi+.20)*j/6+(.15 if row%2 else -.10);z=1.025-row*.073;radius=[.103,.164,.182,.163][row]
   root=Vector((radius*cos(a),.025+radius*sin(a),z));out=Vector((cos(a),sin(a),0));tan=Vector((-sin(a),cos(a),0));flow=1 if j<4 else -1
   p=[root-out*.012,root+out*.030-tan*.025*flow+Vector((0,0,-.040)),root+out*.030+tan*.067*flow+Vector((0,0,-.145)),root+out*.066+tan*.106*flow+Vector((0,0,-.096))]
   o,sections=lock('Layer %d wave %02d'%(row,j),p,.063 if row<3 else .051,tuple(out));records.append({'name':o.name,'sections':sections})
 for j in (1,5):
  a=-.10+(pi+.20)*j/6-.10;root=Vector((.103*cos(a),.025+.103*sin(a),1.025));out=Vector((cos(a),sin(a),0));tan=Vector((-sin(a),cos(a),0));flow=1 if j<4 else -1
  p=[root-out*.012,root+out*.030-tan*.025*flow+Vector((0,0,-.040)),root+out*.030+tan*.067*flow+Vector((0,0,-.145)),root+out*.066+tan*.106*flow+Vector((0,0,-.096))]
  o,sections=lock('Layer 0 wave %02d'%j,p,.063,tuple(out));records.append({'name':o.name,'sections':sections})
 for j in range(7):
  a=.10+(pi-.20)*j/6;r=Vector((.100*cos(a),.035+.120*sin(a),.746));out=Vector((cos(a),sin(a),0));tan=Vector((-sin(a),cos(a),0));sign=1 if j<3 else -1
  p=[r-out*.012,r-out*.040+Vector((0,0,-.055)),r-out*.075+Vector((0,0,-.145)),r+out*.025+tan*.022*sign+Vector((0,0,-.126-.022*sin(a)))]
  o,sections=lock('Nape feather %02d'%j,p,.035,tuple(out),.90);records.append({'name':o.name,'sections':sections})
 for sg,side in [(1,'L'),(-1,'R')]:
  p=[(sg*.170,.005,.793),(sg*.215,-.040,.756),(sg*.175,-.055,.687),(sg*.115,-.060,.710)]
  o,sections=lock('Jaw curl '+side,p,.030,(sg*.45,-1,0),.95);records.append({'name':o.name,'sections':sections})
  p=[(sg*.100,.065,.721),(sg*.055,.034,.658),(sg*.020,.040,.596),(sg*.111,.032,.608)]
  o,sections=lock('Neck curl '+side,p,.026,(sg*.2,-1,0),.92);records.append({'name':o.name,'sections':sections})
 bpy.context.view_layer.update()
 after={name:fingerprint(bpy.data.objects[name]) for name in before};assert before==after,'Non-target mesh changed'
 scene=bpy.context.scene;scene['kai_hair_revision']='Rounded marked locks; gravity-following crown and longer jaw/nape curls'
 report={'changed_locks':len(records),'non_target_meshes_unchanged':len(before),'records':records,'backup':str(backup)}
 (OUT/'hair_volume_validation.json').write_text(json.dumps(report,indent=2))
 cam=scene.camera;cam.location=(0,-3,.57);cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews/front.png')
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 for name,pos in [('front',(0,-3,.57)),('three_quarter',(1.8,-3,1.0)),('side',(3,0,.57)),('back',(0,3,.57))]:
  print('Rendering '+name,flush=True);(WORK/'hair_volume_progress.txt').write_text('Rendering '+name)
  cam.location=pos;cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True)
 (WORK/'hair_volume_progress.txt').write_text('Completed marked thicker hair and four renders')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'hair_volume_error.txt').write_text(traceback.format_exc());raise
