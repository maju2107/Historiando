"""Render the current Kai source into an external inspection folder."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');WORK=Path('C:/Users/obran/Historiando_Backups/kai_finish_2026-10-16/review');WORK.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/kai/kai.blend'))
name=sys.argv[sys.argv.index('--')+1]
views={'front':((0,-3,.57),1.27,(0,0,.55)),'three_quarter':((1.8,-3,1.0),1.27,(0,0,.55)),'side':((3,0,.57),1.27,(0,0,.55)),'back':((0,3,.57),1.27,(0,0,.55)),'face':((0,-3,.88),.63,(0,-.02,.86)),'lower':((1.5,-3,.65),.62,(0,0,.26)),'lower_back':((1.5,3,.55),.62,(0,0,.26)),'lower_side':((3,0,.30),.62,(0,0,.26))}
pos,scale,target=views[name];s=bpy.context.scene;c=s.camera;c.data.ortho_scale=scale;c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=900;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=4;s.cycles.samples=24;s.render.filepath=str(WORK/f'{name}.png')
bpy.ops.render.render(write_still=True)
