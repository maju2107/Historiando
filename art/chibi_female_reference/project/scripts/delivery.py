"""Save the final normal .blend plus portable full-character exports."""
import bpy,shutil,json
from config import PROJECT
from helpers import character_objects

def export_final():
    source=PROJECT/'output'/'07_final_cleanup.blend'
    dest=PROJECT/'output'/'chibi_female_base.blend'
    shutil.copy2(source,dest)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in character_objects(): obj.select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects['CHR_Body']
    bpy.ops.export_scene.gltf(filepath=str(PROJECT/'output'/'chibi_female_base.glb'),export_format='GLB',
      use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False)
    states=[]
    for obj in character_objects():
        for mod in obj.modifiers:
            if mod.type=='SUBSURF': states.append((mod,mod.show_viewport)); mod.show_viewport=False
    bpy.ops.wm.obj_export(filepath=str(PROJECT/'output'/'chibi_female_base.obj'),export_selected_objects=True,
      apply_modifiers=True,export_triangulated_mesh=False,export_materials=True)
    for mod,value in states: mod.show_viewport=value
    print('FINAL DELIVERABLE',dest)
