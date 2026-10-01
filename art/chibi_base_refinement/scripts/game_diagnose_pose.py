import bpy,sys,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from game_pose_validation import set_pose
from validation import mesh_report
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_10_skeleton_skinning.blend'))
rig=bpy.data.objects['RIG_Chibi']; body=bpy.data.objects['CHR_Body']
for m in body.modifiers:
    if m.type=='SUBSURF':m.show_viewport=False
for frame in (20,40,80):
    set_pose(rig,frame); ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh(); r=mesh_report(me,False,True)
    print('FRAME',frame,'CROSSES SOURCE COORDINATES',flush=True)
    ids=set(a for a,b in r['self_intersections'])|set(b for a,b in r['self_intersections'])
    print([tuple(round(x,4) for x in sum((body.data.vertices[i].co for i in me.polygons[p].vertices),Vector())/len(me.polygons[p].vertices)) for p in sorted(ids)][:90],flush=True)
    ratios=[]
    for e in me.edges:
        a,b=e.vertices; length=(body.data.vertices[a].co-body.data.vertices[b].co).length
        if length>1e-5: ratios.append(((me.vertices[a].co-me.vertices[b].co).length/length,a,b))
    print('WORST',[(round(r,3),tuple(body.data.vertices[a].co),tuple(body.data.vertices[b].co),[(body.vertex_groups[g.group].name,round(g.weight,3)) for g in body.data.vertices[a].groups],[(body.vertex_groups[g.group].name,round(g.weight,3)) for g in body.data.vertices[b].groups]) for r,a,b in sorted(ratios,reverse=True)[:5]],flush=True)
    ev.to_mesh_clear()
