import bpy,json,shutil,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai'
WORK=Path('C:/Users/obran/Historiando_Backups/kai_finish_2026-10-16');WORK.mkdir(exist_ok=True)
b=WORK/'kai_before_finish.blend'
if not b.exists():shutil.copy2(OUT/'kai.blend',b)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'kai.blend'))
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 cs=[o.matrix_world@v.co for v in o.data.vertices]
 rows.append({'name':o.name,'vertices':len(cs),'bounds':[[min(v[a] for v in cs),max(v[a] for v in cs)] for a in range(3)],'location':list(o.location),'scale':list(o.scale),'modifiers':[(m.name,m.type) for m in o.modifiers],'materials':[m.name for m in o.data.materials]})
(WORK/'objects.json').write_text(json.dumps(rows,indent=2))
details={}
for name in ['KAI_Cargo shorts / continuous pelvis','KAI_Base_LowerLashline.L','KAI_Small crown curl']:
 o=bpy.data.objects[name]
 details[name]={'verts':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]}
(WORK/'mesh_details.json').write_text(json.dumps(details))
views={'face':((0,-3,.86),.55,(0,0,.84)),'lower':((1.5,-3,.65),.62,(0,0,.26)),'side':((3,0,.30),.62,(0,0,.26))}
if '--' in sys.argv:
 name=sys.argv[sys.argv.index('--')+1];pos,scale,target=views[name];s=bpy.context.scene;c=s.camera
 c.location=pos;c.data.ortho_scale=scale;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
 s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=4;s.cycles.samples=24
 s.render.filepath=str(WORK/f'before_{name}.png');bpy.ops.render.render(write_still=True)
