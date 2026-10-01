"""Deformation skeleton, FK controls, calibrated finger chains and skin weights."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes,collection
from game_restore import checkpoint
from game_retopology import select
from head_refinement import smoothstep

DIGITS={
 'index':[(.368,-.035,.599),(.398,-.036,.591),(.425,-.035,.580),(.446,-.034,.572)],
 'middle':[(.368,.000,.605),(.401,.006,.596),(.430,.010,.585),(.461,.011,.571)],
 'ring':[(.367,.043,.588),(.392,.049,.573),(.412,.052,.563),(.432,.055,.549)],
 'thumb':[(.332,-.047,.568),(.362,-.068,.550),(.397,-.064,.540)]}

def create_rig():
    data=bpy.data.armatures.new('Chibi game skeleton'); rig=bpy.data.objects.new('RIG_Chibi',data); collection('RIG').objects.link(rig)
    rig.show_in_front=True; data.display_type='OCTAHEDRAL'; select(rig); bpy.ops.object.mode_set(mode='EDIT')
    def bone(name,head,tail,parent=None,deform=True):
        b=data.edit_bones.new(name); b.head=head; b.tail=tail; b.use_deform=deform
        if parent: b.parent=data.edit_bones[parent]
        if abs((b.tail-b.head).normalized().dot(Vector((0,1,0))))<.9: b.align_roll(Vector((0,1,0)))
        return b
    bone('root',(0,0,0),(0,0,.09),deform=False)
    bone('pelvis',(0,.005,.35),(0,.005,.425),'root')
    bone('spine',(0,.005,.425),(0,0,.49),'pelvis')
    bone('chest',(0,0,.49),(0,0,.567),'spine')
    bone('neck',(0,0,.567),(0,-.013,.640),'chest')
    bone('head',(0,-.013,.640),(0,.02,.930),'neck')
    for side,suffix in [(1,'L'),(-1,'R')]:
        def p(v): return (side*v[0],v[1],v[2])
        bone('clavicle.'+suffix,p((.012,0,.557)),p((.080,0,.561)),'chest')
        bone('upper_arm.'+suffix,p((.080,0,.561)),p((.188,0,.561)),'clavicle.'+suffix)
        bone('forearm.'+suffix,p((.188,0,.561)),p((.282,0,.565)),'upper_arm.'+suffix)
        bone('hand.'+suffix,p((.282,0,.565)),p((.367,0,.581)),'forearm.'+suffix)
        for digit,points in DIGITS.items():
            parent='hand.'+suffix
            for i,(a,b) in enumerate(zip(points,points[1:]),1):
                name=f'{digit}_{i:02d}.{suffix}'; bone(name,p(a),p(b),parent); parent=name
        bone('thigh.'+suffix,p((.070,.005,.372)),p((.074,-.016,.218)),'pelvis')
        bone('shin.'+suffix,p((.074,-.016,.218)),p((.084,.008,.083)),'thigh.'+suffix)
        bone('foot.'+suffix,p((.084,.008,.083)),p((.084,-.075,.031)),'shin.'+suffix)
        bone('toe.'+suffix,p((.084,-.075,.031)),p((.084,-.114,.026)),'foot.'+suffix)
        eye=bpy.data.objects['CHR_Eye.'+suffix]; lo=Vector(tuple(min(v.co[i] for v in eye.data.vertices) for i in range(3))); hi=Vector(tuple(max(v.co[i] for v in eye.data.vertices) for i in range(3))); c=(lo+hi)/2
        bone('eye.'+suffix,c,c+Vector((0,-.05,0)),'head')
    bpy.ops.object.mode_set(mode='OBJECT')
    deform=data.collections.new('Body / FK'); fingers=data.collections.new('Fingers / FK'); face=data.collections.new('Head and eyes'); root=data.collections.new('Root')
    for b in data.bones:
        col=root if b.name=='root' else fingers if any(b.name.startswith(x+'_') for x in DIGITS) else face if b.name in ('head','neck') or b.name.startswith('eye.') else deform
        col.assign(b)
        b.color.palette='THEME03' if b.name.endswith('.L') else 'THEME04' if b.name.endswith('.R') else 'THEME02'
    for pb in rig.pose.bones: pb.rotation_mode='XYZ'
    rig['instructions']='Pose Mode: rotate FK bones. Fingers use local X for curling. Root moves entire character. RESET: Alt+G, Alt+R, Alt+S. Rest pose is T-pose. No IK constraints baked into export.'
    return rig

def install_armature(obj,rig):
    obj.parent=rig
    mods=[m for m in obj.modifiers if m.type=='ARMATURE']
    if mods: mod=mods[0]
    else: mod=obj.modifiers.new('Skin / game skeleton','ARMATURE')
    mod.object=rig; mod.use_deform_preserve_volume=False
    select(obj); bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)

def point_segment(co,a,b):
    axis=b-a; t=max(0,min(1,(co-a).dot(axis)/axis.length_squared)); return (co-a-axis*t).length,t

def body_weights(body,rig):
    body.vertex_groups.clear(); select(body); rig.select_set(True); bpy.context.view_layer.objects.active=rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    deform={b.name for b in rig.data.bones if b.use_deform}
    groups={g.name:g for g in body.vertex_groups}
    for name in deform:
        if name not in groups: groups[name]=body.vertex_groups.new(name=name)
    by_index={g.index:g.name for g in body.vertex_groups}
    finger_assignments=0
    for v in body.data.vertices:
        weights={by_index[g.group]:g.weight for g in v.groups if by_index[g.group] in deform and g.weight>1e-6}
        x,y,z=v.co; suffix='L' if x>=0 else 'R'; co=Vector((abs(x),y,z))
        if abs(x)>.345:
            chains=[]
            for digit,points in DIGITS.items():
                distances=[point_segment(co,Vector(a),Vector(b))[0] for a,b in zip(points,points[1:])]
                chains.append((min(distances),digit))
            distance,digit=min(chains); points=[Vector(a) for a in DIGITS[digit]]
            # The dedicated digit chain prevents heat weights crossing narrow finger gaps.
            onset=.351 if digit=='thumb' else .375
            influence=smoothstep(onset-.017,onset+.012,abs(x))
            raw={}
            for i,(a,b) in enumerate(zip(points,points[1:]),1):
                d,t=point_segment(co,a,b); raw[f'{digit}_{i:02d}.{suffix}']=1/(d*d+.000016)**2
            total=sum(raw.values()); raw={n:w/total*influence for n,w in raw.items()}
            raw['hand.'+suffix]=1-influence
            weights=raw; finger_assignments+=1
        if not weights:
            # A deterministic safety fallback only for isolated heat-solver misses.
            closest=min((point_segment(v.co,b.head_local,b.tail_local)[0],b.name) for b in rig.data.bones if b.use_deform and not b.name.startswith('eye.'))
            weights={closest[1]:1}
        weights=dict(sorted(weights.items(),key=lambda x:x[1],reverse=True)[:4]); total=sum(weights.values())
        for g in list(v.groups): body.vertex_groups[g.group].remove([v.index])
        for name,value in weights.items():
            if value>1e-6: groups[name].add([v.index],value/total,'REPLACE')
    install_armature(body,rig)
    print('FINGER WEIGHT VERTICES',finger_assignments,flush=True)

def rigid_weights(obj,rig,name):
    obj.vertex_groups.clear(); group=obj.vertex_groups.new(name=name); group.add(list(range(len(obj.data.vertices))),1,'REPLACE'); install_armature(obj,rig)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_09_game_retopology_welded.blend'))
    rig=create_rig(); body_weights(bpy.data.objects['CHR_Body'],rig)
    for obj in meshes():
        if obj.name=='CHR_Body': continue
        if obj.name.startswith('CHR_Eye.'):
            rigid_weights(obj,rig,'eye.'+obj.name[-1]); continue
        if obj.name=='CHR_Neck':
            obj.vertex_groups.clear(); a=obj.vertex_groups.new(name='chest'); b=obj.vertex_groups.new(name='neck'); c=obj.vertex_groups.new(name='head')
            for v in obj.data.vertices:
                t=smoothstep(.578,.618,v.co.z); h=smoothstep(.631,.661,v.co.z)
                for g,w in [(a,1-t),(b,t*(1-h)),(c,t*h)]:
                    if w>1e-6:g.add([v.index],w,'REPLACE')
            install_armature(obj,rig)
        else: rigid_weights(obj,rig,'head')
    report={'bones':len(rig.data.bones),'deform_bones':sum(b.use_deform for b in rig.data.bones),'meshes':{}}
    for obj in meshes():
        sums=[sum(g.weight for g in v.groups) for v in obj.data.vertices]
        report['meshes'][obj.name]={'vertices':len(sums),'unweighted':sum(x<.999 for x in sums),'max_weight_sum_error':max(abs(x-1) for x in sums),'max_influences':max(len(v.groups) for v in obj.data.vertices)}
    (PROJECT/'output'/'game_skin_weights.json').write_text(json.dumps(report,indent=2)); print(report,flush=True)
    assert all(r['unweighted']==0 and r['max_influences']<=4 for r in report['meshes'].values())
    select(rig)
    checkpoint(10,'skeleton_skinning','Created FK game skeleton with calibrated three-finger-plus-thumb chains, eye bones and full body skinning. Weights normalized and limited to four influences; finger weights isolated by chain. Pose validation next.')

if __name__=='__main__': main()
