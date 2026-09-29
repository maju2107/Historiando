import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import *
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_01_import_cleanup.blend'))
for o in meshes():
    print('OBJECT',o.name,'PARENT',o.parent.name if o.parent else None,'WORLD',list(map(list,o.matrix_world)),'WORLD_BOUNDS',bounds([o]),flush=True)
setup_studio()
bpy.data.objects['quadril'].hide_render=True
render_views(0)
