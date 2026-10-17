import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));rig=bpy.data.objects['KAI_Rig']
rows={}
for n in ['UpperArm.R','LowerArm.R','Hand.R','Index.1.R','Thumb.1.R']:
 b=rig.pose.bones[n];rows[n]={'rest':list(map(list,b.bone.matrix_local)),'pose':list(map(list,b.matrix)),'q':list(b.rotation_quaternion),'head':list(b.head),'tail':list(b.tail)}
(W/'pose_probe.json').write_text(json.dumps(rows,indent=2))
