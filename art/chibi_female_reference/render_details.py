"""Render additional inspection views without modifying the saved project."""
import bpy,sys
from pathlib import Path
from mathutils import Vector

out=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(out/'Chibi_Feminina.blend'))
scene=bpy.context.scene
camera=scene.camera
for obj in bpy.data.collections['02 · PREVIEW STUDIO'].objects:
    obj.hide_set(False)
scene.render.resolution_x=1200
scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.cycles.samples=32
for name,loc,target,scale in (
    ('hand_detail',(1.32,-1.10,4.5),(1.32,-.090,2.005),1.16),
    ('top_three_quarter',(0,-6.5,8),(0,0,1.80),4.10),
):
    if '--hand-only' in sys.argv and name!='hand_detail':
        continue
    camera.location=loc
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale
    scene.render.filepath=str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
print('DETAILS COMPLETE')
