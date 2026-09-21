"""Isolated developer check; does not write the delivered blend or exports."""
import bpy, bmesh, sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
root = Path(__file__).resolve().parent
namespace = {'__file__': str(root/'build_character.py'), '__name__': 'leg_check'}
source = (root/'build_character.py').read_text(encoding='utf-8')
exec(compile(source.split('# Work in a convenient facial')[0], str(root/'build_character.py'), 'exec'), namespace)
sys.path.insert(0, str(root))
from refine_body import rebuild_legs
verts, faces, regions = (namespace[k] for k in ('verts', 'faces', 'regions'))
faces = rebuild_legs(verts, faces, regions, namespace['ns'])
mesh = bpy.data.meshes.new('leg module check')
mesh.from_pydata(verts, [], faces)
mesh.update()
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
coords = [v.co.copy() for v in mesh.vertices]
polys = [tuple(f.vertices) for f in mesh.polygons]
tree = BVHTree.FromPolygons(coords, polys)
overlap = [(a,b) for a,b in tree.overlap(tree) if a<b and not set(polys[a]).intersection(polys[b])]
bm = bmesh.new(); bm.from_mesh(mesh)
boundary = [e for e in bm.edges if e.is_boundary]
bad = [f for f in bm.faces if f.calc_area()<1e-10]
print('LEG_AUDIT', {'vertices':len(bm.verts),'faces':len(bm.faces),
                  'non_quads':sum(len(f.verts)!=4 for f in bm.faces),
                  'boundary_edges':len(boundary),'degenerate':len(bad),
                  'self_intersections':overlap[:20]})
assert len(boundary)==16, 'Expected only the neck boundary'
assert not bad and not overlap
assert all(len(f.verts)==4 for f in bm.faces)
bm.free()
obj = bpy.data.objects.new('Leg cage inspection', mesh)
namespace['model_group'].objects.link(obj)
for p in mesh.polygons: p.use_smooth=True
mod=obj.modifiers.new('Smooth reference surface','SUBSURF'); mod.levels=2
dg=bpy.context.evaluated_depsgraph_get()
ev=obj.evaluated_get(dg); evmesh=ev.to_mesh()
ecoords=[v.co.copy() for v in evmesh.vertices]
epolys=[tuple(f.vertices) for f in evmesh.polygons]
etree=BVHTree.FromPolygons(ecoords, epolys)
eoverlap=[(a,b) for a,b in etree.overlap(etree) if a<b and not set(epolys[a]).intersection(epolys[b])]
print('LEG_EVALUATED_INTERSECTIONS',len(eoverlap))
assert not eoverlap
ev.to_mesh_clear()
mat=bpy.data.materials.new('neutral');mat.diffuse_color=(.5,.53,.52,1)
obj.data.materials.append(mat)
obj.show_wire=True; obj.show_all_edges=True
cam_data=bpy.data.cameras.new('audit camera');cam=bpy.data.objects.new('audit camera',cam_data)
namespace['stage'].objects.link(cam)
cam.location=(0,-6,.64); target=Vector((0,0,.64))
if '--side' in sys.argv: cam.location=(6,0,.64)
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO';cam_data.ortho_scale=1.52
scene=bpy.context.scene;scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.render.resolution_x=1000;scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.filepath=str(root/'leg_audit.png')
if '--side' in sys.argv: scene.render.filepath=str(root/'leg_audit_side.png')
bpy.ops.render.render(write_still=True)
