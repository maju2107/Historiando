"""Export the current Yara skin with its nine game actions; do not resave the source."""
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/yara/yara.blend'))
skin=bpy.data.objects['Yara_PaintedSkin'];rig=bpy.data.objects['YARA_Rig']
for o in bpy.data.objects:
 if o.type in ('MESH','CURVE'):o.hide_set(o!=skin)
 if o!=skin:
  for mod in o.modifiers:mod.show_viewport=False
for action in list(bpy.data.actions):
 if action.name.startswith('RigCheck_'):bpy.data.actions.remove(action)
bpy.ops.object.select_all(action='DESELECT');skin.hide_set(False);skin.select_set(True);rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/characters/yara/yara_playable.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False)
print('Exported current Yara. Reimport in Godot and run the two validation scripts.')
