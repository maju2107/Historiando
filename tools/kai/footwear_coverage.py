"""Keep hidden body faces inside boots out of the render, non-destructively in source."""
import bpy,bmesh,sys,json,traceback,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
sys.path.insert(0,str(R/'tools/kai'))
from rig_export import assign,log

def main():
 if not (W/'kai_before_coverage.blend').exists():shutil.copy2(R/'art/kai/kai.blend',W/'kai_before_coverage.blend')
 bpy.ops.wm.open_mainfile(filepath=str(W/'runtime_uv.blend'));skin=bpy.data.objects['Kai_Skin'];body_indices=set()
 for poly in skin.data.polygons:
  if 'KAI_Base_Body' in skin.data.materials[poly.material_index].name:body_indices.update(poly.vertices)
 bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));body=bpy.data.objects['KAI_Base_Body'];group=body.vertex_groups.get('Footwear coverage') or body.vertex_groups.new(name='Footwear coverage')
 for v in body.data.vertices:group.add([v.index],1.0 if v.co.z>=.14 else 0.0,'REPLACE')
 mod=body.modifiers.get('Concealed skin inside boots') or body.modifiers.new('Concealed skin inside boots','MASK');mod.vertex_group=group.name
 index=next(i for i,m in enumerate(body.modifiers) if m.type=='ARMATURE');body.modifiers.move(list(body.modifiers).index(mod),index)
 mod.show_in_editmode=False
 body['footwear_coverage']='Non-destructive display mask below .14 m; original foot topology and weights retained for editing.'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/kai/kai.blend'))
 bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'));skin=bpy.data.objects['Kai_Skin'];bm=bmesh.new();bm.from_mesh(skin.data);bm.verts.ensure_lookup_table()
 faces=[p for p in bm.faces if all(v.index in body_indices and v.co.z<.14 for v in p.verts)];count=len(faces)
 bmesh.ops.delete(bm,geom=faces,context='FACES_ONLY');bm.to_mesh(skin.data);bm.free();skin.data.update()
 rig=bpy.data.objects['KAI_Rig'];assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/'kai_game_export.blend'))
 bpy.ops.export_scene.gltf(filepath=str(R/'assets/characters/kai/kai.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False,export_morph=True)
 (R/'art/kai/footwear_coverage_validation.json').write_text(json.dumps({'native_body_topology_retained':True,'source_display_mask':'Concealed skin inside boots','runtime_hidden_faces_removed':count,'coverage_cutoff_m':.14,'backup':str(W/'kai_before_coverage.blend')},indent=2));log('Concealed footwear body faces masked and runtime exported')
if __name__=='__main__':
 try:main()
 except Exception:
  (W/'error.txt').write_text(traceback.format_exc());raise
