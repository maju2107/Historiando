"""Scene organization, checkpoints, inspection and reference-view rendering."""
import bpy,bmesh,math,json,datetime,shutil
from mathutils import Vector,Quaternion
from mathutils.kdtree import KDTree
from config import PROJECT,STAGES

def ensure_directories():
    for name in ('source','references','scripts','renders','output'):
        (PROJECT/name).mkdir(parents=True,exist_ok=True)

def meshes(): return [o for o in bpy.data.collections['CHARACTER'].objects if o.type=='MESH']

def collection(name):
    col=bpy.data.collections.get(name)
    if not col: col=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(col)
    return col

def move_to(obj,col):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    col.objects.link(obj)

def bounds(objects=None):
    pts=[obj.matrix_world@v.co for obj in objects or meshes() for v in obj.data.vertices]
    return [min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]

def inspect():
    report={'bounds':bounds(),'objects':{}}
    for obj in meshes():
        bm=bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
        pending=set(bm.verts); comps=[]
        while pending:
            wave=[pending.pop()]; comp=[]
            while wave:
                v=wave.pop(); comp.append(v)
                for e in v.link_edges:
                    w=e.other_vert(v)
                    if w in pending: pending.remove(w); wave.append(w)
            comps.append({'vertices':len(comp),'bbox':[[min(v.co[i] for v in comp) for i in range(3)],
                         [max(v.co[i] for v in comp) for i in range(3)]]})
        kd=KDTree(len(bm.verts))
        for v in bm.verts: kd.insert(v.co,v.index)
        kd.balance()
        symmetry=max(kd.find((-v.co.x,v.co.y,v.co.z))[2] for v in bm.verts)
        report['objects'][obj.name]={'vertices':len(bm.verts),'faces':len(bm.faces),
           'quads':sum(len(f.verts)==4 for f in bm.faces),'triangles':sum(len(f.verts)==3 for f in bm.faces),
           'nonmanifold':sum(not e.is_manifold for e in bm.edges),'boundary':sum(e.is_boundary for e in bm.edges),
           'normals':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'components':comps,
           'symmetry_error_local':symmetry,'location':list(obj.location),'rotation':list(obj.rotation_euler),
           'scale':list(obj.scale),'materials':[m.name if m else None for m in obj.data.materials],
           'uv_layers':[u.name for u in obj.data.uv_layers],
           'modifiers':[(m.name,m.type) for m in obj.modifiers],'groups':[g.name for g in obj.vertex_groups]}
        bm.free()
    return report

def sync_basis():
    for obj in meshes():
        if obj.data.shape_keys:
            for vertex,keypoint in zip(obj.data.vertices,obj.data.shape_keys.key_blocks[0].data): keypoint.co=vertex.co
            obj.data.update()
    bpy.context.view_layer.update()

def save_checkpoint(n,notes,revision=''):
    sync_basis()
    path=PROJECT/'output'/f'character_{n:02d}{revision}_{STAGES[n]}.blend'
    if path.exists(): raise RuntimeError('Checkpoint already exists; preserve it: '+str(path))
    bpy.context.scene['milestone']=n
    for script in (PROJECT/'scripts').glob('*.py'):
        old=bpy.data.texts.get(script.name)
        if old: bpy.data.texts.remove(old)
        bpy.data.texts.load(str(script))
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    p=PROJECT/'progress.json'; state=json.loads(p.read_text()) if p.exists() else {'completed':[]}
    state['completed'].append({'stage':n,'file':path.name,'notes':notes,'saved_at':datetime.datetime.now().isoformat()})
    state.update(latest_checkpoint=path.name,latest_stage=n,next_stage=n+1 if n<7 else None)
    p.write_text(json.dumps(state,indent=2),encoding='utf-8')
    (PROJECT/'RESUME.md').write_text(f'Latest checkpoint: output/{path.name}\n\nLoad this file and continue. Do not reimport or rebuild the model.\nNext stage: {state["next_stage"]}.\n',encoding='utf-8')
    print('CHECKPOINT SAVED',path,flush=True)

def aim(obj,point): obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

def setup_studio():
    col=collection('VALIDATION'); scene=bpy.context.scene
    lo,hi=bounds(); height=hi[2]-lo[2]; target=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,(lo[2]+hi[2])/2))
    for label,direction in [('Front',(0,-3,0)),('Right',(3,0,0)),('Back',(0,3,0)),('ThreeQuarter',(1.6,-3,.65))]:
        name='CAM_'+label; cam=bpy.data.objects.get(name)
        if not cam: cam=bpy.data.objects.new(name,bpy.data.cameras.new(name)); col.objects.link(cam)
        cam.location=target+Vector(direction)*height; aim(cam,target)
        cam.data.type='ORTHO'; cam.data.ortho_scale=max(height*1.18,(hi[0]-lo[0])*1.10)
        cam.data.clip_start=.001; cam.data.clip_end=max(100,height*10); cam.hide_set(True)
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO'; scene.display.shading.studiolight_rotate_z=.25
    scene.display.shading.color_type='SINGLE'; scene.display.shading.single_color=(.65,.67,.67)
    scene.display.shading.background_type='WORLD'; scene.world.color=(.045,.045,.045)
    scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type='BOTH'; scene.display.shading.curvature_ridge_factor=1.1
    scene.display.shading.curvature_valley_factor=.8
    scene.view_settings.view_transform='Standard'
    scene.render.image_settings.file_format='PNG'; scene.render.resolution_percentage=100
    scene.camera=bpy.data.objects['CAM_ThreeQuarter']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active; sp.region_3d.view_location=target; sp.region_3d.view_distance=height*1.7
                sp.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2); sp.region_3d.view_perspective='ORTHO'

def render_views(stage,resolution=900):
    folder=PROJECT/'renders'/f'stage_{stage:02d}'; folder.mkdir(exist_ok=True)
    scene=bpy.context.scene; scene.render.resolution_x=resolution; scene.render.resolution_y=resolution
    for name,label in [('front','Front'),('side','Right'),('back','Back'),('three_quarter','ThreeQuarter')]:
        scene.camera=bpy.data.objects['CAM_'+label]; scene.render.filepath=str(folder/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        shutil.copy2(folder/(name+'.png'),PROJECT/'renders'/(name+'.png'))
    scene.camera=bpy.data.objects['CAM_ThreeQuarter']
