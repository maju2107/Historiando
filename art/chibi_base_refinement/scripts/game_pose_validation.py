"""Create a documented FK deformation test and inspect posed meshes."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes,collection,aim
from game_restore import checkpoint
from validation import mesh_report

POSES={1:'T_POSE',20:'RELAXED',40:'ELBOW_KNEE_BEND',60:'HEAD_TURN',80:'FINGER_CURL'}

def set_pose(rig,frame):
    for pb in rig.pose.bones:
        pb.location=(0,0,0); pb.scale=(1,1,1); pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=Quaternion()
    def rotate(name,axis,angle):
        pb=rig.pose.bones[name]; local=(rig.matrix_world.to_3x3()@pb.bone.matrix_local.to_3x3()).inverted()@Vector(axis)
        pb.rotation_quaternion=Quaternion(local,math.radians(angle))
    if frame==20:
        rotate('upper_arm.L',(0,1,0),55); rotate('upper_arm.R',(0,1,0),-55)
        rotate('forearm.L',(0,0,1),-12); rotate('forearm.R',(0,0,1),12)
    if frame==40:
        rotate('upper_arm.L',(0,1,0),35); rotate('upper_arm.R',(0,1,0),-35)
        rotate('forearm.L',(0,0,1),-65); rotate('forearm.R',(0,0,1),65)
        rotate('thigh.L',(1,0,0),-25); rotate('shin.L',(1,0,0),55)
        rotate('foot.L',(1,0,0),-25); rotate('spine',(0,0,1),8)
    if frame==60:
        rotate('neck',(0,0,1),12); rotate('head',(0,0,1),18); rotate('head',(0,1,0),12)
        rotate('upper_arm.L',(0,1,0),48); rotate('upper_arm.R',(0,1,0),-48)
    if frame==80:
        for side,sign in [('L',1),('R',-1)]:
            for digit in ('index','middle','ring'):
                for j,angle in [(1,38),(2,42),(3,25)]: rotate(f'{digit}_{j:02d}.{side}',(0,1,0),sign*angle)
            rotate('thumb_01.'+side,(0,1,0),sign*22); rotate('thumb_02.'+side,(0,1,0),sign*25)
    bpy.context.view_layer.update()

def render(name,camera,res=1100):
    scene=bpy.context.scene; scene.camera=bpy.data.objects[camera]; scene.render.resolution_x=res; scene.render.resolution_y=res
    scene.render.filepath=str(PROJECT/'renders'/'game'/(name+'.png')); bpy.ops.render.render(write_still=True)

def validate_poses(rig):
    body=bpy.data.objects['CHR_Body']; baseline=[(body.data.vertices[e.vertices[0]].co-body.data.vertices[e.vertices[1]].co).length for e in body.data.edges]
    report={}
    for frame,label in POSES.items():
        set_pose(rig,frame)
        states=[m for m in body.modifiers if m.type=='SUBSURF']
        for m in states:m.show_viewport=False
        bpy.context.view_layer.update(); ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
        audit=mesh_report(me,False,True); stretches=[]
        for e,rest in zip(me.edges,baseline):
            if rest>1e-5: stretches.append((me.vertices[e.vertices[0]].co-me.vertices[e.vertices[1]].co).length/rest)
        stretches.sort(); audit['edge_stretch_p99']=stretches[int(len(stretches)*.99)]; audit['edge_stretch_max']=max(stretches)
        report[label]=audit; ev.to_mesh_clear()
        for m in states:m.show_viewport=True
        print('POSE AUDIT',label,audit['self_intersection_count'],audit['edge_stretch_p99'],audit['edge_stretch_max'],flush=True)
    (PROJECT/'output'/'game_pose_audit.json').write_text(json.dumps(report,indent=2))
    return report

def make_action(rig):
    rig.animation_data_create(); action=bpy.data.actions.new('TEST_Deformation_FK'); rig.animation_data.action=action
    for frame,label in POSES.items():
        set_pose(rig,frame)
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
            pb.keyframe_insert('location',frame=frame,group=pb.name)
        bpy.context.scene.timeline_markers.new(label,frame=frame)
    action.use_fake_user=True; bpy.context.scene.frame_start=1; bpy.context.scene.frame_end=80; bpy.context.scene.frame_set(1)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_10_skeleton_skinning.blend'))
    (PROJECT/'renders'/'game').mkdir(exist_ok=True)
    rig=bpy.data.objects['RIG_Chibi']; validate_poses(rig); make_action(rig)
    for frame,name in [(1,'rest_three_quarter'),(20,'relaxed'),(40,'joint_bend'),(60,'head_turn')]:
        bpy.context.scene.frame_set(frame); render(name,'CAM_ThreeQuarter')
    bpy.context.scene.frame_set(80); render('hand_curl','CAM_Hand',1200)
    bpy.context.scene.frame_set(1); render('hand_rest','CAM_Hand',1200); render('front','CAM_Front'); render('back','CAM_Back'); render('face','CAM_Face',1200)
    checkpoint(11,'deformation_validation','Added five FK test poses and rendered head/hand/joint deformation. Rest pose at frame 1. See game_pose_audit.json; any remaining pose issues must be reviewed before final export.')

if __name__=='__main__': main()
