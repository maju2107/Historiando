"""Refine the saved head's eyes, cartilage and crown without rebuilding it."""
import bpy,bmesh,json,math
from mathutils import Vector
from config import PROJECT
from modeling import smooth_interpolate

def old_to_current(co):
    scene=bpy.context.scene; scale=scene['import_scale']; floor=scene['import_floor']
    x,y,z=co; x*=scale; y*=scale; z=(z-floor)*scale
    curves=json.loads((PROJECT/'renders'/'m02_measurements.json').read_text())
    return Vector((x*smooth_interpolate(z,curves['x_scale']),
                   y*smooth_interpolate(z,curves['y_scale'])+smooth_interpolate(z,curves['y_offset']),z))

def head_point(x,y,z):
    return old_to_current((x*1.09,y*1.03,2.30+(z-2.465)*1.30/1.135))

def original_head_point(co):
    scene=bpy.context.scene; scale=scene['import_scale']; floor=scene['import_floor']
    curves=json.loads((PROJECT/'renders'/'m02_measurements.json').read_text())
    x,y,z=co
    x/=smooth_interpolate(z,curves['x_scale'])
    y=(y-smooth_interpolate(z,curves['y_offset']))/smooth_interpolate(z,curves['y_scale'])
    return Vector((x/scale/1.09,y/scale/1.03,2.465+((z/scale+floor)-2.30)*1.135/1.30))

def group_vertices(obj,name):
    group=obj.vertex_groups.get(name)
    if not group: return []
    return [v for v in obj.data.vertices if any(g.group==group.index and g.weight>.1 for g in v.groups)]

def create_eyes():
    for side,label in ((1,'L'),(-1,'R')):
        obj=bpy.data.objects['CHR_Eye.'+label]; vertices=[]; faces=[]; n=32
        phis=(.020,.38,.75,1.08,1.38,1.70,2.04,2.37,2.70,2.97,3.12)
        for phi in phis:
            for k in range(n):
                a=math.tau*k/n; dx=.164*math.sin(phi)*math.cos(a)
                z=2.945+.156*math.sin(phi)*math.sin(a)
                y=-.468-.076*math.cos(phi)+side*.16*dx+.003*math.sin(phi)**4
                vertices.append(head_point(side*.268+dx,y,z))
        for row in range(len(phis)-1):
            for k in range(n):
                j=(k+1)%n; faces.append((row*n+k,row*n+j,(row+1)*n+j,(row+1)*n+k))
        for start in (0,(len(phis)-1)*n):
            for k in range(1,n-2,2): faces.append((start,start+k,start+k+1,start+k+2))
        data=bpy.data.meshes.new(obj.name+' fitted radial mesh'); data.from_pydata(vertices,[],faces); data.update()
        materials=list(obj.data.materials); old=obj.data; obj.data=data
        for mat in materials: data.materials.append(mat)
        bm=bmesh.new(); bm.from_mesh(data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(data); bm.free()
        for p in data.polygons: p.use_smooth=True
        obj['eye_fit']='Shallow radial ellipsoid; outer edge seats behind eyelid opening.'
        if old.users==0: bpy.data.meshes.remove(old)

def create_ears():
    obj=bpy.data.objects['CHR_Body']; verts=group_vertices(obj,'Head / ears.L')
    # Some inherited group weights were omitted by float32 coordinate lookup
    # in the earlier generator. The preserved ear patch is still contiguous.
    first,last=min(v.index for v in verts),max(v.index for v in verts)
    if last-first+1!=72: raise RuntimeError('Unexpected saved ear layout span')
    verts=list(obj.data.vertices)[first:last+1]
    obj.vertex_groups['Head / ears.L'].add(list(range(first,last+1)),1,'REPLACE')
    center=Vector((.624,0,2.847)); axis=Vector((.65,.760,0)); normal=Vector((.760,-.65,0))
    angles=[]
    for v in verts[:12]:
        raw=original_head_point(v.co); sine=max(-1,min(1,(raw.z-center.z)/.183))
        u=(raw-center).dot(axis)
        cosine=(u-.09*.183*sine)/(.122*(1+.1*sine))
        angles.append(math.atan2(sine,cosine))
    rings=((.122,.183,0),(.110,.176,.032),(.080,.145,.057),
           (.053,.106,-.006),(.031,.059,-.040),(.014,.027,-.046))
    for row,(rx,rz,depth) in enumerate(rings):
        for k,a in enumerate(angles):
            sine=math.sin(a); u=rx*math.cos(a)*(1+.10*sine)+.09*rz*sine
            co=center+axis*u+Vector((0,0,rz*sine))+normal*depth
            if row in (1,2): co+=normal*(.008*max(0,-sine)**2)
            if row>=3:
                angle=math.atan2(math.sin(a-math.pi),math.cos(a-math.pi))
                tragus=math.exp(-(angle/.80)**2)*(rx/.053)
                co+=normal*(.100*tragus)+axis*(.027*tragus+.004)
            verts[row*12+k].co=head_point(*co)
    # Hold the posterior crown center measured in the side view through the
    # apex, instead of letting the last fitted row swing back toward the neck.
    curves=json.loads((PROJECT/'renders'/'m02_measurements.json').read_text())
    offset=smooth_interpolate(.97,curves['y_offset'])
    for v in obj.data.vertices:
        t=max(0,min(1,(v.co.z-.97)/.031)); t=t*t*(3-2*t)
        v.co.y+=offset*t
    obj.data.update()

def create_face_topology():
    create_eyes(); create_ears(); bpy.context.view_layer.update()
    return 'Fitted shallow radial eye surfaces behind eyelids, refined rolled helix/concha/tragus in existing ear loops, and continued posterior skull curvature through the crown. Head mesh retained.'
