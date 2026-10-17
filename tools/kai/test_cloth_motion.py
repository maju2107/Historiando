"""Settle the shirt into its neutral drape and test live cloth with torso motion."""
import bpy,json,math,traceback,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai'
WORK=Path('C:/Users/obran/Historiando_Backups/kai_cloth_2026-10-16')
def log(s):
 (WORK/'simulation_progress.txt').write_text(s);print(s,flush=True)
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[x.co.copy() for x in m.vertices];ev.to_mesh_clear();return v
def main():
 bpy.ops.wm.open_mainfile(filepath=str(OUT/'kai.blend'));s=bpy.context.scene;o=bpy.data.objects['KAI_Sleeveless tank'];c=next(m for m in o.modifiers if m.type=='CLOTH')
 post=[m for m in o.modifiers if m.type in {'SUBSURF','SOLIDIFY'}]
 for m in post:m.show_viewport=False
 initial=[v.co.copy() for v in o.data.vertices]
 if '--settle' in sys.argv:
  for fr in range(1,33):
   s.frame_set(fr);vv=coords(o)
   if fr%4==0:log('Settling frame '+str(fr))
  distance=[(a-b).length for a,b in zip(vv,initial)]
  assert len(vv)==len(initial) and all(math.isfinite(x) for v in vv for x in v)
  assert max(distance)<.09,('Unstable cloth',max(distance))
  # Torso bones have identity poses, so settled coordinates are also rest space.
  for bn in ['Spine','Chest']:assert bpy.data.objects['KAI_Rig'].pose.bones[bn].matrix_basis.is_identity
  o.modifiers.remove(c)
  for v,co in zip(o.data.vertices,vv):v.co=co
  o.data.update();c=o.modifiers.new('Soft cotton cloth physics','CLOTH')
  bpy.context.view_layer.objects.active=o
  while o.modifiers.find(c.name)>1:bpy.ops.object.modifier_move_up(modifier=c.name)
  cs=c.settings;cs.quality=8;cs.mass=.22;cs.air_damping=3;cs.tension_stiffness=35;cs.compression_stiffness=25;cs.shear_stiffness=8;cs.bending_stiffness=.25;cs.bending_damping=2
  cs.tension_damping=8;cs.compression_damping=8;cs.shear_damping=6;cs.vertex_group_mass='Cloth anchors';cs.pin_stiffness=1;cs.use_dynamic_mesh=True
  cc=c.collision_settings;cc.use_collision=True;cc.distance_min=.0015;cc.collision_quality=4;cc.friction=5;cc.use_self_collision=True;cc.self_distance_min=.0015;cc.self_friction=3;c.point_cache.frame_start=1;c.point_cache.frame_end=72
  for m in post:m.show_viewport=True
  s.frame_set(1)
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
  r=json.loads((OUT/'cloth_validation.json').read_text());r['neutral_settle']={'frames':32,'max_displacement_m':max(distance),'mean_displacement_m':sum(distance)/len(distance),'saved_rest_drape':True};(OUT/'cloth_validation.json').write_text(json.dumps(r,indent=2))
  log('Saved settled neutral drape');return
 # Motion is only assigned in this QA process; native source stays in neutral pose.
 rig=bpy.data.objects['KAI_Rig'];s.render.fps=24
 bones=['Spine','Chest','UpperArm.L','UpperArm.R'];base={n:rig.pose.bones[n].matrix_basis.copy() for n in bones}
 from mathutils import Matrix
 for fr,a in [(1,0),(16,0),(28,.13),(40,-.13),(56,.07),(72,0)]:
  for name in bones:
   pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION'
   angle=a*(.6 if name=='Spine' else .5 if name=='Chest' else 1 if name.endswith('L') else -1)
   pb.matrix_basis=base[name]@Matrix.Rotation(angle,4,'Y' if 'Arm' not in name else 'X')
   pb.keyframe_insert(data_path='rotation_quaternion',frame=fr,group=name)
 samples={};render_dir=WORK/'motion';render_dir.mkdir(exist_ok=True)
 cam=s.camera;cam.location=(1.5,-3,.83);cam.data.ortho_scale=.68;cam.rotation_euler=(Vector((0,0,.49))-cam.location).to_track_quat('-Z','Y').to_euler()
 s.render.resolution_x=560;s.render.resolution_y=560;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=4;s.cycles.samples=16
 for fr in range(1,73):
  s.frame_set(fr);vv=coords(o)
  assert all(math.isfinite(x) for v in vv for x in v)
  if fr%6==0:log('Testing cloth motion frame '+str(fr))
  if fr in [16,28,40,56,72]:
   c.show_viewport=False;bpy.context.view_layer.update();skinned=coords(o);c.show_viewport=True;bpy.context.view_layer.update()
   delta=[(a-b).length for a,b in zip(vv,skinned)]
   samples[str(fr)]={'max_vs_skinning_m':max(delta),'mean_vs_skinning_m':sum(delta)/len(delta)}
   # Reenable final surface modifiers for preview, leaving sim vertex count intact.
   for m in post:m.show_render=True
   s.render.filepath=str(render_dir/f'{fr:03}.png');bpy.ops.render.render(write_still=True)
 assert max(v['max_vs_skinning_m'] for v in samples.values())>.001,'No visible cloth displacement'
 assert max(v['max_vs_skinning_m'] for v in samples.values())<.10,'Cloth is unstable'
 r=json.loads((OUT/'cloth_validation.json').read_text());r['simulation_test']={'passed':True,'frames':72,'fps':24,'motion':'Torso lean and opposing upper-arm swing; QA-only animation','samples':samples,'all_positions_finite':True};(OUT/'cloth_validation.json').write_text(json.dumps(r,indent=2))
 log('Motion test passed; source remains in neutral pose')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'simulation_error.txt').write_text(traceback.format_exc());raise
