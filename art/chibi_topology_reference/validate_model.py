"""Run against the saved blend; validate only the actual character mesh."""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils.bvhtree import BVHTree

out=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(out/'Chibi_Reference_Base.blend'))
obj=bpy.data.objects['Chibi Base · editable mesh']
mesh=obj.data
bm=bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()
nonmanifold=[e.index for e in bm.edges if not e.is_manifold]
zero_faces=[f.index for f in bm.faces if f.calc_area()<1e-10]
components=[]
pending=set(bm.verts)
while pending:
    stack=[pending.pop()]
    count=0
    while stack:
        v=stack.pop()
        count+=1
        for edge in v.link_edges:
            other=edge.other_vert(v)
            if other in pending:
                pending.remove(other)
                stack.append(other)
    components.append(count)
coords={tuple(round(c,5) for c in v.co) for v in bm.verts}
asymmetric=[v.index for v in bm.verts if (round(-v.co.x,5),round(v.co.y,5),round(v.co.z,5)) not in coords]
tree=BVHTree.FromBMesh(bm,epsilon=0.000001)
overlaps=[]
for a,b in tree.overlap(tree):
    if a>=b or set(bm.faces[a].verts)&set(bm.faces[b].verts):
        continue
    overlaps.append([a,b])
mesh.calc_loop_triangles()
report={
    'blend_reopened':True,
    'object':obj.name,
    'vertices':len(mesh.vertices),
    'edges':len(mesh.edges),
    'faces':len(mesh.polygons),
    'triangles':len(mesh.loop_triangles),
    'all_quad_faces':all(len(p.vertices)==4 for p in mesh.polygons),
    'connected_components':components,
    'nonmanifold_edges':nonmanifold,
    'degenerate_faces':zero_faces,
    'asymmetric_vertices':asymmetric,
    'nonadjacent_face_intersections':overlaps,
    'signed_volume':bm.calc_volume(signed=True),
    'finite_coordinates':all(math.isfinite(c) for v in bm.verts for c in v.co),
    'height':round(obj.dimensions.z,4),
    'uv_layers':len(mesh.uv_layers),
    'packed_reference_images':[im.name for im in bpy.data.images if im.packed_file],
    'subdivision_disabled':not obj.modifiers[0].show_viewport and not obj.modifiers[0].show_render,
    'exports':{name:(out/name).stat().st_size for name in ('Chibi_Reference_Base.glb','Chibi_Reference_Base.obj')},
}
(out/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
bm.free()
assert report['all_quad_faces']
assert len(components)==1
assert not nonmanifold and not zero_faces and not asymmetric and not overlaps
assert report['signed_volume']>0 and report['finite_coordinates']
assert report['uv_layers'] and report['packed_reference_images']
print('VALIDATION PASSED')
