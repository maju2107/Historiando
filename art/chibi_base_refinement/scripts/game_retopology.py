"""Surface-constrained quad retopology of the approved existing design."""
import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import meshes,collection,render_views
from game_restore import checkpoint

FACE_BUDGETS={'CHR_Body':4800,'CHR_Head':4400,'CHR_Neck':160,'CHR_Eyelid.L':240}

def select(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.hide_set(False); obj.select_set(True); bpy.context.view_layer.objects.active=obj

def source_tree(obj):
    return BVHTree.FromPolygons([v.co for v in obj.data.vertices],[list(p.vertices) for p in obj.data.polygons])

def setup_preview(obj):
    for face in obj.data.polygons: face.use_smooth=True
    mod=obj.modifiers.new('Subdivision preview / disable for game export','SUBSURF'); mod.levels=1; mod.render_levels=1
    obj.data.materials.clear(); obj.data.materials.append(bpy.data.materials['MAT_ReferenceClay'])

def retopo(obj):
    target=bpy.data.objects['HIGH_'+obj.name]; tree=source_tree(target)
    obj.shape_key_clear(); obj.modifiers.clear(); select(obj)
    print('RETOPO START',obj.name,len(obj.data.polygons),flush=True)
    if obj.name in ('CHR_Eye.L','CHR_Ear.L'):
        bm=bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.unsubdivide(bm,verts=list(bm.verts),iterations=4)
        bm.to_mesh(obj.data); bm.free()
    else:
        obj.data.use_mirror_x=obj.name in ('CHR_Head','CHR_Body','CHR_Neck')
        obj.data.use_mirror_y=False; obj.data.use_mirror_z=False
        bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=obj.data.use_mirror_x,use_preserve_sharp=False,
            use_preserve_boundary=True,smooth_normals=True,target_faces=FACE_BUDGETS[obj.name],seed=11)
    # Project the new cage onto the approved source, without changing the design.
    for v in obj.data.vertices:
        hit=tree.find_nearest(v.co)
        if hit and hit[0] is not None: v.co=hit[0]
    bm=bmesh.new(); bm.from_mesh(obj.data)
    if obj.name in ('CHR_Head','CHR_Body','CHR_Neck'):
        bmesh.ops.symmetrize(bm,input=list(bm.verts)+list(bm.edges)+list(bm.faces),direction='X',dist=1e-6)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free()
    obj.data.update(); setup_preview(obj)
    obj['retopology_source']='HIGH_'+obj.name
    obj['retopology_method']='Recovered regular quad cage' if obj.name in ('CHR_Eye.L','CHR_Ear.L') else 'QuadriFlow field aligned quad cage, projected to restored source, symmetric where applicable'
    print('RETOPO FINISH',obj.name,len(obj.data.vertices),len(obj.data.polygons),flush=True)

def mirror_pairs():
    for stem in ('CHR_Eye','CHR_Ear','CHR_Eyelid'):
        old=bpy.data.objects[stem+'.R']; bpy.data.objects.remove(old,do_unlink=True)
        left=bpy.data.objects[stem+'.L']; right=left.copy(); right.data=left.data.copy(); right.name=stem+'.R'; collection('CHARACTER').objects.link(right)
        for v in right.data.vertices: v.co.x=-v.co.x
        bm=bmesh.new(); bm.from_mesh(right.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(right.data); bm.free()

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_08_restored_design.blend'))
    for name in ('CHR_Body','CHR_Head','CHR_Neck','CHR_Eye.L','CHR_Ear.L','CHR_Eyelid.L'):
        retopo(bpy.data.objects[name])
    mirror_pairs()
    checkpoint(9,'game_retopology','New projected quad cages over restored source. Original eye/ear cages reduced where regular. Four digits retained per hand. High-resolution source archived. Joint deformation and weights still require validation.')
    render_views(9,1100)
    from validation import audit
    audit('game_retopology_control',False); audit('game_retopology_smooth',True)

if __name__=='__main__': main()
