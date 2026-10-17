import bpy,json
from pathlib import Path
W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16');R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(W/'runtime_uv.blend'));skin=bpy.data.objects['Kai_Skin'];parts={}
for p in skin.data.polygons:
 n=skin.data.materials[p.material_index].name
 if any(x in n for x in ['High top boot L','Tall triangular bow L','Cross lace L','Finished boot cuff L']):parts.setdefault(n,set()).update(p.vertices)
bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'));skin=bpy.data.objects['Kai_Skin'];rows={}
for name,indices in parts.items():
 rows[name]=[{'co':list(skin.data.vertices[i].co),'weights':{skin.vertex_groups[g.group].name:g.weight for g in skin.data.vertices[i].groups if g.weight>.01}} for i in list(indices)[::max(1,len(indices)//6)]]
(W/'boot_weight_probe.json').write_text(json.dumps({'matrix':list(map(list,skin.matrix_world)),'parts':rows},indent=2))
