import bpy,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import *
from topology import hand_overview
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_06_hands_feet.blend'))
obj=bpy.data.objects['CHR_Body']; idx=obj.vertex_groups['Added fourth finger.L'].index
vs=[v for v in obj.data.vertices if any(g.group==idx for g in v.groups)]
for row in range(8):
    ring=vs[row*12:(row+1)*12]; center=sum((v.co for v in ring),Vector())/12
    amount=1.10+.20*min(1,row/3); shift=Vector((0,-.011*(row/7),0))
    for v in ring: v.co=center+(v.co-center)*amount+shift
vs[-1].co.y-=.011; obj.data.update()
save_checkpoint(6,'Rounded the added little finger to match the source fingers and reduced its outward splay. Only eight palm faces were replaced; the three source fingers and thumb remain.',revision='b')
render_views(6); hand_overview(PROJECT/'renders'/'hand_after.png')
