"""Edit current Kai: lower fringe, continuous upper lids, clean tapered eyebrow arcs."""
import bpy,math,json,shutil,traceback,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import sin,cos,pi
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_face_2026-10-16')
spec=importlib.util.spec_from_file_location('volume',ROOT/'tools/kai/refine_hair_volume.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);B=V.B
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def main():
 WORK.mkdir(parents=True,exist_ok=True);backup=WORK/'kai_before_forehead_lids_brows.blend'
 if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));B.COL=bpy.data.collections['KAI | Editable character'];B.rig=bpy.data.objects['KAI_Rig']
 hairshift={'KAI_Flowing fringe 02':.024,'KAI_Fine fringe left':.024,'KAI_Flowing fringe 04':.028,'KAI_Fine fringe right':.028,'KAI_Center part curl':.034,'KAI_Part wisp':.034}
 face_names={'KAI_Base_Eyebrow.'+s for s in ('L','R')}|{'KAI_Relaxed upper lid '+s for s in ('L','R')}|{'KAI_Relaxed upper eye contour '+s for s in ('L','R')}
 targets=set(hairshift)|{'KAI_Outer brow curl R','KAI_Base_Body'}|face_names
 before={o.name:V.fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in targets}
 for name,delta in hairshift.items():
  for v in bpy.data.objects[name].data.vertices:v.co.z-=delta
 for v in bpy.data.objects['KAI_Outer brow curl R'].data.vertices:v.co.z-=.003+.025*smooth((v.co.z-.820)/.065)
 skin=bpy.data.materials['Kai / Warm brown skin'];dark=bpy.data.materials['Kai / Warm dark contours']
 body=bpy.data.objects['KAI_Base_Body'];body_original=[v.co.copy() for v in body.data.vertices];body_changed=set();bodyTree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
 for name in face_names:
  if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 def body_y(x,z):
  p=bodyTree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))[0]
  return p.y if p is not None and p.y<-.060 else None
 records=[]
 for sg,side in [(1,'L'),(-1,'R')]:
  cx=sg*.079;eyeTree=BVHTree.FromObject(bpy.data.objects['KAI_Base_Eye.'+side],bpy.context.evaluated_depsgraph_get())
  # Fit only intact forehead skin, excluding the eye opening and rear-wall hits.
  rows=[];values=[]
  def basis(x,z):
   u=(x-cx)/.057;w=(z-.845)/.05
   return [u**i*w**j for i in range(5) for j in range(3)]
  for u in np.linspace(-1,1,41):
   for z in np.linspace(.828,.884,9):
    x=cx+.057*u;y=body_y(x,z)
    if y is not None:rows.append(basis(x,z));values.append(y)
  coeff=np.linalg.lstsq(np.array(rows),np.array(values),rcond=None)[0]
  def baseline(x,z):return float(np.dot(basis(x,z),coeff))
  def lowz(u):return .797+.003*u*sg+.0035*(1-u*u)
  if sg==1:
   # The original face already contains concentric eye-socket loops. Reposition
   # the upper loops in that existing topology instead of laying a skin patch over it.
   for offset in range(7):
    outer=body.data.vertices[945+offset];middle=body.data.vertices[961+offset];lip=body.data.vertices[977+offset];inner=body.data.vertices[993+offset]
    assert .025<lip.co.x<.14 and .78<lip.co.z<.83
    u=max(-1,min(1,(lip.co.x-.079)/.047));lip.co.z=.797+.003*u+.0035*(1-u*u)
    lip.co.y=baseline(lip.co.x,lip.co.z)-.001
    middle.co.z=.50*(outer.co.z+lip.co.z);middle.co.y=baseline(middle.co.x,middle.co.z)-.0005
    inner.co.z=lip.co.z-.0020;inner.co.y=lip.co.y+.0040
    body_changed.update([middle.index,lip.index,inner.index])
   # The outer sclera bulges forward more than the forehead surface. Give the
   # outer socket enough clearance to keep that white wedge under the upper lid.
   for idx in list(range(945,952))+list(range(961,968))+list(range(977,984))+list(range(993,1000))+[944,960,976,992]:
    v=body.data.vertices[idx];amount=.008*smooth((v.co.x-.102)/.030)
    if amount>0:v.co.y-=amount;body_changed.add(idx)
   body.data.update();bpy.context.view_layer.update();bodyTree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
  # Thin, smoothly arched contour with tapered ends.
  pts=[]
  for u in np.linspace(-.84,.93,42):
   x=cx+.047*u;z=lowz(u)+.001;pts.append(Vector((x,baseline(x,z)-.0018,z)))
  contour=B.tube('Relaxed upper eye contour '+side,pts,.0014,dark,'Head',taper=True,normal=(0,-1,0),sub=2);contour.modifiers[0].levels=1
  bpy.context.view_layer.update()
  # A rounded but restrained eyebrow, thick at the inner portion and tapered at the tail.
  points=B.bez([(sg*.039,0,.846),(sg*.060,0,.857),(sg*.098,0,.858),(sg*.125,0,.843)],36)
  bv=[];bf=[];N=10
  for i,p in enumerate(points):
   t=i/(len(points)-1);x,z=p.x,p.z;by=body_y(x,z);y=by if by is not None else baseline(x,z)
   center=Vector((x,y-.0016,z));tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();sidevec=tangent.cross(Vector((0,-1,0))).normalized()
   w=.0060*(.70+.40*sin(pi*t))*max(.001,1-t)**.35
   for j in range(N):
    a=j*2*pi/N;bv.append(center+sidevec*(w*cos(a))+Vector((0,-.0015*sin(a)*min(1,w/.004),0)))
  for i in range(len(points)-1):
   for j in range(N):k=i*N+j;nxt=i*N+(j+1)%N;bf.append((k,nxt,nxt+N,k+N))
  bf.extend([tuple(range(N-1,-1,-1)),tuple((len(points)-1)*N+j for j in range(N))])
  brow=B.mesh('Base_Eyebrow.'+side,bv,bf,dark,2,'Head');brow.modifiers[0].levels=1
  records.append({'side':side,'skin_fit_samples':len(rows),'max_forehead_fit_error':float(max(abs(np.array(rows)@coeff-np.array(values))))})
 bpy.context.view_layer.update();assert before=={name:V.fingerprint(bpy.data.objects[name]) for name in before}
 assert all(v.co==body_original[v.index] for v in body.data.vertices if v.index not in body_changed),'Other body vertices changed'
 scene=bpy.context.scene;scene['kai_face_revision']='Lower central fringe, fitted smooth upper eyelids and tapered eyebrow arcs'
 report={'hair_lowering':hairshift,'upper_lids':'Integrated into existing face topology; separate patches removed','body_upper_eye_control_vertices_changed':sorted(body_changed),'all_other_body_vertices_unchanged':True,'rebuilt_face_objects':[n for n in sorted(face_names) if ' upper lid ' not in n],'unchanged_other_meshes':len(before),'fit':records,'backup':str(backup)}
 (OUT/'face_refinement_validation.json').write_text(json.dumps(report,indent=2))
 cam=scene.camera;cam.location=(0,-3,.57);cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews/front.png');bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 for name,pos,scale,target in [('front',(0,-3,.57),1.27,(0,0,.55)),('three_quarter',(1.8,-3,1.0),1.27,(0,0,.55)),('side',(3,0,.57),1.27,(0,0,.55)),('back',(0,3,.57),1.27,(0,0,.55)),('face',(0,-3,.87),.54,(0,-.02,.84))]:
  (WORK/'progress.txt').write_text('Rendering '+name);cam.data.ortho_scale=scale;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True)
 (WORK/'progress.txt').write_text('Completed forehead, upper eyelids and brows')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'error.txt').write_text(traceback.format_exc());raise
