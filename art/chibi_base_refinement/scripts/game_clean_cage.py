"""Repair the symmetric seam and complete the small component cages."""
import bpy,bmesh,sys,math,json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes,render_views
from game_restore import checkpoint
from game_retopology import select,setup_preview,mirror_pairs
from head_refinement import smoothstep
from validation import audit

def clean(obj):
    obj.shape_key_clear()
    bm=bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()

def neck_cage():
    obj=bpy.data.objects['CHR_Neck']; obj.shape_key_clear(); obj.modifiers.clear()
    vs=[]; fs=[]; n=16
    for z,rx,ry,cy in [(.572,.026,.022,-.010),(.578,.029,.025,-.011),(.593,.032,.026,-.012),(.612,.032,.026,-.013),(.631,.033,.027,-.011),(.654,.037,.029,-.008),(.673,.034,.025,-.006),(.680,.026,.020,-.006)]:
        for j in range(n): a=j*math.tau/n; vs.append((rx*math.cos(a),cy+ry*math.sin(a),z))
    for i in range(7):
        for j in range(n): k=(j+1)%n; fs.append((i*n+j,i*n+k,(i+1)*n+k,(i+1)*n+j))
    for start in (0,7*n):
        center=len(vs); vs.append(tuple(sum(v[d] for v in vs[start:start+n])/n for d in range(3)))
        for j in range(0,n,2): fs.append((center,start+j,start+(j+1)%n,start+(j+2)%n))
    me=bpy.data.meshes.new('Neck articulation quad rings'); me.from_pydata(vs,[],fs); obj.data=me; clean(obj); setup_preview(obj)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_09_game_retopology.blend'))
    for obj in meshes(): clean(obj)
    for name in ('CHR_Head','HIGH_CHR_Head'):
        head=bpy.data.objects[name]; head.shape_key_clear()
        for v in head.data.vertices:
            x,y,z=v.co; w=smoothstep(.005,.055,y)
            q=Vector((x/.177,(y-.025)/.174,(z-.820)/.180))
            if q.length>1e-8:
                q.normalize(); v.co=v.co.lerp(Vector((q.x*.177,.025+q.y*.174,.820+q.z*.180)),w)
        head.data.update()
    neck_cage()
    obj=bpy.data.objects['CHR_Eyelid.L']; obj.modifiers.clear(); select(obj)
    result=bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=True,smooth_normals=True,target_faces=240,seed=8)
    print('LID QUAD RESULT',result,len(obj.data.polygons),flush=True)
    if len(obj.data.polygons)>700:
        bm=bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.unsubdivide(bm,verts=list(bm.verts),iterations=4)
        tris=[f for f in bm.faces if len(f.verts)==3]
        bmesh.ops.join_triangles(bm,faces=tris,angle_face_threshold=math.pi,angle_shape_threshold=math.pi)
        bm.to_mesh(obj.data); bm.free()
    clean(obj); setup_preview(obj); mirror_pairs()
    report=audit('game_clean_control',False); audit('game_clean_smooth',True)
    checkpoint(9,'game_retopology_clean','Welded symmetric seam; rebuilt neck as controlled quad rings; reduced eyelid cages; rounded the full posterior cranium without altering the frontal features. Technical audit retained for further local cleanup.')
    render_views(9,1100)

if __name__=='__main__': main()
