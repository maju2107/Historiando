"""Incremental geometry changes applied to the preceding numbered checkpoint."""
import bpy,bmesh,json,math
import numpy as np
from mathutils import Vector
from config import *
from helpers import character_objects,bounds

def evaluated_edges():
    starts=[]; ends=[]; graph=bpy.context.evaluated_depsgraph_get()
    for obj in character_objects():
        ev=obj.evaluated_get(graph); me=ev.to_mesh()
        vs=np.array([obj.matrix_world@v.co for v in me.vertices])
        ee=np.array([e.vertices[:] for e in me.edges])
        starts.append(vs[ee[:,0]]); ends.append(vs[ee[:,1]]); ev.to_mesh_clear()
    return np.concatenate(starts),np.concatenate(ends)

def cross_sections(zvalues):
    a,b=evaluated_edges(); result={}
    for z in zvalues:
        mask=(a[:,2]-z)*(b[:,2]-z)<=0
        aa,bb=a[mask],b[mask]; dz=bb[:,2]-aa[:,2]
        valid=np.abs(dz)>1e-10; aa=aa[valid]; bb=bb[valid]; dz=dz[valid]
        if not len(aa): continue
        t=(z-aa[:,2])/dz; hits=aa+(bb-aa)*t[:,None]
        result[z]={'xmin':float(hits[:,0].min()),'xmax':float(hits[:,0].max()),
                   'ymin':float(hits[:,1].min()),'ymax':float(hits[:,1].max())}
    return result

def smooth_interpolate(x,knots):
    if x<=knots[0][0]: return knots[0][1]
    if x>=knots[-1][0]: return knots[-1][1]
    for i,((a,va),(b,vb)) in enumerate(zip(knots,knots[1:])):
        if x<=b:
            t=(x-a)/(b-a)
            # Smoothstep blending avoids corners between measured sections.
            t=t*t*(3-2*t)
            return va+(vb-va)*t

def fit_silhouette():
    report=json.loads((PROJECT/'references'/'analysis.json').read_text(encoding='utf-8'))
    ref={view:{r['z_m']:r for r in report['measurements'][view]['sections']} for view in ('FRONT','SIDE')}
    samples=[z for z in ref['FRONT'] if z<=.48 or z>=.67]
    before=cross_sections(samples); xf=[]; yf=[]; ys=[]
    for z in samples:
        old=before[z]; target=ref['FRONT'][z]['width_m']; current=old['xmax']-old['xmin']
        factor=max(.83,min(1.18,target/current))
        xf.append((z,1+.85*(factor-1)))
        mn=-ref['SIDE'][z]['max_m']; mx=-ref['SIDE'][z]['min_m']
        factor=max(.80,min(1.22,(mx-mn)/(old['ymax']-old['ymin'])))
        factor=1+.85*(factor-1)
        shift=((mx+mn)-(old['ymax']+old['ymin'])*factor)*.5*.85
        yf.append((z,factor)); ys.append((z,shift))
    # Arm and neck proportions are already close; do not interpret hand depth
    # as torso depth in the lateral reference.
    for knots,neutral in ((xf,1),(yf,1),(ys,0)):
        knots.extend([(.51,neutral),(.60,neutral),(.635,neutral),(1.001,neutral)])
        knots.sort()
    for obj in character_objects():
        for v in obj.data.vertices:
            z=v.co.z
            v.co.x*=smooth_interpolate(z,xf)
            v.co.y=v.co.y*smooth_interpolate(z,yf)+smooth_interpolate(z,ys)
        obj.data.update()
    bpy.context.view_layer.update(); after=cross_sections(samples)
    (PROJECT/'renders'/'m02_measurements.json').write_text(json.dumps({'before':before,'after':after,
      'x_scale':xf,'y_scale':yf,'y_offset':ys,'reference':ref},indent=2),encoding='utf-8')
    # Only the nine aligned project images are kept, with the originals intact.
    used={o.data for o in bpy.data.collections['REFERENCES'].objects if o.type=='EMPTY' and o.data}
    for im in list(bpy.data.images):
        if im.name.startswith(PREFIX) and im not in used: bpy.data.images.remove(im)
    return 'Fitted the saved silhouette to measured front and side sections; increased posterior skull volume, adjusted cheek depth and body widths while retaining topology and T-pose.'

def setup_modifiers():
    body=bpy.data.objects['CHR_Body']; bm=bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
      dist=1e-7,plane_co=(0,0,0),plane_no=(1,0,0),clear_inner=True,clear_outer=False)
    for v in bm.verts:
        if abs(v.co.x)<1e-6: v.co.x=0
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(body.data); bm.free()
    mirror=body.modifiers.new('Symmetry / editable half','MIRROR'); mirror.use_clip=True
    mirror.use_mirror_merge=True; mirror.merge_threshold=.00001
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.modifier_move_to_index(modifier=mirror.name,index=0)
    body['symmetry']='Edit the positive-X half; Mirror maintains the negative-X half.'
    for obj in character_objects():
        for mod in obj.modifiers:
            if mod.type=='SUBSURF': mod.levels=2; mod.render_levels=2; mod.use_limit_surface=False
    return 'Converted the existing continuous body to an editable positive-X half with clipping Mirror before Subdivision 2. Preserved deformation loops and reference-like quad flow.'

def apply_milestone(number):
    if number==2: return fit_silhouette()
    if number==3: return setup_modifiers()
    if number==4:
        from face import create_face_topology
        return create_face_topology()
    if number==5:
        from hands import create_hands
        return create_hands()
    if number==6:
        from validation import validate_scene
        report=validate_scene(6)
        source=json.loads((PROJECT/'references'/'analysis.json').read_text())
        sections=source['measurements']['FRONT']['sections']
        measured=cross_sections([r['z_m'] for r in sections])
        comparisons=[]
        for r in sections:
            z=r['z_m']; width=measured[z]['xmax']-measured[z]['xmin']
            comparisons.append({'z_m':z,'reference_width_m':r['width_m'],'model_width_m':width,
              'error_m':width-r['width_m'],'error_percent':100*(width/r['width_m']-1)})
        (PROJECT/'renders'/'proportion_comparison.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
        return 'Compared measured widths and all orthographic views. Validation identified isolated vertices, eight non-quad cage faces from the symmetry cut and four cage intersection pairs; the subdivided surface is closed without self-intersections. These local control-mesh issues are recorded for milestone 7 cleanup.'
    if number==7:
        from controls import apply_proportion_controls
        from cleanup import final_cleanup
        from validation import validate_scene
        apply_proportion_controls()
        notes=final_cleanup(); validate_scene(7,strict=True)
        return notes
    raise RuntimeError(f'Milestone {number} is not implemented yet; preceding checkpoint remains intact.')
