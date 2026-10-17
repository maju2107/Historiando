"""Reopen Kai and record structural checks; does not modify the source .blend."""
import bpy,json,math,hashlib
from pathlib import Path
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'kai.blend'))
rig=bpy.data.objects['KAI_Rig'];bones=set(b.name for b in rig.data.bones)
rows=[];fail=[];triangles=0
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bonegroups={g.index for g in o.vertex_groups if g.name in bones}
 missing=0;nonunit=0
 for v in o.data.vertices:
  total=sum(g.weight for g in v.groups if g.group in bonegroups)
  if total<.001:missing+=1
  elif abs(total-1)>.015:nonunit+=1
  if not all(math.isfinite(c) for c in v.co):fail.append(o.name+' nonfinite vertex')
 if missing:fail.append(o.name+' unweighted vertices: '+str(missing))
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();tris=len(m.loop_triangles);triangles+=tris;ev.to_mesh_clear()
 rows.append(dict(name=o.name,control_vertices=len(o.data.vertices),evaluated_viewport_triangles=tris,unweighted_vertices=missing,nonunit_weights=nonunit,materials=[m.name for m in o.data.materials]))
face_report=json.loads((ROOT/'art/island_intro/facial_source_validation.json').read_text())
# Yara's face was subsequently edited at the user's request. Verify the scoped
# native comparison and its exact exported artifacts, rather than the old
# pre-expression whole-file hashes.
assert not face_report['issues']
assert face_report['Yara']['outside_face_changes']==0
expected={'art/yara/yara.blend':face_report['Yara']['native_sha256'],'assets/characters/yara/yara_playable.glb':face_report['Yara']['runtime_sha256']}
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in expected}
report={'source_reopened':True,'armature_bones':len(bones),'mesh_objects':len(rows),'evaluated_viewport_triangles':triangles,'structural_errors':fail,'protected_yara_unchanged':{p:hashes[p]==h for p,h in expected.items()},'protected_hashes':hashes,'meshes':rows,'source_actions':[a.name for a in bpy.data.actions if a.get('kai_clip')],'facial_shapes':[k.name for k in bpy.data.objects['KAI_Base_Body'].data.shape_keys.key_blocks],'review_views':['front','three_quarter','side','back'],'scope':'Editable rig, normalized clothing/joint paint, high-boot ankle limits, hinge elbows, flexible wrapped pads and facial shape keys. Godot runtime motion/cinematic checks are recorded separately; no platform performance certification.'}
OUT.joinpath('validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='meshes'},indent=2))
assert not fail,fail
assert all(report['protected_yara_unchanged'].values()),'Donor changed since initial read; inspect before delivery.'
