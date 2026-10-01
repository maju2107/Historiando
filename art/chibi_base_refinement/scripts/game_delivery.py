"""Review geometry, write editable rig and export only runtime character assets."""
import bpy,sys,json,math,datetime
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes,collection
from game_restore import checkpoint
from game_pose_validation import render,set_pose
from game_retopology import select
from validation import audit

def runtime_modifiers():
    for obj in meshes():
        for m in obj.modifiers:
            if m.type=='SUBSURF':m.show_viewport=False;m.show_render=False

def create_rig_review(rig):
    col=collection('RIG_REVIEW')
    materials={}
    for label,color in [('L',(.05,.45,1,1)),('R',(1,.24,.035,1)),('C',(.15,.9,.45,1))]:
        mat=bpy.data.materials.new('REVIEW_Bone_'+label);mat.diffuse_color=color;mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color
        bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=.4;materials[label]=mat
    for b in rig.data.bones:
        a=b.head_local.copy(); end=b.tail_local.copy(); direction=(end-a).normalized(); length=(end-a).length
        p=direction.cross(Vector((0,1,0)))
        if p.length<.1:p=direction.cross(Vector((1,0,0)))
        p.normalize();q=direction.cross(p); mid=a+(end-a)*.27; radius=min(.007,max(.0012,length*.11))
        coords=[a,end,mid+p*radius,mid+q*radius,mid-p*radius,mid-q*radius]
        faces=[]
        for i in range(4):j=2+i;k=2+(i+1)%4;faces.extend([(0,j,k),(1,k,j)])
        me=bpy.data.meshes.new('Review bone');me.from_pydata(coords,[],faces)
        ob=bpy.data.objects.new('REVIEW_'+b.name,me);col.objects.link(ob);me.materials.append(materials['L' if b.name.endswith('.L') else 'R' if b.name.endswith('.R') else 'C'])
    return col

def reviews(rig):
    from prepare_delivery import create_wire_review
    create_wire_review();wire=bpy.data.collections['TOPOLOGY_REVIEW'];wire.hide_render=False
    render('topology_front','CAM_Front',1400);render('topology_hand','CAM_Hand',1400);render('topology_face','CAM_Face',1400)
    wire.hide_render=True;wire.hide_viewport=True
    col=create_rig_review(rig)
    ghost=bpy.data.materials.new('REVIEW_Ghost');ghost.use_nodes=True;nodes=ghost.node_tree.nodes;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.22
    transparent=nodes.new('ShaderNodeBsdfTransparent');bs=nodes.new('ShaderNodeBsdfDiffuse');bs.inputs['Color'].default_value=(.6,.65,.7,1)
    links=ghost.node_tree.links;links.new(transparent.outputs[0],mix.inputs[1]);links.new(bs.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
    old={o:list(o.data.materials) for o in meshes()}
    for o in meshes():o.data.materials.clear();o.data.materials.append(ghost)
    render('skeleton_front','CAM_Front',1400)
    for o,mats in old.items():
        o.data.materials.clear()
        for m in mats:o.data.materials.append(m)
    col.hide_viewport=True;col.hide_render=True

def store_expected_poses(rig):
    action=rig.animation_data.action;rig.animation_data.action=None; data={}
    for frame in (1,40,80):
        set_pose(rig,frame)
        graph=bpy.context.evaluated_depsgraph_get()
        for obj in meshes():
            ev=obj.evaluated_get(graph);me=ev.to_mesh();data[f'{frame}__{obj.name}']=np.array([obj.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear()
    np.savez_compressed(str(PROJECT/'output'/'game_expected_poses.npz'),**data)
    rig.animation_data.action=action;bpy.context.scene.frame_set(1)

def export_files(rig):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes():obj.select_set(True)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(PROJECT/'output'/'character_GAME_RIGGED.glb'),export_format='GLB',
        use_selection=True,export_animations=False,export_skins=True,export_all_influences=False,export_apply=False)
    bpy.ops.export_scene.fbx(filepath=str(PROJECT/'output'/'character_GAME_RIGGED.fbx'),use_selection=True,
        object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,
        use_armature_deform_only=True,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_12_runtime_detail.blend'))
    rig=bpy.data.objects['RIG_Chibi'];scene=bpy.context.scene;scene.frame_set(1);runtime_modifiers()
    report=audit('game_final_rest',False);assert not report['issues'];runtime_modifiers()
    poses=json.loads((PROJECT/'output'/'game_pose_audit.json').read_text());assert all(p['self_intersection_count']==0 for p in poses.values())
    stats={'vertices':sum(len(o.data.vertices) for o in meshes()),'faces':sum(len(o.data.polygons) for o in meshes()),
      'quads':sum(len(p.vertices)==4 for o in meshes() for p in o.data.polygons),'triangles_when_exported':sum(len(p.vertices)-2 for o in meshes() for p in o.data.polygons),
      'bones':len(rig.data.bones),'deform_bones':sum(b.use_deform for b in rig.data.bones),'parts':{},'pose_tests':{n:{'self_intersections':p['self_intersection_count'],'stretch_p99':p['edge_stretch_p99']} for n,p in poses.items()}}
    for obj in meshes():
        stats['parts'][obj.name]={'vertices':len(obj.data.vertices),'max_influences':max(len(v.groups) for v in obj.data.vertices),
          'weight_error':max(abs(sum(g.weight for g in v.groups)-1) for v in obj.data.vertices),'uv_layers':len(obj.data.uv_layers)}
    (PROJECT/'output'/'game_final_stats.json').write_text(json.dumps(stats,indent=2))
    reviews(rig);store_expected_poses(rig);runtime_modifiers()
    scene.camera=bpy.data.objects['CAM_ThreeQuarter'];scene.render.resolution_x=1200;scene.render.resolution_y=1200
    select(rig)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.region_3d.view_location=Vector((0,0,.52));space.region_3d.view_distance=1.65
                space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion();space.region_3d.view_perspective='ORTHO'
    rig.animation_data.action.name='TEST_Deformacao_FK';scene.frame_set(1)
    for name in ['SCULPT_SOURCE','SOURCE_PARTS','REFERENCES','TOPOLOGY_REVIEW','RIG_REVIEW']:
        col=bpy.data.collections.get(name)
        if col:col.hide_viewport=True;col.hide_render=True
    for doc in ['GAME_README.md']:
        if (PROJECT/doc).exists():bpy.data.texts.load(str(PROJECT/doc))
    checkpoint(13,'game_ready','Runtime mesh and FK skeleton reviewed in five test poses, with no body self-intersections detected. Packed face normal map, reference images, source archive and topology/rig review helpers retained. Export/reimport verification follows.')
    final=PROJECT/'output'/'character_GAME_RIGGED.blend'
    if final.exists():raise RuntimeError('Preserve previous game delivery')
    bpy.ops.wm.save_as_mainfile(filepath=str(final));export_files(rig)
    print('GAME STATS',json.dumps(stats),flush=True)

if __name__=='__main__':main()
