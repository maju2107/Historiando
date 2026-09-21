"""Named proportion controls for editing the latest saved mesh, without rebuild."""
import bpy,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import config
from helpers import character_objects,bounds

DEFAULTS={'TOTAL_HEIGHT':1.,'HEAD_HEIGHT':.365,'HEAD_WIDTH':.350,'HEAD_DEPTH':.340,
 'EYE_DIAMETER':.090,'EYE_SPACING':.155,'SHOULDER_WIDTH':.170,'SHOULDER_HEIGHT':.559,
 'TORSO_LENGTH':.211,'WAIST_WIDTH':.128,'HIP_WIDTH':.185,'LEG_LENGTH':.341,
 'KNEE_HEIGHT':.213,'FOOT_WIDTH':.139,'FOOT_LENGTH':.190,'ARM_LENGTH':.310,'HAND_LENGTH':.153}

def apply_proportion_controls():
    scene=bpy.context.scene
    old=json.loads(scene.get('proportion_controls',json.dumps(DEFAULTS)))
    new={name:getattr(config,name) for name in DEFAULTS}
    if any(v<=0 for v in new.values()): raise ValueError('All dimensions must be positive')
    scene['proportion_controls']=json.dumps(new)
    if old==new: return
    ratio={k:new[k]/old[k] for k in new}
    def gate(z,a,b):
        t=max(0,min(1,(z-a)/(b-a))); return t*t*(3-2*t)
    for obj in character_objects():
        eye=obj.name.startswith(('CHR_Eye.','CHR_Eyelid.','CHR_Eyelash'))
        for v in obj.data.vertices:
            x,y,z=v.co; ax=abs(x); sign=1 if x>=0 else -1
            h=gate(z,.62,.665)
            x*=1+h*(ratio['HEAD_WIDTH']-1)
            y=.025+(y-.025)*(1+h*(ratio['HEAD_DEPTH']-1))
            dz=h*max(0,z-.635)*(ratio['HEAD_HEIGHT']-1)
            dz+=min(z,.341)*(ratio['LEG_LENGTH']-1)
            dz+=max(0,min(z-.341,.211))*(ratio['TORSO_LENGTH']-1)
            dz+=(new['KNEE_HEIGHT']-old['KNEE_HEIGHT'])*math.exp(-((z-.213)/.05)**2)
            body_weight=1-h
            x*=1+body_weight*(ratio['WAIST_WIDTH']-1)*math.exp(-((z-.465)/.045)**2)
            x*=1+body_weight*(ratio['HIP_WIDTH']-1)*math.exp(-((z-.375)/.050)**2)
            shoulder=math.exp(-((z-.559)/.045)**4)
            x*=1+(ratio['SHOULDER_WIDTH']-1)*shoulder*min(1,.08/max(ax,.001))
            dz+=(new['SHOULDER_HEIGHT']-old['SHOULDER_HEIGHT'])*shoulder
            if .50<z<.61 and ax>.075:
                arm=.075+(min(ax,.29)-.075)*ratio['ARM_LENGTH']+max(0,ax-.29)*ratio['HAND_LENGTH']
                x+=sign*(arm-ax)
            foot=1-gate(z,.075,.15)
            x+=sign*(ax-.080)*(ratio['FOOT_WIDTH']-1)*foot
            y=-.012+(y+.012)*(1+foot*(ratio['FOOT_LENGTH']-1))
            if eye:
                cx=sign*old['EYE_SPACING']/2
                x=cx+(x-cx)*ratio['EYE_DIAMETER']+sign*(new['EYE_SPACING']-old['EYE_SPACING'])/2
                dz+=(z-.791)*(ratio['EYE_DIAMETER']-1)
            v.co=(x,y,z+dz)
        obj.data.update()
    bpy.context.view_layer.update(); low,high=bounds(); scale=new['TOTAL_HEIGHT']/(high[2]-low[2])
    for obj in character_objects():
        for v in obj.data.vertices: v.co=(v.co.x*scale,v.co.y*scale,(v.co.z-low[2])*scale)

if __name__=='__main__':
    import argparse
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); ns=p.parse_args(args)
    dest=Path(ns.output).resolve()
    if dest.exists(): raise RuntimeError('Choose a new output filename to preserve previous work')
    state=json.loads((config.PROJECT/'progress.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=state['latest_checkpoint'])
    apply_proportion_controls()
    from helpers import rebuild_wire
    rebuild_wire(); bpy.ops.wm.save_as_mainfile(filepath=str(dest))
