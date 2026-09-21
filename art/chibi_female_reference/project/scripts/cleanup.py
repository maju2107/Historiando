"""Local cage repairs, UVs, normals and final scale normalization."""
import bpy,bmesh,math
from mathutils import Vector
from helpers import character_objects,bounds
from face import group_vertices

def final_cleanup():
    obj=bpy.data.objects['CHR_Body']
    # Separate the exterior socket support ring from the adjacent cheek quad.
    ring=group_vertices(obj,'Head / eyelids & sockets.L')
    first,last=min(v.index for v in ring),max(v.index for v in ring)
    if last-first+1!=112: raise RuntimeError('Unexpected socket patch extent')
    center_x=sum(v.co.x for v in list(obj.data.vertices)[first+32:first+48])/16
    for row in range(3):
        for v in list(obj.data.vertices)[first+16*row:first+16*(row+1)]:
            amount=(1,1,.5)[row]
            v.co.y-=.0028*amount
            v.co.x=center_x+(v.co.x-center_x)*(1-.012*amount)
    bm=bmesh.new(); bm.from_mesh(obj.data); deform=bm.verts.layers.deform.verify()
    group=obj.vertex_groups['Finger / thumb.L'].index
    thumb={v for v in bm.verts if v[deform].get(group,0)>.1}
    roots={v for v in thumb if any(e.other_vert(v) not in thumb for e in v.link_edges)}
    distance={v:0 for v in roots}; wave=list(roots)
    while wave:
        v=wave.pop(0)
        for e in v.link_edges:
            w=e.other_vert(v)
            if w in thumb and w not in distance: distance[w]=distance[v]+1; wave.append(w)
    for level in sorted(set(distance.values())):
        vertices=[v for v,d in distance.items() if d==level]
        center=sum((v.co for v in vertices),Vector())/len(vertices)
        t=min(1,level/7); shrink=.80+.20*t
        shift=Vector((0,-.0045*(1-t)**2,0))
        for v in vertices: v.co=center+(v.co-center)*shrink+shift
    isolated=[v for v in bm.verts if not v.link_faces]
    if isolated: bmesh.ops.delete(bm,geom=isolated,context='VERTS')
    # Split only symmetry-boundary edges of four cut triangles. The inserted
    # centerline support points make quad faces on the editable half.
    seam=[]
    for f in bm.faces:
        if len(f.verts)==3:
            edge=next((e for e in f.edges if all(abs(v.co.x)<1e-7 for v in e.verts)),None)
            if edge is None: raise RuntimeError('Non-seam triangle needs explicit review')
            seam.append(edge)
    if seam: bmesh.ops.subdivide_edges(bm,edges=seam,cuts=1,use_grid_fill=False)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free(); obj.data.update()
    # Real-world scale is verified from the evaluated surface, including Mirror.
    bpy.context.view_layer.update(); lo,hi=bounds(); factor=1/(hi[2]-lo[2]); floor=lo[2]
    for part in character_objects():
        for v in part.data.vertices:
            v.co.x*=factor; v.co.y*=factor; v.co.z=(v.co.z-floor)*factor
        for mod in part.modifiers:
            if mod.type=='SOLIDIFY': mod.thickness*=factor
        bm=bmesh.new(); bm.from_mesh(part.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(part.data); bm.free()
        for f in part.data.polygons: f.use_smooth=True
        bpy.ops.object.select_all(action='DESELECT'); part.select_set(True); bpy.context.view_layer.objects.active=part
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(64),island_margin=.015)
        bpy.ops.object.mode_set(mode='OBJECT')
    return 'Removed isolated vertices, converted symmetry-cut triangles to quads with centerline support points, separated thumb/palm and cheek/socket cage faces, recalculated normals, refreshed UVs and set the evaluated height to exactly 1 m with soles at Z=0.'
