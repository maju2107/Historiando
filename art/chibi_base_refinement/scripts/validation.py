"""Technical audit of the source-preserving refinement."""
import bpy,bmesh,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from config import PROJECT
from helpers import meshes

def mesh_report(mesh,symmetry=False,intersections=False):
    bm=bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    kd=KDTree(len(bm.verts))
    for v in bm.verts: kd.insert(v.co,v.index)
    kd.balance(); duplicates=[]
    for v in bm.verts:
        duplicates.extend((v.index,j) for _,j,d in kd.find_range(v.co,1e-8) if j>v.index)
    crosses=[]
    if intersections:
        tree=BVHTree.FromBMesh(bm,epsilon=1e-10)
        crosses=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)]
    r={'vertices':len(bm.verts),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),
       'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'normal_errors':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
       'degenerate_faces':sum(f.calc_area()<1e-13 for f in bm.faces),'duplicate_vertex_pairs':duplicates[:100],
       'self_intersections':crosses[:100],'self_intersection_count':len(crosses),'signed_volume':bm.calc_volume(signed=True)}
    if symmetry: r['max_symmetry_error']=max(kd.find((-v.co.x,v.co.y,v.co.z))[2] for v in bm.verts)
    bm.free(); return r

def audit(label,subdivision=True):
    report={'label':label,'parts':{},'issues':[]}; graph=bpy.context.evaluated_depsgraph_get(); points=[]
    for obj in meshes():
        states=[]
        if not subdivision:
            for m in obj.modifiers:
                if m.type=='SUBSURF': states.append(m); m.show_viewport=False
        bpy.context.view_layer.update(); graph=bpy.context.evaluated_depsgraph_get(); ev=obj.evaluated_get(graph); me=ev.to_mesh()
        check=obj.name in ('CHR_Body','CHR_Head','CHR_Neck')
        r=mesh_report(me,symmetry=check,intersections=check)
        points.extend(obj.matrix_world@v.co for v in me.vertices); ev.to_mesh_clear()
        r['transforms_identity']=max(abs(obj.scale[i]-1) for i in range(3))<1e-6 and obj.location.length<1e-6 and sum(abs(a) for a in obj.rotation_euler)<1e-6
        r['source_name']=obj.get('source_object_name'); r['uv_layers']=len(obj.data.uv_layers)
        for m in states: m.show_viewport=True
        report['parts'][obj.name]=r
        for key in ('nonmanifold_edges','normal_errors','degenerate_faces','duplicate_vertex_pairs','self_intersection_count'):
            if r[key]: report['issues'].append(f'{obj.name}: {key} = {r[key]}')
        print('AUDIT',label,obj.name,r['vertices'],r['quads'],'nonmanifold',r['nonmanifold_edges'],'crosses',r['self_intersection_count'],flush=True)
    lo=[min(v[i] for v in points) for i in range(3)]; hi=[max(v[i] for v in points) for i in range(3)]
    report['bounds']=[lo,hi]; report['height_m']=hi[2]-lo[2]
    (PROJECT/'output'/('validation_'+label+'.json')).write_text(json.dumps(report,indent=2))
    print('ISSUES',report['issues'],flush=True); return report

if __name__=='__main__':
    state=json.loads((PROJECT/'progress.json').read_text()); bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/state['latest_checkpoint']))
    audit('control',False); audit('subdivision',True)
