import bpy,bmesh,sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from helpers import load_checkpoint
from validation import evaluate
load_checkpoint(5); obj=bpy.data.objects['CHR_Body']
for m in obj.modifiers:
    if m.type=='SUBSURF': m.show_viewport=False
r=evaluate(obj,False)
bpy.context.view_layer.update(); ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
def info(p):
    labels=collections.Counter(obj.vertex_groups[g.group].name for i in p.vertices for g in me.vertices[i].groups)
    return {'face':p.index,'n':len(p.vertices),'co':list(p.center),'groups':labels.most_common(3),
            'vertices':[(i,list(me.vertices[i].co)) for i in p.vertices]}
print('INTERSECTIONS')
for a,b in r['self_intersections']: print(json.dumps([info(me.polygons[a]),info(me.polygons[b])]))
print('NONQUADS')
for p in me.polygons:
    if len(p.vertices)!=4: print(json.dumps(info(p)))
print('HALF_NONQUADS')
for p in obj.data.polygons:
    if len(p.vertices)!=4: print(p.index,list(p.vertices),[list(obj.data.vertices[i].co) for i in p.vertices])
