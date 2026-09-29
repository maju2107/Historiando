"""Restore the user's rounded lower face, retaining the enlarged eye region."""
import bpy, sys, math
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import PROJECT
from helpers import sync_basis, save_checkpoint, render_views
from head_refinement import smoothstep
from topology import relax_surface

INPUT_CHECKPOINT = 'character_07_validation.blend'
ROUNDED_SOURCE_CHECKPOINT = 'character_03c_proportion_fix.blend'
CHEEK_RESTORE_END_Z = .769
CHEEK_RESTORE_FULL_Z = .728

def refine_lower_face():
    head = bpy.data.objects['CHR_Head']
    with bpy.data.libraries.load(str(PROJECT/'output'/ROUNDED_SOURCE_CHECKPOINT), link=False) as (source, target):
        target.objects = ['CHR_Head']
    previous = target.objects[0]
    assert len(head.data.vertices) == len(previous.data.vertices)
    for vertex, original in zip(head.data.vertices, previous.data.vertices):
        source = original.co.copy()
        x, y, z = source
        front = 1-smoothstep(-.065, .005, y)
        nose = math.exp(-((x/.033)**2 + ((z-.752)/.026)**2))*front
        source.x *= 1-.14*nose
        source.y += .0055*nose
        mouth = math.exp(-((x/.048)**4 + ((z-.710)/.024)**4))*front
        source.x *= 1-.13*mouth
        source.z = .710+(source.z-.710)*(1-.24*mouth)
        restore = (1-smoothstep(CHEEK_RESTORE_FULL_Z, CHEEK_RESTORE_END_Z, z))*front
        # Restore the nose too, where the original is a rounded projection.
        restore = max(restore, nose*.95)
        vertex.co = vertex.co.lerp(source, restore)
    bpy.data.objects.remove(previous, do_unlink=True)
    weights=[]
    for v in head.data.vertices:
        x,y,z=v.co
        front=1-smoothstep(-.06,.01,y)
        region=smoothstep(.66,.69,z)*(1-smoothstep(.78,.80,z))
        detail=math.exp(-((x/.042)**4+((z-.725)/.048)**4))
        weights.append(front*region*(1-.92*detail))
    relax_surface(head,55,np.array(weights))
    sync_basis()

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'output'/INPUT_CHECKPOINT))
    refine_lower_face()
    from validation import audit
    if audit('07b_control',False)['issues'] or audit('07b_subdivision',True)['issues']:
        raise RuntimeError('Review lower-face deformation before checkpoint')
    save_checkpoint(7,'Restored the rounded lower-face curvature from the preserved user mesh, with localized nose and mouth reductions. Removed the flattened cheek ledge without replacing head topology.',revision='b')
    render_views(7,1200)

if __name__=='__main__': main()
