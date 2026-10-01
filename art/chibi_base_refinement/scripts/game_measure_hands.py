import bpy,sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_08_restored_design.blend'))
obj=bpy.data.objects['CHR_Body']; co=np.array([v.co[:] for v in obj.data.vertices]); edges=np.array([e.vertices[:] for e in obj.data.edges]); aa=co[edges[:,0]]; bb=co[edges[:,1]]
result={}
for x in [.30,.34,.36,.375,.39,.405,.42,.435,.45,.465]:
    dx=bb[:,0]-aa[:,0]; mask=((aa[:,0]-x)*(bb[:,0]-x)<=0)&(abs(dx)>1e-9)
    a,b,d=aa[mask],bb[mask],dx[mask]; hits=a+(b-a)*((x-a[:,0])/d)[:,None]; hits=hits[np.argsort(hits[:,1])]
    groups=[]
    for hit in hits:
        if not groups or hit[1]-groups[-1][-1][1]>.005: groups.append([])
        groups[-1].append(hit)
    result[x]=[{'min':np.min(g,axis=0).tolist(),'max':np.max(g,axis=0).tolist(),'center':((np.min(g,axis=0)+np.max(g,axis=0))/2).tolist()} for g in groups]
(PROJECT/'output'/'game_hand_sections.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
