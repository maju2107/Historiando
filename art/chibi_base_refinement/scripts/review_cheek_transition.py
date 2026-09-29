"""Locally relax the former orbital crease in the preserved dense source cage."""
import bpy,sys,math
import numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import sync_basis,save_checkpoint,render_views
from topology import relax_surface
from head_refinement import smoothstep
from validation import audit

bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_07b_validation.blend'))
head=bpy.data.objects['CHR_Head']
weights=[]
for vertex in head.data.vertices:
    x,y,z=vertex.co
    front=1-smoothstep(-.060,.005,y)
    weight=math.exp(-(((abs(x)-.078)/.054)**4+((z-.748)/.022)**4))*front
    weights.append(weight*smoothstep(.020,.041,abs(x)))
relax_surface(head,320,np.array(weights)); sync_basis()
if audit('07c_control',False)['issues'] or audit('07c_subdivision',True)['issues']:
    raise RuntimeError('Review cheek relaxation')
save_checkpoint(7,'Relaxed the original narrow lower-orbital crease into the rounded cheek; retained every source head face and the original nose/mouth structure.',revision='c')
render_views(7,1200)
