"""Final local repairs and validation of the preserved FBX model."""
import bpy,bmesh,json,math,shutil,cmath
import numpy as np
from mathutils import Vector
from config import PROJECT
from helpers import meshes,collection,sync_basis,aim
from topology import relax_surface
from head_refinement import smoothstep,create_eyebrows

def repair_finger_root():
    obj=bpy.data.objects['CHR_Body']; idx=obj.vertex_groups['Added fourth finger.L'].index
    vs=[v for v in obj.data.vertices if any(g.group==idx for g in v.groups)]
    ids={v.index for v in vs}; adjacency={v.index:[] for v in obj.data.vertices}
    for edge in obj.data.edges:
        a,b=edge.vertices; adjacency[a].append(b); adjacency[b].append(a)
    roots={i for i in ids if any(j not in ids for j in adjacency[i])}
    first=[min(roots)]; previous=None
    while True:
        current=first[-1]; nxt=next(j for j in adjacency[current] if j in roots and j!=previous)
        if nxt==first[0]: break
        first.append(nxt); previous=current
    rings=[first]; previous=set()
    while len(rings)<8:
        current=set(rings[-1]); following=[]
        for i in rings[-1]:
            following.append(next(j for j in adjacency[i] if j in ids and j not in current and j not in previous))
        previous=current; rings.append(following)
    if any(len(set(r))!=12 for r in rings): raise RuntimeError('Unexpected finger ring connectivity')
    tip_id=next(i for i in ids if i not in {j for ring in rings for j in ring})
    root=Vector(json.loads((PROJECT/'output'/'local_hand_change.json').read_text())['root'])
    source_angles=[]
    for i in rings[0]:
        boundary=obj.data.vertices[next(j for j in adjacency[i] if j not in ids)]
        source_angles.append(math.atan2((boundary.co.z-root.z)/.88,boundary.co.x-root.x))
    turn=sum(math.atan2(math.sin(b-a),math.cos(b-a)) for a,b in zip(source_angles,source_angles[1:]+source_angles[:1]))
    sign=1 if turn>0 else -1
    phase=cmath.phase(sum(cmath.exp(1j*(a-sign*k*math.tau/12)) for k,a in enumerate(source_angles)))
    # Even angular order avoids folding the narrow source patch's concave
    # boundary angles into every subsequent finger ring.
    angles=[phase+sign*k*math.tau/12 for k in range(12)]
    profiles=[((0,.010,0),.0100),((.007,.020,-.001),.0112),((.020,.026,-.003),.0120),
      ((.032,.027,-.005),.0120),((.043,.027,-.007),.0115),((.052,.027,-.009),.0102),
      ((.059,.027,-.010),.0068),((.062,.027,-.010),.0015)]
    for i,(offset,radius) in enumerate(profiles):
        pos=root+Vector(offset)
        if i==0: tangent=Vector((0,1,0))
        else: tangent=(Vector(profiles[min(i+1,7)][0])-Vector(profiles[i-1][0])).normalized()
        up=(Vector((0,0,1))-tangent*tangent.z).normalized(); across=tangent.cross(up).normalized()
        for vertex_index,angle in zip(rings[i],angles): obj.data.vertices[vertex_index].co=pos+across*(radius*math.cos(angle))+up*(radius*.88*math.sin(angle))
    obj.data.vertices[tip_id].co=root+Vector(profiles[-1][0])
    # Redistribute width across all four fingers, keeping their source shapes
    # and connectivity. This is an invertible cross-sectional compression.
    for v in obj.data.vertices:
        amount=smoothstep(.29,.36,abs(v.co.x)); v.co.y=-.015+(v.co.y+.015)*(1-.14*amount)
    obj.data.update()

def local_repairs():
    for obj in meshes():
        for mod in obj.modifiers:
            if mod.type=='MIRROR': mod.bisect_threshold=1e-7; mod.merge_threshold=1e-7
    neck=bpy.data.objects['CHR_Neck']
    weights=np.array([smoothstep(.642,.658,v.co.z) for v in neck.data.vertices])
    relax_surface(neck,100,weights); sync_basis()
    repair_finger_root()
    for obj in list(meshes()):
        if obj.name.startswith('CHR_Eyebrow'): bpy.data.objects.remove(obj,do_unlink=True)
    create_eyebrows(); sync_basis()
    for obj in meshes():
        if obj.name.startswith('CHR_Eyebrow'):
            bm=bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free()
    return 'Fixed the local fourth-finger attachment and original hidden neck folds; tightened Mirror thresholds for dense source topology and restored solid eyebrow thickness.'

def setup_final_materials():
    mat=bpy.data.materials.get('MAT_ReferenceClay') or bpy.data.materials.new('MAT_ReferenceClay')
    mat.use_nodes=True; bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(.46,.47,.47,1); bs.inputs['Roughness'].default_value=.85
    bs.inputs['Specular IOR Level'].default_value=.25
    for obj in meshes():
        obj.data.materials.clear(); obj.data.materials.append(mat)
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED'; scene.render.threads=6; scene.view_settings.view_transform='Standard'
    scene.world.use_nodes=True; node=scene.world.node_tree.nodes['Background']; node.inputs['Color'].default_value=(.045,.045,.045,1); node.inputs['Strength'].default_value=.7
    col=collection('VALIDATION')
    for name,loc,energy,size in [('Key',(-1,-1.5,2),36,1.2),('Fill',(1,-1,1.5),23,1.2),('Rim',(.5,1.2,1.5),29,1.2)]:
        lamp=bpy.data.lights.new('LGT_'+name,'AREA'); lamp.energy=energy; lamp.size=size
        obj=bpy.data.objects.new('LGT_'+name,lamp); col.objects.link(obj); obj.location=loc; aim(obj,(0,0,.5)); obj.hide_set(True)

def prepare_uvs():
    sync_basis()
    for obj in meshes():
        if obj.data.uv_layers: continue
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.01); bpy.ops.object.mode_set(mode='OBJECT')

def finish_stage():
    notes=local_repairs()
    from validation import audit
    control=audit('final_control',False); smooth=audit('final_subdivision',True)
    if control['issues'] or smooth['issues']: raise RuntimeError('Local repairs need further review before final save.')
    prepare_uvs(); setup_final_materials()
    return notes
