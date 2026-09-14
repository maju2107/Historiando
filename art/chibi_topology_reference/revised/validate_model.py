"""Run against the saved blend; validate only the actual character mesh."""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils.bvhtree import BVHTree

out=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(out/'Chibi_Topology_Corrigida.blend'))
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
region_faces=json.loads(obj['region_faces'])
finger_groups={side:[g.name for g in obj.vertex_groups if g.name.startswith('Finger / ') and g.name.endswith('.'+side)]
               for side in ('L','R')}
deformed=bm.copy()
deformed.verts.ensure_lookup_table()
deformed.faces.ensure_lookup_table()
bend=obj.data.shape_keys.key_blocks['Teste_joelho_L_60graus']
for v,p in zip(deformed.verts,bend.data):
    v.co=p.co
deformed.normal_update()
bend_tree=BVHTree.FromBMesh(deformed,epsilon=.000001)
bend_overlaps=[]
for a,b in bend_tree.overlap(bend_tree):
    if a<b and not set(deformed.faces[a].verts)&set(deformed.faces[b].verts):
        bend_overlaps.append([a,b])
bend_zero=[f.index for f in deformed.faces if f.calc_area()<1e-10]
bend_volume=deformed.calc_volume(signed=True)
deformed.free()
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
    'five_fingers_per_hand':{side:len(names)==5 for side,names in finger_groups.items()},
    'finger_vertex_groups':finger_groups,
    'perineum_bridge_quads':len(region_faces['Perineum bridge']),
    'patella_contour_quads_per_knee':{side:len(region_faces['Knee contour.'+side]) for side in ('L','R')},
    'knee_60_degree_test':{'nonadjacent_face_intersections':bend_overlaps,
                          'degenerate_faces':bend_zero,'signed_volume':bend_volume,
                          'saved_shape_key_value':bend.value},
    'packed_reference_images':[im.name for im in bpy.data.images if im.packed_file],
    'subdivision_disabled':not obj.modifiers[0].show_viewport and not obj.modifiers[0].show_render,
    'exports':{name:(out/name).stat().st_size for name in ('Chibi_Topology_Corrigida.glb','Chibi_Topology_Corrigida.obj')},
}
(out/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
bm.free()
assert report['all_quad_faces']
assert len(components)==1
assert not nonmanifold and not zero_faces and not asymmetric and not overlaps
assert report['signed_volume']>0 and report['finite_coordinates']
assert report['uv_layers'] and report['packed_reference_images']
assert len(report['packed_reference_images'])==4
assert all(report['five_fingers_per_hand'].values())
assert report['perineum_bridge_quads']==8
assert not bend_overlaps and not bend_zero and bend_volume>0 and bend.value==0
print('VALIDATION PASSED')
