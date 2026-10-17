import bpy,json,shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_lashes_2026-10-16');WORK.mkdir(exist_ok=True)
backup=WORK/'kai_before_lash_fit.blend'
if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
bpy.ops.wm.open_mainfile(filepath=str(backup));body=bpy.data.objects['KAI_Base_Body'];bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());rows={}
for s in ['L','R']:
 for prefix,N in [('KAI_Relaxed upper eye contour ',10),('KAI_Base_LowerLashline.',4)]:
  o=bpy.data.objects[prefix+s];points=[]
  for i in range(len(o.data.vertices)//N):
   center=sum((o.matrix_world@v.co for v in list(o.data.vertices)[i*N:(i+1)*N]),Vector())/N
   hit,normal,idx,d=bvh.find_nearest(center);points.append({'point':list(center),'skin':list(hit),'normal':list(normal),'gap':d})
  rows[o.name]=points
rows['eye_rim_controls']={str(i):list(body.data.vertices[i].co) for i in range(944,1008)}
rows['body_modifiers']=[{'name':m.name,'type':m.type,'levels':getattr(m,'levels',None),'render_levels':getattr(m,'render_levels',None)} for m in body.modifiers]
(WORK/'probe.json').write_text(json.dumps(rows,indent=2))
