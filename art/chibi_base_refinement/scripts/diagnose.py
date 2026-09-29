import bpy,sys,json,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from validation import mesh_report
from mathutils.bvhtree import BVHTree
for checkpoint in ('character_02_reference_setup.blend','character_06b_hands_feet.blend'):
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/checkpoint))
    for name in ('CHR_Head','CHR_Neck','CHR_Body'):
        obj=bpy.data.objects[name]
        for m in obj.modifiers:
            if m.type=='MIRROR': m.bisect_threshold=1e-7; m.merge_threshold=1e-7
            if m.type=='SUBSURF': m.show_viewport=False
        bpy.context.view_layer.update(); ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
        r=mesh_report(me,True,True); print(checkpoint,name,'errors',{k:r[k] for k in ('nonmanifold_edges','self_intersection_count','max_symmetry_error')},flush=True)
        bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        cross=r['self_intersections']; print('COORDS',[[list(bm.faces[a].calc_center_median()),list(bm.faces[b].calc_center_median())] for a,b in cross[:12]],flush=True)
        bm.free(); ev.to_mesh_clear()
