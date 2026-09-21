import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from helpers import load_checkpoint
from face import group_vertices,original_head_point
load_checkpoint(3)
obj=bpy.data.objects['CHR_Body']
for name in ('Head / ears.L','Head / ear attachment.L','Arm.L','Hand / palm.L'):
    vs=group_vertices(obj,name)
    print(name,len(vs))
    if 'ears' in name:
        for v in vs: print(v.index,tuple(round(c,5) for c in original_head_point(v.co)))
