import bpy,sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_06b_hands_feet.blend'))
o=bpy.data.objects['CHR_Body']; gid=o.vertex_groups['Added fourth finger.L'].index
vs=[v for v in o.data.vertices if any(g.group==gid for g in v.groups)]; vi={v.index for v in vs}
adj={v.index:[] for v in o.data.vertices}
for e in o.data.edges:
    a,b=e.vertices; adj[a].append(b); adj[b].append(a)
for k,v in enumerate(vs[:12]):
    root=[i for i in adj[v.index] if i not in vi]
    print(k,v.index,list(v.co),'roots',[(i,list(o.data.vertices[i].co)) for i in root])
