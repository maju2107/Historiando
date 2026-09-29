import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import *
from proportions import fix_proportions
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_03b_proportion_fix.blend'))
for obj in meshes():
    key=obj.data.shape_keys.key_blocks['Imported form / normalized']
    for v,k in zip(obj.data.vertices,key.data): v.co=k.co
fix_proportions()
save_checkpoint(3,'Second proportion pass: replaced linear section interpolation with continuous cubic tangents to soften transitions while retaining the source connectivity and shape backup.',revision='c')
render_views(3)
