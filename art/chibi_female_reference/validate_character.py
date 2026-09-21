import bpy,bmesh,json,math
from pathlib import Path
from mathutils import kdtree
from mathutils.bvhtree import BVHTree
out=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(out/'Chibi_Feminina.blend'))
body=bpy.data.objects['Chibi - corpo e cabeca']
def inspect(mesh):
    bm=bmesh.new(); bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    pending=set(bm.verts); components=[]
    while pending:
        stack=[pending.pop()]; count=0
        while stack:
            v=stack.pop(); count+=1
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in pending: pending.remove(other); stack.append(other)
        components.append(count)
    tree=BVHTree.FromBMesh(bm,epsilon=1e-7); intersections=[]
    for a,b in tree.overlap(tree):
        if a<b and not set(bm.faces[a].verts)&set(bm.faces[b].verts): intersections.append([a,b])
    kd=kdtree.KDTree(len(bm.verts))
    for v in bm.verts: kd.insert(v.co,v.index)
    kd.balance()
    symmetry=max(kd.find((-v.co.x,v.co.y,v.co.z))[2] for v in bm.verts)
    report={'vertices':len(bm.verts),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),
            'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
            'degenerate_faces':[f.index for f in bm.faces if f.calc_area()<1e-10],
            'components':components,'self_intersections':intersections,'signed_volume':bm.calc_volume(signed=True),
            'max_symmetry_error':symmetry,'finite_coordinates':all(math.isfinite(c) for v in bm.verts for c in v.co)}
    bm.free(); return report
report={'blend_reopened':True,'body_control':inspect(body.data)}
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
report['body_subdivision']=inspect(me); ev.to_mesh_clear()
report['parts']={}
for obj in bpy.data.collections['01 · MODEL'].objects:
    if obj.type!='MESH': continue
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
    bm=bmesh.new(); bm.from_mesh(me)
    report['parts'][obj.name]={'control_faces':len(obj.data.polygons),'evaluated_faces':len(me.polygons),
         'uv_layers':len(obj.data.uv_layers),'evaluated_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)}
    bm.free(); ev.to_mesh_clear()
report['references']={im.name:list(im.size) for im in bpy.data.images if im.packed_file}
report['exports']={name:(out/name).stat().st_size for name in ('Chibi_Feminina.blend','Chibi_Feminina.glb','Chibi_Feminina.obj')}
export_scene=bpy.data.scenes.new('Verificacao da exportacao GLB')
bpy.context.window.scene=export_scene
bpy.ops.import_scene.gltf(filepath=str(out/'Chibi_Feminina.glb'))
imported=[o for o in export_scene.objects if o.type=='MESH']
report['glb_reimport']={'mesh_objects':len(imported),'triangles':sum(len(o.data.polygons) for o in imported),
                      'all_have_uvs':all(len(o.data.uv_layers)>0 for o in imported),
                      'all_have_materials':all(len(o.data.materials)>0 for o in imported)}
(out/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
for key in ('body_control','body_subdivision'):
    r=report[key]
    assert not r['nonmanifold_edges'] and not r['degenerate_faces'] and not r['self_intersections'],key
    assert r['signed_volume']>0 and r['max_symmetry_error']<1e-5 and len(r['components'])==1,key
    assert r['finite_coordinates'] and r['quads']==r['faces'],key
assert len(report['references'])==9
assert all(p['uv_layers'] and not p['evaluated_nonmanifold_edges'] for p in report['parts'].values())
assert len(imported)==13 and report['glb_reimport']['all_have_uvs'] and report['glb_reimport']['all_have_materials']
print('VALIDATION PASSED')
