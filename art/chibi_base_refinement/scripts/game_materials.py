"""Prepare runtime UVs and transfer original facial surface detail to a normal map."""
import bpy,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes
from game_retopology import select
from game_restore import checkpoint
from game_pose_validation import render

def prepare_uvs():
    for obj in meshes():
        select(obj)
        while obj.data.uv_layers:obj.data.uv_layers.remove(obj.data.uv_layers[0])
        obj.data.uv_layers.new(name='GameUV')
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.018)
        bpy.ops.object.mode_set(mode='OBJECT')

def bake_head():
    low=bpy.data.objects['CHR_Head']; high=bpy.data.objects['HIGH_CHR_Head']; col=bpy.data.collections['SCULPT_SOURCE']
    col.hide_viewport=False; col.hide_render=False
    for obj in col.objects: obj.hide_render=True
    high.hide_render=False; high.hide_set(False)
    for m in high.modifiers:
        if m.type=='SUBSURF': m.levels=1; m.render_levels=1
    mat=bpy.data.materials['MAT_ReferenceClay'].copy(); mat.name='MAT_GameHead'; low.data.materials.clear(); low.data.materials.append(mat)
    image=bpy.data.images.new('Chibi_head_normal',width=2048,height=2048,alpha=False); image.colorspace_settings.name='Non-Color'
    image.generated_color=(.5,.5,1,1)
    node=mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image=image; node.label='Original face detail / tangent normal'; mat.node_tree.nodes.active=node
    select(low); high.select_set(True); bpy.context.view_layer.objects.active=low
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=8
    scene.render.bake.use_selected_to_active=True; scene.render.bake.cage_extrusion=.012; scene.render.bake.max_ray_distance=.035
    scene.render.bake.margin=16; scene.render.bake.normal_space='TANGENT'
    bpy.ops.object.bake(type='NORMAL')
    folder=PROJECT/'textures'; folder.mkdir(exist_ok=True)
    image.filepath_raw=str(folder/'chibi_head_normal.png'); image.file_format='PNG'; image.save(); image.pack()
    normal=mat.node_tree.nodes.new('ShaderNodeNormalMap'); normal.inputs['Strength'].default_value=1
    mat.node_tree.links.new(node.outputs['Color'],normal.inputs['Color'])
    mat.node_tree.links.new(normal.outputs['Normal'],mat.node_tree.nodes['Principled BSDF'].inputs['Normal'])
    high.hide_render=True; col.hide_viewport=True; col.hide_render=True
    scene.render.bake.use_selected_to_active=False; scene.cycles.samples=32

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_11_refined_joint_weights.blend'))
    bpy.context.scene.frame_set(1)
    for obj in meshes():
        for mod in obj.modifiers:
            if mod.type=='SUBSURF':mod.show_viewport=False;mod.show_render=False
    prepare_uvs(); bake_head()
    checkpoint(12,'runtime_materials','Prepared fresh game UVs, disabled optional subdivision for the runtime mesh, and baked the original head surface onto a packed 2K tangent normal texture. Rig stays in T-pose at frame 1.')
    render('runtime_face','CAM_Face',1200); render('runtime_three_quarter','CAM_ThreeQuarter',1200)
    bpy.context.scene.frame_set(40); render('runtime_joint_bend','CAM_ThreeQuarter',1200)

if __name__=='__main__':main()
