"""Make boot shafts follow shins; distribute elbow volume across the bend.

Updates current editable meshes and the already baked runtime skin, without
changing silhouettes, atlas UVs or the user's face/hair edits.
"""
import bpy,json,sys,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
sys.path.insert(0,str(R/'tools/kai'))
from rig_export import paint,smooth,assign,log

def repair(objects,rig):
 bones=set(rig.data.bones.keys());counts={'boot_shaft':0,'elbow_blend':0}
 for o in objects:
  if o.type!='MESH':continue
  for v in o.data.vertices:
   ws={o.vertex_groups[g.group].name:g.weight for g in v.groups if o.vertex_groups[g.group].name in bones and g.weight>.00001}
   pos=o.matrix_world@v.co;side='L' if pos.x>=0 else 'R';foot='Foot.'+side;shin='LowerLeg.'+side
   if ws.get(foot,0)>.999 and pos.z>.075:
    front=smooth((pos.y+.125)/.085);high=smooth((pos.z-.12)/.035)
    blend=smooth((pos.z-.075)/.07)*(front*(1-high)+high)
    if pos.z>=.155:blend=1.0
    if blend>.00001:
     paint(o,v.index,{foot:1-blend,shin:blend},bones);counts['boot_shaft']+=1
   upper='UpperArm.'+side;lower='LowerArm.'+side;helper='ElbowVolume.'+side
   if .155<abs(pos.x)<.225 and sum(ws.get(n,0) for n in [upper,lower,helper])>.99 and ws.get(helper,0)<.999:
    t=smooth((abs(pos.x)-.155)/.07)
    paint(o,v.index,{upper:(1-t)**2,lower:t*t,helper:2*t*(1-t)},bones);counts['elbow_blend']+=1
 return counts

def main():
 bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));rig=bpy.data.objects['KAI_Rig'];report={'source':repair(list(bpy.data.objects),rig)}
 assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/kai/kai.blend'))
 bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'));rig=bpy.data.objects['KAI_Rig'];report['runtime']=repair([bpy.data.objects['Kai_Skin']],rig)
 missing=[n for n in ['Talk','Explain','Correct','Shrug','Point','React'] if n not in bpy.data.actions]
 if missing:
  with bpy.data.libraries.load(str(R/'art/kai/kai.blend'),link=False) as (src,dst):dst.actions=missing
  for action in dst.actions:action.use_fake_user=True;assign(rig,action)
 assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/'kai_game_export.blend'))
 bpy.ops.export_scene.gltf(filepath=str(R/'assets/characters/kai/kai.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False)
 (R/'art/kai/joint_paint_validation.json').write_text(json.dumps(report,indent=2));log('Boot-shaft and elbow-volume weights exported')
if __name__=='__main__':
 try:main()
 except Exception:
  (W/'error.txt').write_text(traceback.format_exc());raise
