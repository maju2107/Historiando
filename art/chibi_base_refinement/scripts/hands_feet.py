"""Add the missing fourth finger through a small local palm opening."""
import bpy,bmesh,math,json
from mathutils import Vector
from helpers import collection,meshes,sync_basis
from config import PROJECT

def add_missing_finger():
    obj=bpy.data.objects['CHR_Body']
    backup=obj.copy(); backup.data=obj.data.copy(); backup.name='SRC_Body_before_fourth_finger'
    collection('SOURCE_PARTS').objects.link(backup); backup.hide_render=True
    obj.shape_key_clear()
    bm=bmesh.new(); bm.from_mesh(obj.data); deform=bm.verts.layers.deform.verify()
    bm.faces.ensure_lookup_table(); bm.normal_update()
    desired=Vector((.366,.052,.574))
    candidates=[f for f in bm.faces if .34<f.calc_center_median().x<.395 and .54<f.calc_center_median().z<.61 and f.normal.y>.45]
    seed=min(candidates,key=lambda f:(f.calc_center_median()-desired).length)
    center=seed.calc_center_median(); patch={seed}; wave=[seed]
    while wave:
        f=wave.pop()
        for e in f.edges:
            for other in e.link_faces:
                if other in patch: continue
                if (other.calc_center_median()-center).length<.0095 and other.normal.y>.10:
                    patch.add(other); wave.append(other)
    boundary=[e for e in bm.edges if sum(f in patch for f in e.link_faces)==1]
    adjacency={}
    for e in boundary:
        a,b=e.verts; adjacency.setdefault(a,[]).append(b); adjacency.setdefault(b,[]).append(a)
    if any(len(v)!=2 for v in adjacency.values()): raise RuntimeError('Finger patch boundary is not a simple loop')
    loop=[next(iter(adjacency))]; prev=None
    while True:
        current=loop[-1]; nxt=next(v for v in adjacency[current] if v!=prev)
        if nxt==loop[0]: break
        loop.append(nxt); prev=current
        if len(loop)>len(adjacency): raise RuntimeError('Boundary traversal failed')
    if len(loop)!=len(adjacency) or len(loop)%2: raise RuntimeError('Need one even quad-compatible boundary')
    root=sum((v.co for v in loop),Vector())/len(loop); n=len(loop)
    angles=[math.atan2((v.co-root).z,(v.co-root).x) for v in loop]
    removed=len(patch); bmesh.ops.delete(bm,geom=list(patch),context='FACES_ONLY')
    for e in list(bm.edges):
        if not e.link_faces and e not in boundary: bm.edges.remove(e)
    for v in list(bm.verts):
        if not v.link_edges and v not in loop: bm.verts.remove(v)
    group=obj.vertex_groups.new(name='Added fourth finger.L')
    previous=loop; created=[]
    profiles=[((0,.005,0),.0100),((.008,.009,-.001),.0105),((.020,.013,-.003),.0103),
      ((.032,.015,-.005),.0098),((.043,.017,-.007),.0092),((.052,.018,-.009),.0082),
      ((.059,.018,-.010),.0055),((.062,.018,-.010),.0012)]
    for i,(offset,radius) in enumerate(profiles):
        pos=root+Vector(offset)
        if i==0: tangent=Vector((0,1,0))
        else:
            before=root+Vector(profiles[i-1][0]); after=root+Vector(profiles[min(i+1,len(profiles)-1)][0])
            tangent=(after-before).normalized()
        up=(Vector((0,0,1))-tangent*tangent.z).normalized(); across=tangent.cross(up).normalized()
        ring=[]
        for angle in angles:
            co=pos+across*(radius*math.cos(angle))+up*(radius*.88*math.sin(angle))
            v=bm.verts.new(co); v[deform][group.index]=1; ring.append(v); created.append(v)
        for k in range(n): j=(k+1)%n; bm.faces.new((previous[k],previous[j],ring[j],ring[k]))
        previous=ring
    tip=bm.verts.new(sum((v.co for v in previous),Vector())/n); tip[deform][group.index]=1; created.append(tip)
    for k in range(0,n,2): bm.faces.new((tip,previous[k],previous[(k+1)%n],previous[(k+2)%n]))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free(); obj.data.update()
    for p in obj.data.polygons: p.use_smooth=True
    obj['digits_per_hand']='Original thumb and three fingers retained; one smaller fourth finger attached locally. Mirror creates opposite side.'
    record={'original_hand':'3 long fingers and thumb','final_hand':'4 long fingers and thumb',
      'replaced_palm_faces':removed,'boundary_vertices':n,'added_vertices':len(created),'root':list(root),
      'preserved':'Original thumb, three fingers, wrist, arm, torso, pelvis, legs and feet remain in the same mesh.'}
    (PROJECT/'output'/'local_hand_change.json').write_text(json.dumps(record,indent=2))
    return record

def refine_hands_feet():
    record=add_missing_finger()
    return 'Kept the original thumb, three existing fingers, palm, wrist and feet. Added the missing fourth finger through a small quad palm patch; mirrored the addition. Feet retain the source shape with measured width/depth and leg-length refinements.'
