"""Read-only trials of subdivision-cage recovery; saves statistics, not meshes."""
import bpy,bmesh,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_03c_proportion_fix.blend'))
results={}
for obj in bpy.data.collections['CHARACTER'].objects:
    if obj.type!='MESH': continue
    trials=[]
    for iterations in (0,2,4,6):
        bm=bmesh.new(); bm.from_mesh(obj.data)
        if iterations: bmesh.ops.unsubdivide(bm,verts=list(bm.verts),iterations=iterations)
        counts={}
        for f in bm.faces: counts[len(f.verts)]=counts.get(len(f.verts),0)+1
        trials.append({'iterations':iterations,'verts':len(bm.verts),'faces':len(bm.faces),'face_sizes':counts,'nonmanifold':sum(not e.is_manifold for e in bm.edges)})
        bm.free()
    results[obj.name]=trials
(PROJECT/'output'/'game_topology_trials.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results),flush=True)
