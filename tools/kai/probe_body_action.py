import bpy,json
from pathlib import Path
W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16');R=Path(__file__).resolve().parents[2]
rows={}
for path in [R/'art/kai/kai.blend',W/'kai_game_export.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['KAI_Rig'];action=bpy.data.actions['Idle'];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for o in bpy.data.objects:
  if o.type=='MESH':
   for m in o.modifiers:m.show_viewport=False
 vals=[]
 for f in [0,5,10,15,20,30,45,60]:
  bpy.context.scene.frame_set(f);vals.append({'frame':f,'loc':list(rig.pose.bones['Body'].location),'head':list(rig.pose.bones['Body'].head)})
 rows[str(path)]={'samples':vals,'range':list(action.frame_range),'slots':[sl.identifier for sl in action.slots]}
(W/'body_action_probe.json').write_text(json.dumps(rows,indent=2))
