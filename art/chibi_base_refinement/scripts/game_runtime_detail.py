"""Concentrate extra polygons at digit and foot silhouettes, keeping the body light."""
import bpy,bmesh,sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes
from game_restore import checkpoint
from game_retopology import source_tree,select
from game_pose_validation import validate_poses,render
from validation import audit

def local_subdivide(body):
    tree=source_tree(bpy.data.objects['HIGH_CHR_Body'])
    bm=bmesh.new(); bm.from_mesh(body.data)
    faces=[f for f in bm.faces if abs(f.calc_center_median().x)>.283 or f.calc_center_median().z<.108]
    edges=list({e for f in faces for e in f.edges})
    bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True,smooth=0)
    ngons=[f for f in bm.faces if len(f.verts)>4]
    result=bmesh.ops.triangulate(bm,faces=ngons)
    tris=[f for f in result.get('faces',[]) if len(f.verts)==3]
    if tris:bmesh.ops.join_triangles(bm,faces=tris,angle_face_threshold=.7,angle_shape_threshold=.7)
    for v in bm.verts:
        if abs(v.co.x)>.294 or v.co.z<.101:
            hit=tree.find_nearest(v.co)
            if hit and hit[0] is not None and hit[3]<.014:v.co=hit[0]
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(body.data); bm.free(); body.data.update()
    # Subdivision interpolates source weights. Limit and normalize after interpolation.
    for v in body.data.vertices:
        values=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-6],key=lambda p:p[1],reverse=True)[:4]
        total=sum(w for i,w in values)
        for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
        for i,w in values:body.vertex_groups[i].add([v.index],w/total,'REPLACE')

def ears():
    for suffix in ['L','R']:
        obj=bpy.data.objects['CHR_Ear.'+suffix]; select(obj)
        mod=next(m for m in obj.modifiers if m.type=='SUBSURF'); mod.show_viewport=True;mod.show_render=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        tree=source_tree(bpy.data.objects['HIGH_CHR_Ear.'+suffix])
        for v in obj.data.vertices:
            hit=tree.find_nearest(v.co)
            if hit and hit[0] is not None:v.co=hit[0]
        obj.data.update()

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_12_runtime_materials.blend'))
    scene=bpy.context.scene;scene.frame_set(1);rig=bpy.data.objects['RIG_Chibi']; action=rig.animation_data.action;rig.animation_data.action=None
    local_subdivide(bpy.data.objects['CHR_Body']);ears()
    for obj in meshes():
        for poly in obj.data.polygons:poly.use_smooth=True
    report=validate_poses(rig)
    rig.animation_data.action=action;scene.frame_set(1)
    a=audit('game_detailed_control',False)
    for obj in meshes():
        for m in obj.modifiers:
            if m.type=='SUBSURF':m.show_viewport=False;m.show_render=False
    checkpoint(12,'runtime_detail','Added projected quad subdivisions only to hands and feet and restored smooth ear contours. Runtime subdivision remains disabled. Inherited skin weights normalized to four influences and deformation retested.')
    render('runtime_three_quarter','CAM_ThreeQuarter',1200); render('runtime_face','CAM_Face',1200);render('runtime_hand','CAM_Hand',1200)

if __name__=='__main__':main()
