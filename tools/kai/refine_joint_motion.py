"""Fit inherited locomotion to Kai's high boots and anatomical elbow hinges."""
import bpy,sys,json,math,traceback
from pathlib import Path
from mathutils import Quaternion,Vector
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
sys.path.insert(0,str(R/'tools/kai'))
from rig_export import assign,log
NAMES=['Idle','Walk','Run','Jump','Fall','VictorySign','Talk','Explain','Correct','Shrug','Point','React']

def main():
 bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));rig=bpy.data.objects['KAI_Rig'];scene=bpy.context.scene;report={}
 flags=[(m,m.show_viewport) for o in bpy.data.objects if o.type=='MESH' for m in o.modifiers]
 for m,flag in flags:m.show_viewport=False
 for name in NAMES:
  action=bpy.data.actions[name];assign(rig,action);samples=[];before=[];after=[]
  for frame in range(int(action.frame_range[0]),int(action.frame_range[1])+1):
   scene.frame_set(frame);row={}
   for side in ['L','R']:
    foot=rig.pose.bones['Foot.'+side];e=foot.rotation_quaternion.to_euler('XYZ');before.append(list(e))
    e.x=max(-.35,min(.38,e.x));e.y=max(-.09,min(.09,e.y));e.z=max(-.09,min(.09,e.z));row[foot.name]=e.to_quaternion();after.append(list(e))
    lower=rig.pose.bones['LowerArm.'+side];el=lower.rotation_quaternion.to_euler('XYZ');row[lower.name]=Quaternion((1,0,0),max(.02,min(2.05,el.x)))
   samples.append((frame,row))
  for frame,row in samples:
   for n,q in row.items():
    rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert(data_path='rotation_quaternion',frame=frame,group=n)
  report[name]={'ankle_x_before_degrees':[round(math.degrees(min(e[0] for e in before)),2),round(math.degrees(max(e[0] for e in before)),2)],'ankle_x_after_degrees':[round(math.degrees(min(e[0] for e in after)),2),round(math.degrees(max(e[0] for e in after)),2)],'elbow_hinge_limit_degrees':[1.15,117.46]}
 assign(rig,bpy.data.actions['Idle']);scene.frame_set(0)
 for m,flag in flags:m.show_viewport=flag
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/kai/kai.blend'))
 bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'));rig=bpy.data.objects['KAI_Rig'];rig.animation_data_clear()
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(R/'art/kai/kai.blend'),link=False) as (src,dst):dst.actions=NAMES.copy()
 for a in dst.actions:a.use_fake_user=True;assign(rig,a)
 assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/'kai_game_export.blend'))
 bpy.ops.export_scene.gltf(filepath=str(R/'assets/characters/kai/kai.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False)
 (R/'art/kai/joint_motion_validation.json').write_text(json.dumps(report,indent=2));log('High-boot ankle limits and hinge elbows exported')
if __name__=='__main__':
 try:main()
 except Exception:
  (W/'error.txt').write_text(traceback.format_exc());raise
