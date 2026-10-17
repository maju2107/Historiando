"""Apply engine-measured sole contact correction to source and exported clips."""
import bpy,json,sys,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
sys.path.insert(0,str(R/'tools/kai'))
from rig_export import assign,log
NAMES=['Idle','Walk','Run','Jump','Fall','VictorySign','Talk','Explain','Correct','Shrug','Point','React']

def main():
 data=json.loads((W/'floor_probe.json').read_text())
 # Body's local Y is vertical; local Z points backward in this adapted rig.
 # Restore the original locomotion/gesture translations before applying height.
 bpy.ops.wm.open_mainfile(filepath=str(W/'runtime_uv.blend'));rig=bpy.data.objects['KAI_Rig'];original={}
 for o in bpy.data.objects:
  if o.type=='MESH':
   for m in o.modifiers:m.show_viewport=False
 for name in data:
  action=bpy.data.actions[name];assign(rig,action);original[name]={}
  for frame in range(int(action.frame_range[0]),int(action.frame_range[1])+1):
   bpy.context.scene.frame_set(frame);original[name][frame]=rig.pose.bones['Body'].location.copy()
 bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));rig=bpy.data.objects['KAI_Rig'];scene=bpy.context.scene
 flags=[(m,m.show_viewport) for o in bpy.data.objects if o.type=='MESH' for m in o.modifiers]
 for m,flag in flags:m.show_viewport=False
 report={}
 for name,samples in data.items():
  action=bpy.data.actions[name];assign(rig,action);start=action.frame_range[0];updates=[]
  for row in samples:
   f=start+row['time']*30;key=max(min(original[name]),min(max(original[name]),round(f)));loc=original[name][key].copy();loc.y+=row['delta_native'];updates.append((f,loc))
  for f,loc in updates:
   rig.pose.bones['Body'].location=loc;rig.pose.bones['Body'].keyframe_insert(data_path='location',frame=f,group='Body')
  report[name]={'frames':len(updates),'height_axis':'Body local Y = world Z','original_forward_motion_restored':True,'maximum_correction_m':max(abs(r['delta_native']) for r in samples)}
 assign(rig,bpy.data.actions['Idle']);scene.frame_set(0)
 for m,flag in flags:m.show_viewport=flag
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/kai/kai.blend'))
 bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'));rig=bpy.data.objects['KAI_Rig'];rig.animation_data_clear()
 for action in list(bpy.data.actions):bpy.data.actions.remove(action)
 with bpy.data.libraries.load(str(R/'art/kai/kai.blend'),link=False) as (src,dst):dst.actions=NAMES.copy()
 for action in dst.actions:action.use_fake_user=True;assign(rig,action)
 assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/'kai_game_export.blend'))
 bpy.ops.export_scene.gltf(filepath=str(R/'assets/characters/kai/kai.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False,export_morph=True)
 (R/'art/kai/ground_contact_validation.json').write_text(json.dumps(report,indent=2));log('Engine-measured foot support applied to source and GLB')
if __name__=='__main__':
 try:main()
 except Exception:
  (W/'error.txt').write_text(traceback.format_exc());raise
