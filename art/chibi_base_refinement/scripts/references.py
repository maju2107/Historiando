"""Normalize the imported mesh without changing its shape, then align images."""
import bpy,bmesh,math,shutil,json
from mathutils import Matrix,Vector
from config import *
from helpers import *

def normalize_import():
    lo,hi=bounds(); scale=1/(hi[2]-lo[2]); floor=lo[2]; center_y=.105
    objects=meshes(); matrices={o:o.matrix_world.copy() for o in objects}
    for obj in objects:
        matrix=matrices[obj]
        obj.parent=None; obj.matrix_world=Matrix.Identity(4)
        for v in obj.data.vertices:
            co=matrix@v.co; v.co=(co.x*scale,(co.y-center_y)*scale,(co.z-floor)*scale)
        obj.data.update()
        for p in obj.data.polygons: p.use_smooth=True
        obj['preserved_source_vertices']=len(obj.data.vertices)
    names={'corpo':'CHR_Body','coco':'CHR_Head','pescoço':'CHR_Neck','quadril':'SRC_HipBlock',
           'bolota do zoio':'CHR_Eyes','orelhas':'CHR_Ears','cílios':'CHR_Eyelids'}
    for obj in objects: obj.name=names.get(obj.name.strip(),obj.name)
    archive=collection('SOURCE_PARTS'); block=bpy.data.objects['SRC_HipBlock']; move_to(block,archive)
    archive.hide_viewport=True; archive.hide_render=True
    block['reason_archived']='Rectangular temporary hip piece. The user body already contains a complete continuous pelvis beneath it.'
    for obj in list(bpy.data.collections['CHARACTER'].objects):
        if obj.type!='MESH': bpy.data.objects.remove(obj,do_unlink=True)
    bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=1
    bpy.context.scene['source_normalization']=json.dumps({'scale':scale,'floor':floor,'center_y':center_y})
    bpy.context.scene['forward_axis']='-Y'

def split_pairs():
    for name,stem in [('CHR_Eyes','CHR_Eye'),('CHR_Ears','CHR_Ear'),('CHR_Eyelids','CHR_Eyelid')]:
        original=bpy.data.objects[name]
        for side,label in ((1,'L'),(-1,'R')):
            obj=original.copy(); obj.data=original.data.copy(); collection('CHARACTER').objects.link(obj); obj.name=stem+'.'+label
            bm=bmesh.new(); bm.from_mesh(obj.data)
            bmesh.ops.delete(bm,geom=[v for v in bm.verts if side*v.co.x<0],context='VERTS')
            bm.to_mesh(obj.data); bm.free()
        bpy.data.objects.remove(original,do_unlink=True)

def setup_references():
    col=collection('REFERENCES')
    for category,suffix in REFERENCES.items():
        name=PREFIX+suffix+'.jpg'; dest=PROJECT/'references'/name
        if not dest.exists(): shutil.copy2(REFERENCE_SOURCE/name,dest)
        im=bpy.data.images.load(str(dest),check_existing=True); im.pack(); im.use_fake_user=True
        obj=bpy.data.objects.new('REF_'+category,None); col.objects.link(obj)
        obj.empty_display_type='IMAGE'; obj.data=im; obj.color[3]=.45; obj.empty_image_depth='BACK'; obj.hide_render=True
        obj['reference_category']=category
        if category in REFERENCE_ALIGNMENT:
            c=REFERENCE_ALIGNMENT[category]; ratio=c['height_px']; dx=(700-c['center_x_px'])/ratio; z=(c['floor_y_px']-500)/ratio
            obj.empty_display_size=1400/ratio
            if category=='FRONT': obj.location=(dx,.4,z); obj.rotation_euler=(math.pi/2,0,0)
            if category=='BACK': obj.location=(-dx,-.4,z); obj.rotation_euler=(math.pi/2,0,math.pi)
            if category=='SIDE': obj.location=(.4,-dx,z); obj.rotation_euler=(math.pi/2,0,-math.pi/2)
            obj.location+=Vector(c['offset'])
        else: obj.empty_display_size=.65; obj.location=(2,0,.2*len(col.objects)); obj.rotation_euler.x=math.pi/2
    col.hide_viewport=True; col.hide_render=True

def prepare_references():
    normalize_import(); split_pairs(); setup_references(); setup_studio()
    from reference_analysis import measure_references
    measure_references()
    (PROJECT/'output'/'normalized_inspection.json').write_text(json.dumps(inspect(),indent=2),encoding='utf-8')
    return 'Kept imported surfaces, applied world transforms and normalized to 1 m. Split paired eyes/ears/eyelids without rebuilding; archived the temporary hip block over the intact pelvis. Packed and aligned nine references.'
