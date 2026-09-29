import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import *
from proportions import fit_head_block
from head_refinement import refine_head
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_04b_head_refine.blend'))
for obj in list(meshes()):
    if obj.name.startswith('CHR_Eyebrow'): bpy.data.objects.remove(obj,do_unlink=True); continue
    if obj.name=='CHR_Body': continue
    original=obj.data.shape_keys.key_blocks['Imported form / normalized']
    for v,k in zip(obj.data.vertices,original.data): v.co=k.co
fit_head_block(); refine_head()
save_checkpoint(4,'Confined orbital movement to the front of the face, preserved the side silhouette and chin, and fitted the cranium before moving facial features. Source head topology retained.',revision='c')
render_views(4)
