"""Refine cinematic hand poses on the current Kai rig; retain meshes and paint."""
import bpy,math,sys,json,traceback
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parents[2];W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
sys.path.insert(0,str(R/'tools/kai'))
from rig_export import assign,log
NAMES=['Talk','Explain','Correct','Shrug','Point','React']

def aimed(pb,direction):
 old=pb.matrix.copy();q=old.to_3x3().col[1].normalized().rotation_difference(direction.normalized())
 m=(q.to_matrix()@old.to_3x3()).to_4x4();m.translation=old.translation;pb.matrix=m;bpy.context.view_layer.update()

def arm(rig,side,wrist,fingers,palm_back):
 upper=rig.pose.bones['UpperArm.'+side];lower=rig.pose.bones['LowerArm.'+side];hand=rig.pose.bones['Hand.'+side]
 s=upper.head.copy();delta=Vector(wrist)-s;d=min(delta.length,.204);axis=delta.normalized();a=(upper.length**2-lower.length**2+d*d)/(2*d)
 pole=Vector((1 if side=='L' else -1,.25,-1));pole=(pole-axis*pole.dot(axis)).normalized()
 elbow=s+axis*a+pole*math.sqrt(max(0,upper.length**2-a*a))
 # Align the upper-arm roll with the bend plane. The forearm then rotates
 # around local X only, rather than twisting through an arbitrary IK roll.
 uy=(elbow-s).normalized();ly=(Vector(wrist)-elbow).normalized();hinge=uy.cross(ly).normalized()
 m=Matrix((hinge,uy,hinge.cross(uy))).transposed().to_4x4();m.translation=s
 upper.matrix=m;bpy.context.view_layer.update()
 lower.rotation_quaternion=Quaternion((1,0,0),uy.angle(ly));bpy.context.view_layer.update()
 y=Vector(fingers).normalized();x=Vector(palm_back);x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized()
 m=Matrix((x,y,z)).transposed().to_4x4();m.translation=hand.head;hand.matrix=m;bpy.context.view_layer.update()

def main():
 bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));rig=bpy.data.objects['KAI_Rig'];s=bpy.context.scene
 flags=[(m,m.show_viewport) for o in bpy.data.objects if o.type=='MESH' for m in o.modifiers]
 for m,flag in flags:m.show_viewport=False
 assign(rig,bpy.data.actions['Idle']);s.frame_set(0)
 base={p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy()) for p in rig.pose.bones}
 for name in NAMES:
  old=bpy.data.actions.get(name)
  if old:bpy.data.actions.remove(old)
  a=bpy.data.actions.new(name);a.use_fake_user=True;a['kai_clip']=True;assign(rig,a)
  for f in range(0,73,3):
   t=f/72;w=math.sin(math.pi*t)**.8
   for n,(l,q,sc) in base.items():
    p=rig.pose.bones[n];p.location=l;p.rotation_quaternion=q;p.scale=sc
   bpy.context.view_layer.update()
   if name in ['Talk','Explain']:arm(rig,'R',(-.17,-.10,.50),(-.12,-1,.22),(0,0,-1))
   elif name=='Correct':arm(rig,'R',(-.17,-.07,.53),(0,-.22,1),(0,1,0))
   elif name=='Point':arm(rig,'R',(-.16,-.13,.53),(-.1,-1,.25),(0,0,-1))
   elif name=='Shrug':
    arm(rig,'R',(-.19,-.055,.51),(-.65,-.65,.18),(0,0,-1))
    arm(rig,'L',(.19,-.055,.51),(.65,-.65,.18),(0,0,-1))
   target={p.name:p.rotation_quaternion.copy() for p in rig.pose.bones}
   for p in rig.pose.bones:
    p.rotation_quaternion=base[p.name][1].slerp(target[p.name],w)
    if p.name.startswith(('Index.','Middle.','Ring.','Little.','Thumb.')) and p.name.endswith('.R') and name in ['Talk','Explain','Correct','Point']:
     angle=.05 if name in ['Talk','Explain'] or p.name.startswith('Index.') else .88
     if name in ['Correct','Point'] and p.name.startswith('Index.1.'):angle=-.50
     if p.name.startswith('Thumb.'):angle=.30
     p.rotation_quaternion=base[p.name][1].slerp(Quaternion((0,0,1),angle),w)
    if p.name=='Head':p.rotation_quaternion=base[p.name][1]@Quaternion((1,0,0),.06*w*math.sin(t*3*math.pi))@Quaternion((0,0,1),(.20 if name=='React' else .055)*w*math.sin(t*2*math.pi))
    if p.name=='Chest':p.rotation_quaternion=base[p.name][1]@Quaternion((1,0,0),(-.10 if name=='React' else .02)*w)
    for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(data_path=channel,frame=f,group=p.name)
 assign(rig,bpy.data.actions['Idle']);s.frame_set(0);bpy.context.preferences.filepaths.save_version=0
 for m,flag in flags:m.show_viewport=flag
 bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/kai/kai.blend'));log('Refined palm-up and pointing gestures saved')
 bpy.ops.wm.open_mainfile(filepath=str(W/'kai_game_export.blend'));rig=bpy.data.objects['KAI_Rig'];rig.animation_data_clear()
 for n in NAMES:
  a=bpy.data.actions.get(n)
  if a:bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(R/'art/kai/kai.blend'),link=False) as (src,dst):dst.actions=NAMES
 for action in dst.actions:action.use_fake_user=True;assign(rig,action)
 assign(rig,bpy.data.actions['Idle']);bpy.context.scene.frame_set(0)
 bpy.ops.wm.save_as_mainfile(filepath=str(W/'kai_game_export.blend'))
 bpy.ops.export_scene.gltf(filepath=str(R/'assets/characters/kai/kai.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False)
 log('Refined gesture GLB exported')
if __name__=='__main__':
 try:main()
 except Exception:
  (W/'error.txt').write_text(traceback.format_exc());raise
