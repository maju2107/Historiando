import bpy,sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_03c_proportion_fix.blend'))
for name in ('CHR_Head','CHR_Body','CHR_Neck','CHR_Eyelid.L'):
    me=bpy.data.objects[name].data; adj=[[] for v in me.vertices]
    for e in me.edges:
        a,b=e.vertices; adj[a].append(b); adj[b].append(a)
    color={0:0}; q=collections.deque([0]); errors=0
    while q:
        i=q.popleft()
        for j in adj[i]:
            if j not in color: color[j]=1-color[i]; q.append(j)
            elif color[j]==color[i]: errors+=1
    print(name,'BIPARTITE',errors,'VALENCES',[(c,dict(collections.Counter(len(adj[i]) for i in color if color[i]==c))) for c in (0,1)],flush=True)
    for c in (0,1):
        irregular=[i for i in color if color[i]==c and len(adj[i])!=4]
        print('IRREGULAR',c,[(i,tuple(round(x,4) for x in me.vertices[i].co),len(adj[i])) for i in irregular[:15]],flush=True)
