import bpy,json
from pathlib import Path
W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'))
report=[]
for a in bpy.data.actions:
 report.append({'name':a.name,'slots':[{'name':s.identifier,'users':[u.name for u in s.users()],'type':s.target_id_type} for s in a.slots],'fake':a.use_fake_user})
(W/'action_probe.json').write_text(json.dumps(report,indent=2))
(W/'blender_paths.txt').write_text(str(bpy.utils.script_paths()))
