"""Monotone joint weight bands and continuous palm-to-finger transitions."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from head_refinement import smoothstep as ss
from game_rig import DIGITS,point_segment
from game_restore import checkpoint
from game_pose_validation import validate_poses,make_action,render

def write_weights(obj,vertex,weights):
    values=sorted([(n,w) for n,w in weights.items() if w>1e-6],key=lambda p:p[1],reverse=True)[:4]
    total=sum(w for n,w in values)
    for item in list(vertex.groups): obj.vertex_groups[item.group].remove([vertex.index])
    for name,w in values: obj.vertex_groups[name].add([vertex.index],w/total,'REPLACE')

def refine():
    body=bpy.data.objects['CHR_Body']
    for v in body.data.vertices:
        x,y,z=v.co; ax=abs(x); side='L' if x>=0 else 'R'; weights=None
        if ax>.038 and z>.50:
            shoulder=ss(.038,.145,ax); elbow=ss(.138,.245,ax); wrist=ss(.255,.310,ax)
            weights={'chest':1-shoulder,'upper_arm.'+side:shoulder*(1-elbow),'forearm.'+side:shoulder*elbow*(1-wrist),'hand.'+side:shoulder*elbow*wrist}
            if ax>.310:
                co=Vector((ax,y,z)); scores={}
                for digit,points in DIGITS.items():
                    d=min(point_segment(co,Vector(a),Vector(b))[0] for a,b in zip(points,points[1:]))
                    scores[digit]=math.exp(-d*d/.00024)
                if ax>.395:
                    best=max(scores,key=scores.get); scores={best:1.0}
                total=sum(scores.values()); influence=0; new={}
                for digit,score in scores.items():
                    points=DIGITS[digit]; amount=ss(points[0][0]-.029,points[0][0]+.017,ax)*(score/total)
                    influence+=amount
                    t=ss(points[1][0]-.012,points[1][0]+.012,ax)
                    if len(points)==4:
                        u=ss(points[2][0]-.010,points[2][0]+.010,ax)
                        parts=[1-t,t*(1-u),t*u]
                    else: parts=[1-t,t]
                    for i,w in enumerate(parts,1):new[f'{digit}_{i:02d}.{side}']=w*amount
                for name,w in weights.items(): new[name]=new.get(name,0)+w*(1-influence)
                weights=new
        elif z<.425:
            leg=(1-ss(.323,.407,z))*ss(.010,.044,ax); knee=1-ss(.155,.278,z); ankle=1-ss(.058,.138,z)
            toes=(1-ss(-.105,-.06,y))*(1-ss(.045,.073,z))
            weights={'pelvis':1-leg,'thigh.'+side:leg*(1-knee),'shin.'+side:leg*knee*(1-ankle),
                     'foot.'+side:leg*knee*ankle*(1-toes),'toe.'+side:leg*knee*ankle*toes}
        if weights is not None: write_weights(body,v,weights)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_11_deformation_validation.blend'))
    rig=bpy.data.objects['RIG_Chibi']; rig.animation_data_clear(); bpy.context.scene.timeline_markers.clear()
    refine(); report=validate_poses(rig); make_action(rig)
    checkpoint(11,'refined_joint_weights','Replaced sharp heat-weight transitions with broad monotone bands at shoulders/elbows/knees/ankles and continuous digit-chain weights across the palm. Five poses audited again.')
    for frame,name,camera in [(20,'relaxed','CAM_ThreeQuarter'),(40,'joint_bend','CAM_ThreeQuarter'),(80,'hand_curl','CAM_Hand')]:
        bpy.context.scene.frame_set(frame); render(name,camera,1200)

if __name__=='__main__': main()
