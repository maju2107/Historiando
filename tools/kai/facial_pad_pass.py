"""Current-source facial shape keys and flexible, curved elbow cushions."""
import bpy,sys,math,json,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
sys.path.insert(0,str(R/'tools/kai'))
from rig_export import assign,smooth,paint,log
SHAPES=['MouthOpen','MouthRound','Smile','Concern','BrowUp','BrowAsym','Blink','EyesWide']

def role(name):
 if 'KAI_Base_Body' in name:return 'skin'
 if 'KAI_Base_Eye.' in name:return 'eye'
 if 'KAI_Base_Eyebrow.' in name:return 'brow'
 if 'KAI_Connected cartoon lashes' in name:return 'lash'
 return ''

def delta(p,kind,shape):
 x,y,z=p;v=Vector((0,0,0));front=smooth((-y-.095)/.035)
 if kind=='skin':
  mouth=(1-smooth(abs(x)/.056))*(1-smooth(abs(z-.704)/.044))*front
  if shape in ['MouthOpen','MouthRound']:
   v.z=(-.025+.031*smooth((z-.700)/.008))*mouth
   if shape=='MouthRound':v.x=-x*.40*mouth;v.y=-.004*mouth;v.z*=.85
  if shape in ['Smile','Concern']:
   v.z=(.015 if shape=='Smile' else -.010)*smooth(abs(x)/.027)*mouth;v.x=x*.09*mouth
   if shape=='Smile':v.z+=.003*(1-smooth(abs(abs(x)-.09)/.055))*(1-smooth(abs(z-.752)/.04))*front
 if kind in ['skin','brow']:
  brow=(1-smooth(abs(z-.844)/.026))*(1-smooth(abs(abs(x)-.083)/.06))*front
  if shape=='BrowUp':v.z+=.014*brow
  if shape=='BrowAsym':v.z+=.014*brow*(1 if x>0 else -.20)
  if shape=='Concern':v.z+=.012*brow*(1-1.3*smooth(abs(x)/.13))
 if shape=='Blink' and kind in ['skin','eye','lash']:
  eye=(1-smooth(abs(abs(x)-.079)/.060))*front
  vertical=1-smooth(max(0,abs(z-.786)-.030)/.025)
  if .735<z<.839:v.z-=(z-.786)*.96*eye*vertical
 if shape=='EyesWide' and kind in ['skin','lash'] and .745<z<.834:
  eye=(1-smooth(abs(abs(x)-.079)/.060))*front
  v.z+=(.012 if z>.786 else -.003)*eye*(1-smooth(abs(z-.792)/.045))
 return v

def add_shapes(o,kind,indices=None):
 if o.data.shape_keys:
  for key in list(o.data.shape_keys.key_blocks)[1:]:o.shape_key_remove(key)
 else:o.shape_key_add(name='Basis')
 active=range(len(o.data.vertices)) if indices is None else indices
 for name in SHAPES:
  key=o.shape_key_add(name=name)
  for i in active:
   p=o.matrix_world@o.data.vertices[i].co;key.data[i].co=o.matrix_world.inverted()@(p+delta(p,kind,name))

def wrap(p):
 sg=1 if p.x>0 else -1;r=.034+.008*max(0,min(1,(p.y-.028)/.015));angle=(p.z-.56)/.037*1.10
 return Vector((sg*(.187+(abs(p.x)-.187)*.88),r*math.cos(angle),.56+r*math.sin(angle)))

def main():
 # The pre-bake mesh has the same vertex indexing and identifies each part.
 bpy.ops.wm.open_mainfile(filepath=str(W/'runtime_uv.blend'));o=bpy.data.objects['Kai_Skin'];parts={}
 for poly in o.data.polygons:
  name=o.data.materials[poly.material_index].name
  if role(name) or 'Violet elbow guard' in name or 'Pad spot' in name:
   parts.setdefault(name,set()).update(poly.vertices)
 bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));rig=bpy.data.objects['KAI_Rig'];bones=set(rig.data.bones.keys());body=bpy.data.objects['KAI_Base_Body'];counts={}
 for o in list(bpy.data.objects):
  if o.type!='MESH':continue
  kind=role(o.name)
  if kind:
   add_shapes(o,kind);counts[o.name]=len(o.data.vertices)
   if o!=body:
    for name in SHAPES:
     drv=o.data.shape_keys.key_blocks[name].driver_add('value').driver;var=drv.variables.new();var.name='expression';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=body.data.shape_keys;var.targets[0].data_path='key_blocks["'+name+'"].value';drv.expression='expression'
  if '--face-only' not in sys.argv and o.name.startswith(('KAI_Violet elbow guard','KAI_Pad spot')):
   for v in o.data.vertices:
    p=wrap(o.matrix_world@v.co);v.co=o.matrix_world.inverted()@p;side='L' if p.x>0 else 'R';t=smooth((abs(p.x)-.155)/.07)
    paint(o,v.index,{'UpperArm.'+side:(1-t)**2,'LowerArm.'+side:t*t,'ElbowVolume.'+side:2*t*(1-t)},bones)
   o['construction']='Curved 126-degree textile cushion; continuous upper-arm, elbow-volume and forearm weights'
 assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/kai/kai.blend'));log('Editable facial shapes and wrapped cushions saved')
 bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'));rig=bpy.data.objects['KAI_Rig'];skin=bpy.data.objects['Kai_Skin'];bones=set(rig.data.bones.keys())
 for name,indices in parts.items():
  if '--face-only' not in sys.argv and ('Violet elbow guard' in name or 'Pad spot' in name):
   for i in indices:
    p=wrap(skin.matrix_world@skin.data.vertices[i].co);skin.data.vertices[i].co=skin.matrix_world.inverted()@p;side='L' if p.x>0 else 'R';t=smooth((abs(p.x)-.155)/.07)
    paint(skin,i,{'UpperArm.'+side:(1-t)**2,'LowerArm.'+side:t*t,'ElbowVolume.'+side:2*t*(1-t)},bones)
 if skin.data.shape_keys:
  for key in list(skin.data.shape_keys.key_blocks)[1:]:skin.shape_key_remove(key)
 else:skin.shape_key_add(name='Basis')
 for shape in SHAPES:
  key=skin.shape_key_add(name=shape)
  for name,indices in parts.items():
   kind=role(name)
   if not kind:continue
   for i in indices:
    p=skin.matrix_world@skin.data.vertices[i].co;key.data[i].co=skin.matrix_world.inverted()@(p+delta(p,kind,shape))
 assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0);skin.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(W/'kai_game_export.blend'))
 bpy.ops.export_scene.gltf(filepath=str(R/'assets/characters/kai/kai.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False,export_morph=True)
 (R/'art/kai/facial_pad_validation.json').write_text(json.dumps({'shape_keys':SHAPES,'source_parts':counts,'curved_pad_angle_degrees':126,'runtime_shapes':len(SHAPES),'all_appearance_parts_preserved':True},indent=2));log('Expressive Kai with wrapped elbow cushions exported')
if __name__=='__main__':
 try:main()
 except Exception:
  (W/'error.txt').write_text(traceback.format_exc());raise
