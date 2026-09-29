"""Measured, continuous deformations of the imported vertices; no replacement."""
import bpy,json,math
import numpy as np
from config import *
from helpers import meshes

BODY_HEIGHT_MAP=[(0,0),(.065,.065),(.13,.165),(.17,.213),(.300,.341),(.375,.396),(.45,.46),(.55,.561),(.64,.64)]
HEAD_HEIGHT_MAP=[(.6446,.638),(.68,.684),(.704,.710),(.741,.752),(.78646,.791),(.86,.86),(1,1)]

def interp(x,knots):
    # Monotone cubic Hermite interpolation: continuous tangents remove the
    # horizontal ridges introduced by piecewise-linear section fitting.
    xx=[p[0] for p in knots]; yy=[p[1] for p in knots]
    if x<=xx[0]: return yy[0]
    if x>=xx[-1]: return yy[-1]
    slopes=[(yy[i+1]-yy[i])/(xx[i+1]-xx[i]) for i in range(len(xx)-1)]
    tangents=[slopes[0]]
    for a,b in zip(slopes,slopes[1:]): tangents.append(2*a*b/(a+b) if a*b>0 else 0)
    tangents.append(slopes[-1])
    i=next(i for i in range(len(xx)-1) if x<=xx[i+1]); h=xx[i+1]-xx[i]; t=(x-xx[i])/h
    return (2*t**3-3*t*t+1)*yy[i]+(t**3-2*t*t+t)*h*tangents[i]+(-2*t**3+3*t*t)*yy[i+1]+(t**3-t*t)*h*tangents[i+1]

def section_bounds(obj,z):
    co=np.array([v.co[:] for v in obj.data.vertices]); edges=np.array([e.vertices[:] for e in obj.data.edges])
    a,b=co[edges[:,0]],co[edges[:,1]]; dz=b[:,2]-a[:,2]
    mask=((a[:,2]-z)*(b[:,2]-z)<=0)&(abs(dz)>1e-9)
    a,b,dz=a[mask],b[mask],dz[mask]
    hit=a+(b-a)*((z-a[:,2])/dz)[:,None]
    return hit.min(axis=0),hit.max(axis=0)

def preserve_basis(obj):
    if obj.data.shape_keys is None:
        obj.shape_key_add(name='Basis')
        key=obj.shape_key_add(name='Imported form / normalized'); key.value=0
        obj['preservation_note']='Imported normalized shape stored as an inactive shape key. Refinement changes coordinates, not the original face connectivity.'

def fit_body():
    obj=bpy.data.objects['CHR_Body']; preserve_basis(obj)
    for v in obj.data.vertices: v.co.z=interp(v.co.z,BODY_HEIGHT_MAP)
    obj.data.update()
    ref=json.loads((PROJECT/'references'/'analysis.json').read_text())
    section=ref['measurements']['FRONT']['sections']; xcurve=[]; depthcurve=[]; offset=[]
    side={r['z_m']:r for r in ref['measurements']['SIDE']['sections']}
    for r in section:
        z=r['z_m']
        if z>.48: continue
        lo,hi=section_bounds(obj,z); xcurve.append((z,min(1.45,max(.8,r['width_m']/(hi[0]-lo[0])))))
        # The source side view points right; forward in this scene is -Y.
        target_min=-side[z]['max_m']; target_max=-side[z]['min_m']
        factor=min(1.35,max(.8,(target_max-target_min)/(hi[1]-lo[1])))
        depthcurve.append((z,factor)); offset.append((z,((target_max+target_min)-(hi[1]+lo[1])*factor)/2))
    xcurve.extend([(.51,1),(.64,1)]); depthcurve.extend([(.51,1),(.64,1)]); offset.extend([(.51,0),(.64,0)])
    for v in obj.data.vertices:
        x,y,z=v.co
        v.co.x=x*interp(z,xcurve); v.co.y=y*interp(z,depthcurve)+interp(z,offset)
        if abs(x)>.09:
            # Shorter reach, retaining the user's palm and individual fingers.
            v.co.x=math.copysign(.09+(abs(v.co.x)-.09)*.927,x)
    # Width fitting above must retain the reference lower-leg spread. Reach
    # correction affects only the horizontal arms, not the legs.
    for v in obj.data.vertices:
        if v.co.z<.50 and abs(v.co.x)>.09: v.co.x=math.copysign(.09+(abs(v.co.x)-.09)/.927,v.co.x)
    obj.data.update()
    return {'body_z_mapping':BODY_HEIGHT_MAP,'width_scale':xcurve,'depth_scale':depthcurve,'depth_offset':offset}

def fit_head_block():
    for obj in meshes():
        if obj.name=='CHR_Body': continue
        preserve_basis(obj)
        for v in obj.data.vertices:
            x,y,z=v.co
            if obj.name=='CHR_Neck':
                # Keep the already close cylindrical neck; the hidden ends
                # continue inside the imported head and torso.
                v.co.x*=1.05; v.co.y*=.88
                continue
            v.co.z=interp(z,HEAD_HEIGHT_MAP)
            v.co.x*=HEAD_WIDTH/.31354776
            v.co.y=(y-.025)*.90+.025
        obj.data.update()

def fix_proportions():
    data=fit_body(); fit_head_block()
    (PROJECT/'output'/'proportion_deformations.json').write_text(json.dumps(data,indent=2))
    bpy.context.scene['preservation']='All source character mesh vertices and face connectivity retained through proportion correction. Temporary hip block is archived separately.'
    return 'Reshaped original vertices: raised crotch and knees, fitted leg/waist/hip widths and side depths to references, shortened arm reach, broadened skull and reduced head depth. Retained original body, head, ears, eyes, eyelids, neck and their topology.'
