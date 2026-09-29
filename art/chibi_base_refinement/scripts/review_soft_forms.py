import bpy,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import *
from topology import cleanup_topology
from head_refinement import smoothstep
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_05_topology_cleanup.blend'))
head=bpy.data.objects['CHR_Head']
for v in head.data.vertices:
    x,y,z=v.co
    front=1-smoothstep(-.065,.015,y)
    forehead=smoothstep(.826,.855,z)*(1-smoothstep(.915,.958,z))
    target=-.117+.50*(z-.84)**2+.045*(x/.175)**4
    v.co.y+=(target-y)*forehead*front*.90
    cheek=math.exp(-(((abs(x)-.10)/.052)**4+((z-.710)/.035)**4))*front
    target=-.139+.045*(x/.175)**4
    v.co.y+=(target-v.co.y)*cheek*.70
head.data.update(); sync_basis(); cleanup_topology()
tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
for obj in meshes():
    if not obj.name.startswith('CHR_Eyebrow'): continue
    for v in obj.data.vertices:
        hit=tree.ray_cast(Vector((v.co.x,-1,v.co.z)),Vector((0,1,0)))[0]
        if hit: v.co.y=hit.y-.0017
save_checkpoint(5,'Smoothed source surface coordinates, softened forehead and cheek transitions without changing connectivity, and retained the symmetry/subdivision modifiers.',revision='b')
render_views(5)
