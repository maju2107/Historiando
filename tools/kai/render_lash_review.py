import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_leg_lash_2026-10-16/review');WORK.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(WORK.parent/'kai_before_leg_lash.blend' if '--before' in sys.argv else OUT/'kai.blend'));s=bpy.context.scene
name=sys.argv[sys.argv.index('--')+1]
views={'face':((0,-3,.88),.63,(0,-.02,.86)),'eye_front':((0,-3,.795),.27,(0,-.11,.785)),'eye_left':((3,-1.8,.795),.24,(.075,-.11,.785)),'eye_right':((-3,-1.8,.795),.24,(-.075,-.11,.785)),'eye_profile_left':((3,-.38,.795),.19,(.075,-.11,.785)),'eye_profile_right':((-3,-.38,.795),.19,(-.075,-.11,.785)),'knees_side':((3,-.8,.225),.23,(.075,0,.215)),'knees_front':((0,-3,.22),.30,(0,0,.205))}
if name.startswith('eye_'):
 for o in bpy.data.objects:
  if o.type=='MESH' and any('hair' in m.name.lower() for m in o.data.materials):o.hide_render=True
pos,scale,target=views[name];c=s.camera;c.location=pos;c.data.ortho_scale=scale;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=1000;s.render.resolution_y=900 if name.startswith('eye_') else 1100;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=4;s.cycles.samples=24;s.render.filepath=str(WORK/f'{name}{"_before" if "--before" in sys.argv else ""}.png')
bpy.ops.render.render(write_still=True)
if name=='eye_front':
 body=bpy.data.objects['KAI_Base_Body'];tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());rows=[]
 for o in bpy.data.objects:
  if not(o.name.startswith('KAI_Relaxed upper eye contour ') or o.name.startswith('KAI_Base_LowerLashline.') or o.name.startswith('KAI_Connected cartoon lashes ')):continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();points=[v.co.copy() for v in m.vertices];centers=[p.center.copy() for p in m.polygons]
  gaps=[tree.find_nearest(p)[3] for p in points];facegaps=[tree.find_nearest(p)[3] for p in centers]
  rows.append({'object':o.name,'max_vertex_distance_m':max(gaps),'max_face_center_distance_m':max(facegaps),'evaluated_vertices':len(points)})
  ev.to_mesh_clear()
 path=OUT/('leg_lash_validation.json' if any(o.name.startswith('KAI_Connected cartoon lashes ') for o in bpy.data.objects) else 'lash_fit_validation.json')
 report=json.loads(path.read_text());report['attachment_check']=rows;report['attachment_passed']=bool(rows) and all(r['max_vertex_distance_m']<.001 and r['max_face_center_distance_m']<.001 for r in rows);path.write_text(json.dumps(report,indent=2))
 assert report['attachment_passed'],rows
