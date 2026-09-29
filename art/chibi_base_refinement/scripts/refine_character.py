"""Checkpoint-first refinement of the supplied base.fbx. Never rebuild the base."""
import bpy,sys,shutil,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import *
from helpers import *

def import_base():
    ensure_directories(); backup=PROJECT/'source'/'base.fbx'
    if not backup.exists(): shutil.copy2(SOURCE,backup)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(backup),use_custom_normals=True)
    col=collection('CHARACTER')
    for obj in list(bpy.context.scene.objects):
        obj['source_object_name']=obj.name
        move_to(obj,col)
    if bpy.context.scene.world is None: bpy.context.scene.world=bpy.data.worlds.new('Neutral World')
    report=inspect(); report['source_sha256']=hashlib.sha256(backup.read_bytes()).hexdigest()
    (PROJECT/'output'/'import_inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    save_checkpoint(1,'Imported the user-created FBX without geometry edits. Preserved every vertex, face, UV and imported object. Original FBX copied to source/base.fbx.')
    setup_studio(); render_views(1)
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    stage=int(sys.argv[-1])
    if stage==1: import_base()
    else:
        state=json.loads((PROJECT/'progress.json').read_text())
        if state['latest_stage']!=stage-1: raise RuntimeError('Continue from the latest stage, do not discard newer work.')
        path=PROJECT/'output'/state['latest_checkpoint']
        bpy.ops.wm.open_mainfile(filepath=str(path))
        if stage==2:
            from references import prepare_references
            notes=prepare_references()
        elif stage==3:
            from proportions import fix_proportions
            notes=fix_proportions()
        elif stage==4:
            from head_refinement import refine_head
            notes=refine_head()
        elif stage==5:
            from topology import cleanup_topology
            notes=cleanup_topology()
        elif stage==6:
            from hands_feet import refine_hands_feet
            notes=refine_hands_feet()
        elif stage==7:
            from finalize import finish_stage
            notes=finish_stage()
        else: raise RuntimeError('Inspect current checkpoint before implementing the next local refinement.')
        save_checkpoint(stage,notes); render_views(stage,1200 if stage==7 else 900)
        if stage in (5,6):
            from topology import hand_overview
            hand_overview(PROJECT/'renders'/('hand_before.png' if stage==5 else 'hand_after.png'))
