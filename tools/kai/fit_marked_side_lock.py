"""Lift and broaden the root of the marked existing side lock to close its crown join."""
import bpy,json,shutil,traceback,importlib.util,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_face_2026-10-16')
spec=importlib.util.spec_from_file_location('volume',ROOT/'tools/kai/refine_hair_volume.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def main():
 backup=WORK/'kai_before_marked_side_lock_fit.blend'
 if not backup.exists():
  shutil.copy2(OUT/'kai.blend',backup)
  dest=WORK/'side_lock_before';dest.mkdir(exist_ok=True)
  for f in (OUT/'previews').glob('*.png'):shutil.copy2(f,dest/f.name)
 bpy.ops.wm.open_mainfile(filepath=str(backup));name='KAI_Flowing fringe 06';o=bpy.data.objects[name]
 before={p.name:V.fingerprint(p) for p in bpy.data.objects if p.type=='MESH' and p.name!=name}
 N=24;R=36;assert len(o.data.vertices)==N*R
 original=[v.co.copy() for v in o.data.vertices]
 for i in range(R):
  t=i/(R-1);influence=1-smooth(t/.60);width=1+.50*(1-smooth(t/.35))
  if influence==0 and width==1:continue
  center=sum((original[i*N+j] for j in range(N)),Vector())/N
  for j in range(N):
   v=o.data.vertices[i*N+j];v.co=center+(original[i*N+j]-center)*width+Vector((-.008*influence,-.008*influence,.050*influence))
 o.data.update();o['side_lock_fit']='Root lifted and broadened into the crown; lower curled end preserved.'
 bpy.context.view_layer.update();assert before=={n:V.fingerprint(bpy.data.objects[n]) for n in before}
 unchanged_tail=all(v.co==original[v.index] for v in o.data.vertices if v.index//N>=22)
 assert unchanged_tail,'Lower curl moved'
 (OUT/'side_lock_validation.json').write_text(json.dumps({'modified_object':name,'preserved_other_meshes':len(before),'lower_curl_unchanged':unchanged_tail,'root_lift':.050,'root_width_factor':1.50,'backup':str(backup)},indent=2))
 scene=bpy.context.scene;scene['kai_side_lock_revision']='Marked side-lock root fitted into crown to cover the visible join gap'
 cam=scene.camera;cam.data.ortho_scale=1.27;cam.location=(0,-3,.57);cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews/front.png');bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 if '--model-only' in sys.argv:
  (WORK/'side_lock_progress.txt').write_text('Saved fitted side lock; render separately')
  return
 for name,pos,scale,target in [('front',(0,-3,.57),1.27,(0,0,.55)),('three_quarter',(1.8,-3,1.0),1.27,(0,0,.55)),('side',(3,0,.57),1.27,(0,0,.55)),('back',(0,3,.57),1.27,(0,0,.55)),('face',(0,-3,.87),.54,(0,-.02,.84))]:
  (WORK/'side_lock_progress.txt').write_text('Rendering '+name);cam.data.ortho_scale=scale;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True)
 (WORK/'side_lock_progress.txt').write_text('Completed marked side-lock fit')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'side_lock_error.txt').write_text(traceback.format_exc());raise
