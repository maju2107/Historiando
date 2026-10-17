import bpy,json,shutil
from pathlib import Path
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_leg_lash_2026-10-16');WORK.mkdir(exist_ok=True)
backup=WORK/'kai_before_leg_lash.blend'
if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
bpy.ops.wm.open_mainfile(filepath=str(backup));o=bpy.data.objects['KAI_Base_Body']
(WORK/'leg_probe.json').write_text(json.dumps([{'i':v.index,'co':list(v.co)} for v in o.data.vertices if .14<v.co.z<.29],indent=2))
