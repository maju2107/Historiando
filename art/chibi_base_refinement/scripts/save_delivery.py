"""Save the visually reviewed checkpoint as an editable deliverable and reopen it."""
import bpy,sys,json,hashlib,datetime
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT,SOURCE,REFERENCE_SOURCE,REFERENCES,PREFIX
from helpers import meshes,sync_basis
from validation import audit

EXPECTED_SOURCE_HASH='8506a84aeae4f134cab5ddb584de7c5f49ada4e617fddc293f39212e8bf58fd5'

def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def paired_symmetry():
    result={}
    for stem in ('CHR_Eye','CHR_Ear','CHR_Eyelid','CHR_Eyebrow'):
        left=bpy.data.objects[stem+'.L']; right=bpy.data.objects[stem+'.R']
        kd=KDTree(len(right.data.vertices))
        for v in right.data.vertices: kd.insert(v.co,v.index)
        kd.balance()
        result[stem]=max(kd.find((-v.co.x,v.co.y,v.co.z))[2] for v in left.data.vertices)
    return result

def prepare_interface():
    scene=bpy.context.scene; scene.camera=bpy.data.objects['CAM_ThreeQuarter']
    scene.render.resolution_x=1200; scene.render.resolution_y=1200
    scene.render.filepath='//../renders/three_quarter.png'
    for name in ('REFERENCES','SOURCE_PARTS','TOPOLOGY_REVIEW'):
        col=bpy.data.collections[name]; col.hide_viewport=True; col.hide_render=True
    bpy.ops.object.select_all(action='DESELECT')
    body=bpy.data.objects['CHR_Body']; body.select_set(True); bpy.context.view_layer.objects.active=body
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active; space.region_3d.view_location=Vector((0,0,.51))
                space.region_3d.view_distance=1.65; space.region_3d.view_perspective='ORTHO'
                space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
                space.clip_start=.001; space.shading.type='SOLID'; space.shading.color_type='SINGLE'
                space.shading.single_color=(.65,.67,.67); space.overlay.show_floor=False
                space.overlay.show_axis_x=False; space.overlay.show_axis_y=False
    scene['delivery_note']='Refined from the user FBX. Original dense quad topology retained. See README text and source checkpoints. Forward -Y. Evaluated height 1 m; soles at Z=0.'
    for image in bpy.data.images:
        if image.name.startswith(PREFIX): image.filepath='//../references/'+image.name
    for name in ('README.md','CORRECTION_PLAN.md'):
        old=bpy.data.texts.get(name)
        if old: bpy.data.texts.remove(old)
        bpy.data.texts.load(str(PROJECT/name))
    for script in (PROJECT/'scripts').glob('*.py'):
        old=bpy.data.texts.get(script.name)
        if old: bpy.data.texts.remove(old)
        bpy.data.texts.load(str(script))
    sync_basis()

def main():
    state=json.loads((PROJECT/'progress.json').read_text()); checkpoint=state['latest_checkpoint']
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/checkpoint))
    prepare_interface()
    dest=PROJECT/'output'/'character_FINAL.blend'
    if dest.exists(): raise RuntimeError('Preserve existing delivery; use a new revision name.')
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    bpy.ops.wm.open_mainfile(filepath=str(dest))
    control=audit('reopened_control',False); subdiv=audit('reopened_subdivision',True)
    symmetry=paired_symmetry()
    assert not control['issues'] and not subdiv['issues']
    assert max(symmetry.values())<1e-5, symmetry
    assert abs(subdiv['height_m']-1)<1e-6
    assert abs(subdiv['bounds'][0][2])<1e-6
    assert all(r['transforms_identity'] for r in control['parts'].values())
    assert sha256(SOURCE)==sha256(PROJECT/'source'/'base.fbx')==EXPECTED_SOURCE_HASH
    reference_hashes={}
    for suffix in REFERENCES.values():
        name=PREFIX+suffix+'.jpg'; a=sha256(PROJECT/'references'/name); b=sha256(REFERENCE_SOURCE/name)
        assert a==b; reference_hashes[name]=a
    packed=[im.name for im in bpy.data.images if im.name.startswith(PREFIX) and im.packed_file]
    assert len(packed)==9
    faces=sum(r['faces'] for r in control['parts'].values()); quads=sum(r['quads'] for r in control['parts'].values())
    manifest={'file':str(dest),'file_size':dest.stat().st_size,'sha256':sha256(dest),'checkpoint':checkpoint,
        'verified_at':datetime.datetime.now().isoformat(),'source_sha256':EXPECTED_SOURCE_HASH,
        'reference_hashes':reference_hashes,'packed_references':packed,'paired_symmetry_error_m':symmetry,
        'height_m':subdiv['height_m'],'floor_z_m':subdiv['bounds'][0][2],
        'control_faces':faces,'control_quads':quads,'quad_percentage':quads/faces*100,
        'technical_issues':[],'renders':[p.name for p in (PROJECT/'renders').glob('*.png')],
        'scope':'Preserved dense source topology; central-part self-intersection tests; separate components intentionally overlap at attachments; no rig.'}
    (PROJECT/'output'/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    state['delivery_file']=dest.name; state['delivery_verified']=True; state['work_status']='refinement_delivery_saved'
    (PROJECT/'progress.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    (PROJECT/'RESUME.md').write_text(f'# Continue from the saved refinement\n\nOpen `output/{dest.name}`. Latest numbered checkpoint: `output/{checkpoint}`.\n\nThe final delivery was reopened and audited. Read README.md for preservation details and remaining differences from the references. Do not rebuild, reimport, or replay earlier deformation scripts on this model. New edits should create another numbered revision.\n',encoding='utf-8')
    print('DELIVERY VERIFIED',json.dumps({k:manifest[k] for k in ['file','file_size','height_m','floor_z_m','quad_percentage','paired_symmetry_error_m']}),flush=True)

if __name__=='__main__': main()
