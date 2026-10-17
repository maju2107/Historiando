import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));o=bpy.data.objects['KAI_Base_Body']
rows=[{'i':v.index,'co':list(v.co)} for v in o.data.vertices if abs(v.co.x)<.065 and .66<v.co.z<.74 and v.co.y<-.10]
(W/'face_probe.json').write_text(json.dumps(rows,indent=2))
