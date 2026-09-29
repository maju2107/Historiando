"""Normalize the evaluated result, measure it, and render review closeups.

Starts at the latest numbered checkpoint; never rebuilds the source character.
"""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes,collection,aim,sync_basis,save_checkpoint,render_views
from validation import audit

def evaluated_bounds():
    points=[]; graph=bpy.context.evaluated_depsgraph_get()
    for obj in meshes():
        ev=obj.evaluated_get(graph); me=ev.to_mesh()
        points.extend(obj.matrix_world@v.co for v in me.vertices); ev.to_mesh_clear()
    return np.min(points,axis=0),np.max(points,axis=0)

def normalize_floor():
    lo,hi=evaluated_bounds(); scale=1/(hi[2]-lo[2]); floor=float(lo[2])
    for obj in meshes():
        sets=[obj.data.vertices]
        if obj.data.shape_keys: sets.extend(k.data for k in obj.data.shape_keys.key_blocks)
        for vertices in sets:
            for v in vertices: v.co=(v.co-Vector((0,0,floor)))*scale
        obj.data.update()
    sync_basis()
    bpy.context.scene['final_normalization']=json.dumps({'scale':float(scale),'floor_before':floor})

def measure_result():
    from proportions import section_bounds
    reference=json.loads((PROJECT/'references'/'analysis.json').read_text())
    body=bpy.data.objects['CHR_Body']; head=bpy.data.objects['CHR_Head']; rows=[]
    for label,z,obj in [('foot_span',.025,body),('lower_leg_span',.12,body),('knee_span',.213,body),('hip_span',.39,body),('waist',.48,body),('head_width',.82,head),('upper_head',.94,head)]:
        lo,hi=section_bounds(obj,z)
        target=next(s['width_m'] for s in reference['measurements']['FRONT']['sections'] if s['z_m']==z)
        rows.append({'landmark':label,'z_m':z,'target_m':target,'model_m':float(hi[0]-lo[0]),'difference_mm':float((hi[0]-lo[0]-target)*1000)})
    eyes=[]
    for label in ['L','R']:
        eye=bpy.data.objects['CHR_Eye.'+label]; co=np.array([v.co[:] for v in eye.data.vertices]); lo=co.min(axis=0); hi=co.max(axis=0)
        eyes.append({'name':eye.name,'center':((hi+lo)/2).tolist(),'dimensions':(hi-lo).tolist()})
    (PROJECT/'output'/'proportion_comparison.json').write_text(json.dumps({'front_sections':rows,'eyes':eyes,'note':'Section dimensions of the preserved control cage; reference measurements are approximate screenshot measurements.'},indent=2))

def create_detail_cameras():
    for name,location,target,scale in [
        ('Face',(0,-3,.817),(0,0,.817),.49),
        ('Hand',(.385,-.018,1.3),(.385,-.018,.55),.28),
        ('FaceThreeQuarter',(.9,-2,.93),(0,0,.814),.49)]:
        cam=bpy.data.objects.get('CAM_'+name)
        if cam is None:
            cam=bpy.data.objects.new('CAM_'+name,bpy.data.cameras.new('CAM_'+name)); collection('VALIDATION').objects.link(cam)
        cam.location=location; cam.data.type='ORTHO'; cam.data.ortho_scale=scale; aim(cam,target); cam.hide_set(True)

def create_wire_review():
    col=collection('TOPOLOGY_REVIEW'); col.hide_render=False; col.hide_viewport=False
    mat=bpy.data.materials.get('MAT_ControlEdges') or bpy.data.materials.new('MAT_ControlEdges')
    mat.use_nodes=True; bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(.003,.004,.004,1); bs.inputs['Roughness'].default_value=1
    for obj in meshes():
        states=[m for m in obj.modifiers if m.type=='SUBSURF' and m.show_viewport]
        for mod in states: mod.show_viewport=False
        bpy.context.view_layer.update(); graph=bpy.context.evaluated_depsgraph_get()
        me=bpy.data.meshes.new_from_object(obj.evaluated_get(graph),depsgraph=graph)
        for mod in states: mod.show_viewport=True
        wire=bpy.data.objects.new('REVIEW_'+obj.name,me); col.objects.link(wire)
        me.materials.clear(); me.materials.append(mat)
        modifier=wire.modifiers.new('Actual control mesh edges','WIREFRAME')
        modifier.thickness=.000045; modifier.offset=1; modifier.use_replace=True; modifier.use_even_offset=False
        wire['purpose']='Actual preserved control edges. Display helper only; not character geometry.'
    col.hide_render=True; col.hide_viewport=True

def render_details():
    scene=bpy.context.scene; scene.render.resolution_x=1400; scene.render.resolution_y=1400
    for camera,file in [('Face','face_closeup.png'),('FaceThreeQuarter','face_three_quarter.png'),('Hand','hand_after.png')]:
        scene.camera=bpy.data.objects['CAM_'+camera]; scene.render.filepath=str(PROJECT/'renders'/file); bpy.ops.render.render(write_still=True)
    col=bpy.data.collections['TOPOLOGY_REVIEW']; col.hide_render=False
    states=[]
    for obj in meshes():
        for mod in obj.modifiers:
            if mod.type=='SUBSURF': states.append((mod,mod.show_render)); mod.show_render=False
    for camera,file in [('Face','topology_face.png'),('Front','topology_front.png'),('Hand','topology_hand.png')]:
        scene.camera=bpy.data.objects['CAM_'+camera]; scene.render.filepath=str(PROJECT/'renders'/file); bpy.ops.render.render(write_still=True)
    for mod,state in states: mod.show_render=state
    col.hide_render=True; scene.camera=bpy.data.objects['CAM_ThreeQuarter']

def main():
    state=json.loads((PROJECT/'progress.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/state['latest_checkpoint']))
    normalize_floor(); measure_result(); create_detail_cameras(); create_wire_review()
    a=audit('delivery_control',False); b=audit('delivery_subdivision',True)
    assert not a['issues'] and not b['issues']
    save_checkpoint(7,'Aligned the subdivided soles to Z=0 and height to 1 m, measured final proportions, and added disabled actual-topology review meshes and detail cameras.',revision='d')
    render_views(7,1200); render_details()

if __name__=='__main__': main()
