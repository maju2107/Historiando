"""Make a welded bilateral cage using a bisect Mirror, with staged audits."""
import bpy,bmesh,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from game_retopology import select,setup_preview
from game_clean_cage import clean
from game_restore import checkpoint
from validation import mesh_report,audit
from helpers import render_views

def stage(obj,label):
    r=mesh_report(obj.data,False,True)
    print('STEP',obj.name,label,{k:r[k] for k in ['vertices','faces','nonmanifold_edges','self_intersection_count']},flush=True)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_09_game_retopology_clean.blend'))
    for name,budget in [('CHR_Body',5000),('CHR_Head',5000)]:
        obj=bpy.data.objects[name]; obj.modifiers.clear(); obj.data=bpy.data.objects['HIGH_'+name].data.copy(); obj.shape_key_clear(); clean(obj); select(obj)
        obj.data.use_mirror_x=False
        result=bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=False,use_preserve_sharp=False,use_preserve_boundary=False,smooth_normals=True,target_faces=budget,seed=14)
        assert 'FINISHED' in result
        stage(obj,'raw_quadflow')
        mod=obj.modifiers.new('Welded bilateral symmetry','MIRROR'); mod.use_bisect_axis[0]=True; mod.merge_threshold=1e-5; mod.bisect_threshold=1e-5
        bpy.ops.object.modifier_apply(modifier=mod.name); clean(obj); stage(obj,'mirror_weld')
        setup_preview(obj)
    audit('game_seam_control',False); audit('game_seam_smooth',True)
    checkpoint(9,'game_retopology_welded','Replaced defective symmetry seams with bisect-and-welded cages; retained approved source shapes. Small component cages and corrected posterior skull preserved.')
    render_views(9,1100)

if __name__=='__main__': main()
