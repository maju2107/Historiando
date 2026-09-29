import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import *
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/'character_03_proportion_fix.blend'))
save_checkpoint(3,'Synchronized the refined mesh coordinates with the Basis shape key so the imported-form backup remains inactive and validation displays the proportion edits. No second deformation applied.',revision='b')
render_views(3)
