"""Restore approved eyes and four-digit hands, correcting only posterior skull."""
import bpy,sys,json,datetime,math
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import collection,move_to,sync_basis,meshes,render_views
from head_refinement import smoothstep
from topology import relax_surface

def checkpoint(number,label,notes):
    path=PROJECT/'output'/f'character_{number:02d}_{label}.blend'
    if path.exists(): raise RuntimeError('Keep existing checkpoint: '+str(path))
    for script in (PROJECT/'scripts').glob('game_*.py'):
        old=bpy.data.texts.get(script.name)
        if old: bpy.data.texts.remove(old)
        bpy.data.texts.load(str(script))
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    state=json.loads((PROJECT/'progress.json').read_text())
    state['completed'].append({'stage':number,'file':path.name,'notes':notes,'saved_at':datetime.datetime.now().isoformat()})
    state.update(latest_checkpoint=path.name,latest_stage=number,next_stage=number+1,work_status='game_retopology_and_rig_in_progress',delivery_verified=False)
    (PROJECT/'progress.json').write_text(json.dumps(state,indent=2))
    (PROJECT/'RESUME.md').write_text(f'Latest checkpoint: output/{path.name}\n\n{notes}\n\nContinue from this checkpoint; do not reimport. Previous FINAL is the earlier dense version with unwanted eyes/finger.\n')
    print('CHECKPOINT',path,flush=True)

def load_parts(filename,names):
    with bpy.data.libraries.load(str(PROJECT/'output'/filename),link=False) as (a,b): b.objects=list(names)
    return b.objects

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_FINAL.blend'))
    for colname in ('TOPOLOGY_REVIEW',):
        col=bpy.data.collections.get(colname)
        if col:
            for ob in list(col.objects): bpy.data.objects.remove(ob,do_unlink=True)
            bpy.data.collections.remove(col)
    names=['CHR_Head','CHR_Eye.L','CHR_Eye.R','CHR_Ear.L','CHR_Ear.R','CHR_Eyelid.L','CHR_Eyelid.R']
    for ob in load_parts('character_03c_proportion_fix.blend',names):
        stem=ob.name.split('.00')[0]
        # Name collision suffixes are assigned on linking libraries.
        desired=next(n for n in names if ob.name==n or ob.name.startswith(n+'.'))
        old=bpy.data.objects.get(desired)
        if old and old!=ob: bpy.data.objects.remove(old,do_unlink=True)
        ob.name=desired; collection('CHARACTER').objects.link(ob)
    old=bpy.data.objects.get('CHR_Body'); bpy.data.objects.remove(old,do_unlink=True)
    body=load_parts('character_05b_topology_cleanup.blend',['CHR_Body'])[0]; body.name='CHR_Body'; collection('CHARACTER').objects.link(body)
    for obj in list(meshes()):
        if obj.name.startswith('CHR_Eyebrow'): bpy.data.objects.remove(obj,do_unlink=True)
    head=bpy.data.objects['CHR_Head']
    for v in head.data.vertices:
        x,y,z=v.co; weight=smoothstep(.015,.09,y)*smoothstep(.660,.735,z)
        q=Vector((x/.177,(y-.025)/.174,(z-.820)/.180))
        if q.length>1e-8:
            q.normalize(); desired=Vector((q.x*.177,.025+q.y*.174,.820+q.z*.180))
            v.co=v.co.lerp(desired,.88*weight)
    relax_surface(head,35,np.array([smoothstep(.015,.085,v.co.y)*smoothstep(.66,.74,v.co.z) for v in head.data.vertices]))
    for obj in meshes():
        for mod in obj.modifiers:
            if mod.type=='MIRROR': mod.bisect_threshold=1e-7; mod.merge_threshold=1e-7
        if not any(m.type=='SUBSURF' for m in obj.modifiers):
            sub=obj.modifiers.new('Smooth preview','SUBSURF'); sub.levels=1; sub.render_levels=1
        mat=bpy.data.materials['MAT_ReferenceClay']; obj.data.materials.clear(); obj.data.materials.append(mat)
    sync_basis()
    archive=collection('SCULPT_SOURCE'); archive.hide_render=True; archive.hide_viewport=True
    for obj in meshes():
        copy=obj.copy(); copy.data=obj.data.copy(); copy.name='HIGH_'+obj.name; archive.objects.link(copy)
    checkpoint(8,'restored_design','Recovered stage 03c head/eyes/ears/lids, original three fingers plus thumb, and retained refined body. Corrected only the posterior skull; archived high resolution targets for retopology.')
    render_views(8,1100)
    print(bpy.ops.object.quadriflow_remesh.get_rna_type().properties.keys(),flush=True)

if __name__=='__main__': main()
