"""Fill the marked Kai hair gaps and replace intersecting rear rows with one sculpted shell."""
import bpy,math,json,shutil,traceback,importlib.util
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,exp
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_work_2026-10-15')
spec=importlib.util.spec_from_file_location('volume',ROOT/'tools/kai/refine_hair_volume.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);B=V.B
def make_rear():
 # A single valued radial surface: strand relief cannot cut through neighboring locks.
 NA=181;NT=87;v=[];f=[];amin=-.58;amax=pi+.58
 for it in range(NT):
  s=it/(NT-1)
  for ia in range(NA):
   a=amin+(amax-amin)*ia/(NA-1)
   lower=.706+.019*abs(cos(a))+.009*cos(8*a+.4)
   end=math.acos((lower-.842)/.215);theta=.18+(end-.18)*s
   relief=0
   for row in range(3):
    start=.12+row*.49;length=.84;u=(theta-start)/length
    if not 0<u<1:continue
    for col in range(9):
     rootA=amin+(amax-amin)*(col+.5)/9
     drift=.18*sin(pi*u/2)*(-1 if col>4 else 1)
     d=abs(a-rootA-drift);width=.33
     if d<width:
      relief=max(relief,.006*(sin(pi*u)**.7)*(cos(d/width*pi/2)**.85))
   envelope=sin(pi*min(1,max(0,s)))**.3
   # Keep the part and outer joins buried beneath the existing crown/fringe roots.
   edge=min(1,(a-amin)/.20,(amax-a)/.20);edge=max(0,edge)
   bump=relief*edge*envelope
   radial=sin(theta);out=Vector((cos(a),sin(a),0))
   p=Vector((.198*radial*cos(a),.025+.217*radial*sin(a),.842+.215*cos(theta)))
   p+=out*bump;v.append(p)
 for it in range(NT-1):
  for ia in range(NA-1):i=it*NA+ia;f.append((i,i+1,i+1+NA,i+NA))
 o=B.mesh('Clean flowing rear hair',v,f,V.HAIR,1,'Head')
 sol=o.modifiers.new('Hair shell thickness','SOLIDIFY');sol.thickness=.004;sol.offset=-1
 uv=o.data.uv_layers.new(name='Rear flow UV')
 for p in o.data.polygons:
  for li in p.loop_indices:
   i=o.data.loops[li].vertex_index;uv.data[li].uv=((i%NA)/(NA-1),(i//NA)/(NT-1))
 o['construction']='Continuous radial quad shell with integrated strand relief; no intersecting rear lock objects.'
 return o
def main():
 backup=WORK/'kai_before_gap_fill_and_clean_rear.blend'
 if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));B.COL=bpy.data.collections['KAI | Editable character'];B.rig=bpy.data.objects['KAI_Rig'];V.HAIR=bpy.data.materials['Kai / Pearl hair with lavender shadows']
 targets={o.name for o in bpy.data.objects if o.name.startswith('KAI_Layer ')}
 edited_nape={o.name for o in bpy.data.objects if o.name.startswith('KAI_Nape feather ')}
 before={o.name:V.fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in targets|edited_nape}
 for name in targets:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 rear=make_rear();added=[rear.name]
 # Long separated sectors replace the former crossing rows. Their roots are buried
 # in the continuous backing; each visible lock stays within its own angular lane.
 for j in range(9):
  a=-.58+(pi+1.16)*(j+.5)/9;flow=.075*cos(a)
  def point(theta,angle,offset):
   return Vector(((.198*sin(theta)+offset)*cos(angle),.025+(.217*sin(theta)+offset)*sin(angle),.842+.215*cos(theta)))
  p=[point(.37,a,-.020),point(.98,a+flow*.3,.045),point(1.75,a+flow*.8,.040),point(2.20,a+flow,.025)]
  # Side locks finish slightly above the central shag to preserve the jaw outline.
  p[3].z+=.013*abs(cos(a))
  o,_=V.lock('Clean rear lock %02d'%j,p,.043,(cos(a),sin(a),0),.84);added.append(o.name)
 # Bring the existing nape roots onto the hair surface, closing the exposed scalp
 # strip below the rear locks while keeping their curled lower tips in place.
 for j in range(7):
  o=bpy.data.objects.get('KAI_Nape feather %02d'%j)
  if not o:continue
  a=.10+(pi-.20)*j/6;out=Vector((cos(a),sin(a),0))
  for vertex in o.data.vertices:
   t=max(0,min(1,(vertex.co.z-.64)/.08));vertex.co+=out*(.045*t*t*(3-2*t))
 for sg,side in [(1,'L'),(-1,'R')]:
  shapes=[
   ('Temple bridge '+side,[(sg*.133,-.035,.970),(sg*.173,-.072,.945),(sg*.178,-.075,.863),(sg*.148,-.112,.831)],.035,(sg*.65,-.75,0)),
   ('Behind ear sweep '+side,[(sg*.155,.030,.792),(sg*.206,.015,.758),(sg*.170,.009,.665),(sg*.108,-.030,.692)],.036,(sg*.8,-.3,0)),
   ('Jaw flick upper '+side,[(sg*.169,-.030,.747),(sg*.185,-.080,.716),(sg*.150,-.095,.676),(sg*.120,-.107,.705)],.021,(sg*.3,-1,0)),
   ('Jaw flick lower '+side,[(sg*.145,.006,.720),(sg*.165,-.046,.693),(sg*.151,-.065,.666),(sg*.116,-.074,.684)],.018,(sg*.3,-1,0)),
  ]
  for name,p,w,n in shapes:
   o,_=V.lock(name,p,w,n,.88);added.append(o.name)
 # A narrow center-part curl conceals the flat bridge between the large front locks.
 for name,p,w,n in [
  ('Center part curl',[(.006,-.084,1.025),(.035,-.144,.988),(.015,-.181,.946),(-.020,-.178,.955)],.023,(0,-1,0)),
  ('Small crown curl',[(0,.015,1.045),(-.038,-.006,1.101),(-.020,-.028,1.118),(.024,-.034,1.087)],.012,(0,-1,0)),
 ]:
  o,_=V.lock(name,p,w,n,.86);added.append(o.name)
 bpy.context.view_layer.update();assert before=={n:V.fingerprint(bpy.data.objects[n]) for n in before}
 scene=bpy.context.scene;scene['kai_hair_revision']='Marked temple/jaw/part gap fills; continuous rear hair relief replacing intersecting rows'
 report={'removed_intersecting_rear_lock_objects':len(targets),'new_hair_objects':added,'blended_nape_roots':len(edited_nape),'preserved_meshes':len(before),'rear_surface':'continuous radial quad shell with nine separated long locks','backup':str(backup)}
 (OUT/'hair_cleanup_validation.json').write_text(json.dumps(report,indent=2))
 cam=scene.camera;cam.location=(0,-3,.57);cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews/front.png');bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 for name,pos in [('front',(0,-3,.57)),('three_quarter',(1.8,-3,1.0)),('side',(3,0,.57)),('back',(0,3,.57))]:
  (WORK/'hair_cleanup_progress.txt').write_text('Rendering '+name);cam.location=pos;cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True)
 (WORK/'hair_cleanup_progress.txt').write_text('Completed clean rear and marked gap fills')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'hair_cleanup_error.txt').write_text(traceback.format_exc());raise
