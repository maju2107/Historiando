import bpy,bmesh,sys,json
import numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import *
from helpers import *
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_02_reference_setup.blend'))
report={}
for obj in meshes():
    co=np.array([v.co[:] for v in obj.data.vertices]); report[obj.name]={'bbox':bounds([obj])}
    if obj.name in ('CHR_Body','CHR_Head'):
        samples=[]
        for z in np.arange(.01,1,.02):
            vs=co[np.abs(co[:,2]-z)<.004]
            if len(vs): samples.append({'z':round(float(z),3),'min':vs.min(axis=0).tolist(),'max':vs.max(axis=0).tolist()})
        report[obj.name]['sections']=samples
    before=len(obj.data.vertices)
    for iterations in (2,4,6):
        bm=bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.unsubdivide(bm,verts=list(bm.verts),iterations=iterations)
        print('UNSUBDIV',obj.name,iterations,'verts',len(bm.verts),'faces',len(bm.faces),'quads',sum(len(f.verts)==4 for f in bm.faces),'boundary',sum(e.is_boundary for e in bm.edges),flush=True)
        bm.free()
(PROJECT/'output'/'shape_analysis.json').write_text(json.dumps(report,indent=2))
print(json.dumps({name:r['bbox'] for name,r in report.items()},indent=2),flush=True)
