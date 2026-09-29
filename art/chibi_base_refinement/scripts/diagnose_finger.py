import bpy,sys,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from finalize import local_repairs
from validation import mesh_report
from topology import hand_overview
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_06b_hands_feet.blend')); local_repairs()
obj=bpy.data.objects['CHR_Body']
for m in obj.modifiers:
    if m.type=='SUBSURF': m.show_viewport=False
bpy.context.view_layer.update(); ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
r=mesh_report(me,True,True); bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
for a,b in r['self_intersections']:
    print(a,b,list(bm.faces[a].calc_center_median()),list(bm.faces[b].calc_center_median()),flush=True)
bm.free(); ev.to_mesh_clear()
hand_overview(PROJECT/'renders'/'finger_diagnosis.png')
