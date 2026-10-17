"""Independent reopen: normalized paint, neutral defaults, local edits and rig preservation."""
import bpy,json,hashlib,math,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/expressive_faces_2026-10-16')
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));data={}
 for o in bpy.data.objects:
  if o.type=='MESH':
   # Bone weights only: authoring masks deliberately add non-deform groups.
   arm=next((m.object for m in o.modifiers if m.type=='ARMATURE' and m.object),None)
   bones=set(arm.data.bones.keys()) if arm else set()
   data[o.name]={'p':[tuple(v.co) for v in o.data.vertices],'weights':[{o.vertex_groups[g.group].name:round(g.weight,6) for g in v.groups if o.vertex_groups[g.group].name in bones} for v in o.data.vertices]}
 clips={}
 for a in bpy.data.actions:
  rows=[]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for f in bag.fcurves:rows.append((f.data_path,f.array_index,[(tuple(k.co),k.interpolation) for k in f.keyframe_points]))
  clips[a.name]=hashlib.sha256(repr(sorted(rows)).encode()).hexdigest()
 return data,clips
out={};issues=[]
for who in ['Kai','Yara']:
 old,old_clips=snapshot(W/(who.lower()+'_before.blend'));path=R/('art/'+who.lower()+'/'+who.lower()+'.blend');new,new_clips=snapshot(path)
 assert old_clips==new_clips,who+' original animation actions changed'
 changed=[];outside=[];nonunit=0;unweighted=0;maximum=0
 skin_name='KAI_Base_Body' if who=='Kai' else 'Yara_PaintedSkin';face_names=[skin_name,'CHR_Body'] if who=='Yara' else [skin_name]
 for name,a in old.items():
  assert name in new,name
  b=new[name];assert len(b['p'])>=len(a['p']),name
  for i,(p,q) in enumerate(zip(a['p'],b['p'])):
   dist=sum((x-y)**2 for x,y in zip(p,q))**.5
   if dist>1e-7:
    changed.append((name,i))
    if name not in face_names or not(abs(p[0])<.19 and p[1]<-.075 and .64<p[2]<.90):outside.append((name,i))
   # Clothing, hair, accessories and limbs keep their exact original paint.
   if (name not in face_names or not(abs(p[0])<.19 and p[1]<-.075 and .64<p[2]<.90)) and a['weights'][i]!=b['weights'][i]:outside.append((name,i,'weights'))
  for weights in b['weights']:
   if not weights:continue
   s=sum(weights.values());maximum=max(maximum,abs(s-1));nonunit+=int(abs(s-1)>.001)
 if outside:issues.append(who+' edits outside the facial scope: '+str(outside[:5]))
 if nonunit:issues.append(who+' unnormalized weights')
 body=bpy.data.objects[skin_name];keys=body.data.shape_keys.key_blocks
 assert len(keys)==18
 assert all(abs(k.value)<1e-7 for k in list(keys)[1:])
 for key in keys:
  assert all(all(math.isfinite(c) for c in v.co) for v in key.data)
 rig=bpy.data.objects['KAI_Rig' if who=='Kai' else 'YARA_Rig']
 assert len(rig.data.bones)==60
 glb=R/('assets/characters/kai/kai.glb' if who=='Kai' else 'assets/characters/yara/yara_playable.glb')
 out[who]={'source_reopened':True,'bones':60,'shape_keys':list(keys.keys())[1:],'neutral_shape_defaults':True,'changed_existing_vertices':len(changed),'outside_face_changes':len(outside),'original_animation_actions_unchanged':True,'normalized_bone_weights':nonunit==0,'maximum_weight_sum_error':maximum,'editable_masks':[g.name for g in body.vertex_groups if g.name.startswith('Face_')],'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'runtime_sha256':hashlib.sha256(glb.read_bytes()).hexdigest()}
out['issues']=issues
(R/'art/island_intro/facial_source_validation.json').write_text(json.dumps(out,indent=2))
assert not issues,issues
print('NATIVE_FACIAL_SOURCE_PASS')
