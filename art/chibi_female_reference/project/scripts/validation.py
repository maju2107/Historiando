"""Inspect the editable cage, mirrored mesh and final subdivision independently."""
import bpy,bmesh,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import kdtree
from mathutils.bvhtree import BVHTree
from config import PROJECT
from helpers import character_objects,bounds

def inspect_mesh(mesh,self_intersections=True):
    bm=bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    kd=kdtree.KDTree(len(bm.verts))
    for v in bm.verts: kd.insert(v.co,v.index)
    kd.balance()
    duplicates=[]
    for v in bm.verts:
        duplicates.extend((v.index,j) for _,j,d in kd.find_range(v.co,1e-7) if j>v.index)
    symmetry=max(kd.find((-v.co.x,v.co.y,v.co.z))[2] for v in bm.verts)
    pending=set(bm.verts); components=[]
    while pending:
        todo=[pending.pop()]; n=0
        while todo:
            v=todo.pop(); n+=1
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in pending: pending.remove(other); todo.append(other)
        components.append(n)
    intersections=[]
    if self_intersections:
        tree=BVHTree.FromBMesh(bm,epsilon=1e-9)
        intersections=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)]
    report={'vertices':len(bm.verts),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),
      'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
      'inconsistent_normal_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
      'degenerate_faces':[f.index for f in bm.faces if f.calc_area()<1e-12],
      'duplicate_vertices':duplicates,'self_intersections':intersections,'components':components,
      'signed_volume':bm.calc_volume(signed=True),'max_symmetry_error':symmetry}
    bm.free(); return report

def evaluate(obj,subdivision=True,check_intersections=True):
    states=[]
    for mod in obj.modifiers:
        if mod.type=='SUBSURF': states.append((mod,mod.show_viewport)); mod.show_viewport=subdivision
    bpy.context.view_layer.update(); ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh()
    result=inspect_mesh(mesh,check_intersections); ev.to_mesh_clear()
    for mod,state in states: mod.show_viewport=state
    bpy.context.view_layer.update(); return result

def validate_scene(stage,strict=False):
    body=bpy.data.objects['CHR_Body']; lo,hi=bounds()
    report={'milestone':stage,'height_m':hi[2]-lo[2],'floor_z':lo[2],
      'editable_half_vertices':len(body.data.vertices),'body_control':evaluate(body,False),
      'body_subdivision':evaluate(body,True),'parts':{},'issues':[]}
    for obj in character_objects():
        result=evaluate(obj,True,False)
        report['parts'][obj.name]={'uv_layers':len(obj.data.uv_layers),'faces':result['faces'],
          'nonmanifold_edges':result['nonmanifold_edges'],'normal_errors':result['inconsistent_normal_edges']}
    for key in ('body_control','body_subdivision'):
        r=report[key]
        for name in ('nonmanifold_edges','inconsistent_normal_edges','degenerate_faces','duplicate_vertices','self_intersections'):
            if r[name]: report['issues'].append(key+': '+name+' = '+str(r[name]))
        if len(r['components'])!=1: report['issues'].append(key+': disconnected components')
        if r['max_symmetry_error']>1e-5: report['issues'].append(key+': asymmetric')
        if r['signed_volume']<=0: report['issues'].append(key+': non-positive volume')
        if r['quads']!=r['faces']: report['issues'].append(key+': non-quad faces')
    for name,r in report['parts'].items():
        if r['nonmanifold_edges'] or r['normal_errors']: report['issues'].append(name+': open or inconsistent normals')
        if strict and not r['uv_layers']: report['issues'].append(name+': missing UVs')
    ref_objs=[o for o in bpy.data.collections['REFERENCES'].objects if o.type=='EMPTY' and o.data]
    report['references']={'image_objects':len(ref_objs),'all_packed':all(o.data.packed_file is not None for o in ref_objs)}
    report['mirror_present']=any(m.type=='MIRROR' for m in body.modifiers)
    if not report['mirror_present']: report['issues'].append('Mirror missing')
    if strict and (abs(report['height_m']-1)>.0001 or abs(report['floor_z'])>.0001): report['issues'].append('Scale or floor mismatch')
    path=PROJECT/'output'/f'validation_{stage:02d}.json'; path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('VALIDATION',stage,'ISSUES',report['issues'])
    if strict and report['issues']: raise RuntimeError('Final validation failed: '+str(report['issues']))
    return report

if __name__=='__main__':
    from helpers import load_checkpoint
    stage=int(sys.argv[-1]); load_checkpoint(stage); validate_scene(stage)
