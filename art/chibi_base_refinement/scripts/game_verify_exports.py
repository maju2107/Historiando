"""Reimport exports and compare rest and two deformed poses with Blender source."""
import bpy,sys,json,hashlib,datetime,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT,SOURCE
from game_pose_validation import set_pose

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    final=PROJECT/'output'/'character_GAME_RIGGED.blend';expected=np.load(PROJECT/'output'/'game_expected_poses.npz')
    bpy.ops.wm.open_mainfile(filepath=str(final));scene=bpy.context.scene
    assert scene.frame_current==1
    assert len(bpy.data.objects['RIG_Chibi'].data.bones)==46
    packed=[im.name for im in bpy.data.images if im.packed_file]
    assert 'Chibi_head_normal' in packed
    text=bpy.data.texts.get('GAME_README.md')
    if text:bpy.data.texts.remove(text)
    bpy.data.texts.load(str(PROJECT/'GAME_README.md'))
    for name in ('game_pose_validation.py','game_verify_exports.py'):
        text=bpy.data.texts.get(name)
        if text:bpy.data.texts.remove(text)
        bpy.data.texts.load(str(PROJECT/'scripts'/name))
    bpy.ops.wm.save_as_mainfile(filepath=str(final))
    report={'blend':str(final),'packed_images':packed,'exports':{}}
    for ext in ('glb','fbx'):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path=PROJECT/'output'/('character_GAME_RIGGED.'+ext)
        if ext=='glb':bpy.ops.import_scene.gltf(filepath=str(path))
        else:bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
        rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];assert len(rigs)==1
        rig=rigs[0];parts=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('CHR_')]
        assert len(parts)==9,(ext,[o.name for o in parts])
        entry={'bones':len(rig.data.bones),'meshes':len(parts),'poses':{}}
        for frame in (1,40,80):
            set_pose(rig,frame); graph=bpy.context.evaluated_depsgraph_get(); errors={}
            for obj in parts:
                coords=expected[f'{frame}__{obj.name}'];kd=KDTree(len(coords))
                for i,co in enumerate(coords):kd.insert(Vector(co),i)
                kd.balance();ev=obj.evaluated_get(graph);me=ev.to_mesh()
                error=max(kd.find(obj.matrix_world@v.co)[2] for v in me.vertices);ev.to_mesh_clear();errors[obj.name]=error
            entry['poses'][str(frame)]=errors
        report['exports'][ext]=entry
        print('REIMPORT',ext,json.dumps(entry),flush=True)
    report['max_roundtrip_position_error_m']=max(e for entry in report['exports'].values() for pose in entry['poses'].values() for e in pose.values())
    assert report['max_roundtrip_position_error_m']<.0001,report['max_roundtrip_position_error_m']
    assert digest(SOURCE)==digest(PROJECT/'source'/'base.fbx')=='8506a84aeae4f134cab5ddb584de7c5f49ada4e617fddc293f39212e8bf58fd5'
    report['files']={ext:{'bytes':(PROJECT/'output'/('character_GAME_RIGGED.'+ext)).stat().st_size,'sha256':digest(PROJECT/'output'/('character_GAME_RIGGED.'+ext))} for ext in ('blend','glb','fbx')}
    report['verified_at']=datetime.datetime.now().isoformat()
    (PROJECT/'output'/'game_export_verification.json').write_text(json.dumps(report,indent=2))
    state=json.loads((PROJECT/'progress.json').read_text());state.update(delivery_file=final.name,delivery_verified=True,next_stage=None,work_status='game_rig_delivery_verified')
    (PROJECT/'progress.json').write_text(json.dumps(state,indent=2))
    (PROJECT/'RESUME.md').write_text('# Current game character\n\nOpen `output/character_GAME_RIGGED.blend`. Latest numbered checkpoint: `output/character_13_game_ready.blend`.\n\nUser-approved long eyes and original three fingers plus thumb restored. Retopology, FK skeleton, normalized weights and five pose tests completed. GLB and FBX reimported and compared in three poses. See GAME_README.md and output/game_export_verification.json.\n\nDo not resume from the older character_FINAL.blend, which is preserved historical work. Do not reimport or rebuild. New refinements should create another checkpoint.\n')
    print('ALL EXPORTS VERIFIED',report['max_roundtrip_position_error_m'],flush=True)

if __name__=='__main__':main()
