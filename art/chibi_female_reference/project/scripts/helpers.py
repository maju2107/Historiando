"""Persistent Blender editing, references, cameras, rendering and checkpoints."""
import bpy,bmesh,math,json,shutil,datetime
from pathlib import Path
from mathutils import Vector,Quaternion
from config import *

def ensure_directories():
    for name in ('references','scripts','renders','output'):
        (PROJECT/name).mkdir(parents=True,exist_ok=True)

def character_objects():
    return [o for o in bpy.data.collections['CHARACTER'].objects if o.type=='MESH']

def bounds(objects=None):
    points=[]; graph=bpy.context.evaluated_depsgraph_get()
    for obj in objects or character_objects():
        ev=obj.evaluated_get(graph); me=ev.to_mesh()
        points.extend(obj.matrix_world@v.co for v in me.vertices); ev.to_mesh_clear()
    return [min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]

def setup_scene():
    """Import the existing editable model once; subsequent stages open checkpoints."""
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
    scene=bpy.context.scene; scene.name='Chibi Female / Reference Reconstruction'
    bpy.data.collections['01 · MODEL'].name='CHARACTER'
    bpy.data.collections['02 · PREVIEW STUDIO'].name='VALIDATION'
    bpy.data.collections['03 · REFERENCE (packed)'].name='REFERENCES'
    names={'Chibi - corpo e cabeca':'CHR_Body','Olho.L':'CHR_Eye.L','Olho.R':'CHR_Eye.R',
      'Sobrancelha.L':'CHR_Eyebrow.L','Sobrancelha.R':'CHR_Eyebrow.R',
      'Palpebra superior.L':'CHR_Eyelid.L','Palpebra superior.R':'CHR_Eyelid.R',
      'Top - peca separada':'CHR_Top','Short - peca separada':'CHR_Briefs'}
    for old,new in names.items(): bpy.data.objects[old].name=new
    for side in ('L','R'):
        for k in (1,2): bpy.data.objects[f'Cilio_{k}.{side}'].name=f'CHR_Eyelash_{k}.{side}'
    low,high=bounds(); scale=TOTAL_HEIGHT/(high[2]-low[2]); floor=low[2]
    scene['import_scale']=scale; scene['import_floor']=floor
    for obj in character_objects():
        for v in obj.data.vertices:
            v.co.x*=scale; v.co.y*=scale; v.co.z=(v.co.z-floor)*scale
        for mod in obj.modifiers:
            if mod.type=='SOLIDIFY': mod.thickness*=scale
        obj.data.update()
    for obj in list(bpy.data.collections['VALIDATION'].objects): bpy.data.objects.remove(obj,do_unlink=True)
    for obj in list(bpy.data.collections['REFERENCES'].objects): bpy.data.objects.remove(obj,do_unlink=True)
    scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1.0
    scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED'; scene.render.threads=6
    scene.view_settings.view_transform='Standard'; scene.render.image_settings.file_format='PNG'
    scene['forward_axis']='-Y'; scene['height_m']=TOTAL_HEIGHT
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active; sp.region_3d.view_location=(0,0,.5); sp.region_3d.view_distance=1.55
                sp.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2); sp.region_3d.view_perspective='ORTHO'
    setup_materials(); setup_validation_cameras()

def setup_materials():
    scene=bpy.context.scene
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.042,.042,.042,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
    for obj in character_objects():
        for face in obj.data.polygons: face.use_smooth=True
        for mat in obj.data.materials:
            if mat and mat.use_nodes:
                bs=mat.node_tree.nodes.get('Principled BSDF')
                if bs: bs.inputs['Base Color'].default_value=(.46,.47,.47,1); bs.inputs['Roughness'].default_value=.8

def setup_references():
    collection=bpy.data.collections['REFERENCES']; collection.hide_viewport=False
    for category,suffix in REFERENCES.items():
        name=PREFIX+suffix+'.jpg'; dest=PROJECT/'references'/name
        if not dest.exists(): shutil.copy2(REFERENCE_SOURCE/name,dest)
        im=bpy.data.images.load(str(dest),check_existing=True); im.pack(); im.use_fake_user=True
        label={'FRONT':'REF_Front','SIDE':'REF_Side','BACK':'REF_Back'}.get(category,'REF_'+category)
        obj=bpy.data.objects.new(label,None); collection.objects.link(obj)
        obj.empty_display_type='IMAGE'; obj.data=im; obj.color[3]=REFERENCE_OPACITY
        obj.empty_image_depth='BACK'; obj.hide_render=True; obj['reference_category']=category
        if category in REFERENCE_ALIGNMENT:
            c=REFERENCE_ALIGNMENT[category]; px=c['height_px']; dx=(im.size[0]/2-c['center_x_px'])/px
            z=(c['floor_y_px']-im.size[1]/2)/px; obj.empty_display_size=im.size[0]/px
            if category=='FRONT': obj.location=(dx,REFERENCE_DISTANCE,z); obj.rotation_euler=(math.pi/2,0,0)
            if category=='BACK': obj.location=(-dx,-REFERENCE_DISTANCE,z); obj.rotation_euler=(math.pi/2,0,math.pi)
            if category=='SIDE': obj.location=(REFERENCE_DISTANCE,-dx,z); obj.rotation_euler=(math.pi/2,0,-math.pi/2)
            obj.location+=Vector(c['offset'])
        else:
            obj.empty_display_size=.6; obj.location=(2,0,len(collection.objects)*.15); obj.rotation_euler.x=math.pi/2
    collection.hide_viewport=True; collection.hide_render=True

def aim(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def setup_validation_cameras():
    col=bpy.data.collections['VALIDATION']
    for label,loc in (('Front',(0,-3,.5)),('Right',(3,0,.5)),('Back',(0,3,.5)),('ThreeQuarter',(1.6,-3,1.15))):
        name='CAM_'+label; camera=bpy.data.objects.get(name)
        if camera is None:
            camera=bpy.data.objects.new(name,bpy.data.cameras.new(name)); col.objects.link(camera)
        camera.data.type='ORTHO'; camera.data.ortho_scale=1.17; camera.data.clip_start=.001; camera.data.clip_end=100
        camera.location=loc; aim(camera,(0,0,.5)); camera.hide_set(True)
    for label,loc,power,size in [('Key',(-1,-1.5,2),45,1.3),('Fill',(1,-1,1.4),28,1.3),('Rim',(.7,1.2,1.6),40,1.3)]:
        data=bpy.data.lights.new('LGT_'+label,'AREA'); data.energy=power; data.size=size
        obj=bpy.data.objects.new('LGT_'+label,data); col.objects.link(obj); obj.location=loc; aim(obj,(0,0,.5)); obj.hide_set(True)
    bpy.context.scene.camera=bpy.data.objects['CAM_ThreeQuarter']

def rebuild_wire():
    from smooth_preview import make_wire_overlay
    col=bpy.data.collections['VALIDATION']
    for obj in list(col.objects):
        if obj.type=='CURVE': bpy.data.objects.remove(obj,do_unlink=True)
    proxies=[]; parts=[]
    for obj in character_objects():
        if any(m.type=='MIRROR' for m in obj.modifiers):
            proxy=obj.copy(); proxy.data=obj.data.copy(); col.objects.link(proxy)
            proxy.hide_set(False); proxy.hide_render=False
            bpy.context.view_layer.objects.active=proxy; proxy.select_set(True)
            for mod in list(proxy.modifiers):
                if mod.type=='MIRROR': bpy.ops.object.modifier_apply(modifier=mod.name)
            proxies.append(proxy); parts.append(proxy)
        else: parts.append(obj)
    wire=make_wire_overlay(parts,col,bpy.data.materials['Topologia'],bevel_depth=.00018)
    wire.name='VIEW_ControlEdges'; wire.hide_set(True)
    for obj in proxies:
        data=obj.data; bpy.data.objects.remove(obj,do_unlink=True); bpy.data.meshes.remove(data)
    return wire

def render_validation_views(milestone,final=False):
    scene=bpy.context.scene; folder=PROJECT/'renders'/f'm{milestone:02d}'; folder.mkdir(exist_ok=True)
    rebuild_wire(); size=FINAL_RESOLUTION if final else PREVIEW_RESOLUTION
    scene.render.resolution_x=size; scene.render.resolution_y=size; scene.render.resolution_percentage=100
    scene.cycles.samples=48 if final else 24
    for filename,camera in [('front','CAM_Front'),('side','CAM_Right'),('back','CAM_Back'),('three_quarter','CAM_ThreeQuarter')]:
        scene.camera=bpy.data.objects[camera]; scene.render.filepath=str(folder/(filename+'.png'))
        bpy.ops.render.render(write_still=True)
        shutil.copy2(folder/(filename+'.png'),PROJECT/'renders'/(filename+'.png'))
    scene.camera=bpy.data.objects['CAM_ThreeQuarter']

    if milestone>=4:
        cam=bpy.data.objects.get('CAM_Details')
        if cam is None:
            cam=bpy.data.objects.new('CAM_Details',bpy.data.cameras.new('CAM_Details'))
            bpy.data.collections['VALIDATION'].objects.link(cam)
        cam.data.type='ORTHO'; cam.data.clip_start=.001; cam.hide_set(True)
        details=[('face_front',(0,-3,.81),(0,0,.81),.53),
                 ('face_three_quarter',(1.7,-3,1.05),(0,.025,.81),.58)]
        if milestone>=5: details.append(('hand_detail',(.375,-.4,1.2),(.375,-.02,.55),.31))
        for name,loc,target,scale in details:
            cam.location=loc; aim(cam,target); cam.data.ortho_scale=scale; scene.camera=cam
            scene.render.filepath=str(folder/(name+'.png')); bpy.ops.render.render(write_still=True)
            shutil.copy2(folder/(name+'.png'),PROJECT/'renders'/(name+'.png'))
        scene.camera=bpy.data.objects['CAM_ThreeQuarter']

def load_checkpoint(n):
    path=PROJECT/'output'/f'{n:02d}_{MILESTONES[n]}.blend'
    if not path.exists(): raise RuntimeError(f'Checkpoint {n} missing. Continue the preceding milestone first.')
    bpy.ops.wm.open_mainfile(filepath=str(path))

def save_project(n,notes):
    scene=bpy.context.scene; scene['milestone']=n; scene['milestone_name']=MILESTONES[n]
    body=bpy.data.objects['CHR_Body']; bpy.ops.object.select_all(action='DESELECT'); body.select_set(True)
    bpy.context.view_layer.objects.active=body
    for path in (PROJECT/'scripts').glob('*.py'):
        existing=bpy.data.texts.get(path.name)
        if existing: bpy.data.texts.remove(existing)
        bpy.data.texts.load(str(path))
    checkpoint=PROJECT/'output'/f'{n:02d}_{MILESTONES[n]}.blend'
    if checkpoint.exists(): raise RuntimeError('A numbered checkpoint is immutable: '+str(checkpoint))
    bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint))
    state_path=PROJECT/'progress.json'
    state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'completed':[]}
    state['completed'].append({'milestone':n,'name':MILESTONES[n],'file':str(checkpoint),'notes':notes,
                              'saved_at':datetime.datetime.now().isoformat()})
    state.update(latest_milestone=n,latest_checkpoint=str(checkpoint),next_milestone=n+1 if n<7 else None)
    state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    (PROJECT/'RESUME.md').write_text(f'# Resume\n\nLatest checkpoint: `{checkpoint.name}`.\n'
      f'Completed milestone: {n} / 7.\nNext: {state["next_milestone"]}.\n\n'
      'Load this checkpoint and continue. Never run the old full-model generator to resume.\n'
      'Run Blender with `--background --python scripts/build_character.py -- --milestone N`.\n',encoding='utf-8')
    print('CHECKPOINT SAVED',checkpoint)
