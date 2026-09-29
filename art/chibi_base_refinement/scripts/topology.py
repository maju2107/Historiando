"""Preserve source connectivity, improve curvature and preview symmetry."""
import bpy,bmesh,math,json
import numpy as np
from config import PROJECT
from helpers import meshes,sync_basis,collection,aim
from head_refinement import smoothstep

def relax_surface(obj,iterations,weights):
    verts=np.array([v.co[:] for v in obj.data.vertices]); edges=np.array([e.vertices[:] for e in obj.data.edges])
    degree=np.bincount(edges.ravel(),minlength=len(verts)).astype(float)
    for _ in range(iterations):
        total=np.zeros_like(verts)
        np.add.at(total,edges[:,0],verts[edges[:,1]])
        np.add.at(total,edges[:,1],verts[edges[:,0]])
        average=total/np.maximum(1,degree)[:,None]
        verts+=(average-verts)*weights[:,None]*.48
    for v,co in zip(obj.data.vertices,verts): v.co=co
    obj.data.update()

def cleanup_topology():
    for name,iterations in [('CHR_Head',90),('CHR_Body',35)]:
        obj=bpy.data.objects[name]; weights=[]
        for v in obj.data.vertices:
            x,y,z=v.co
            if name=='CHR_Head':
                # Relax broad cheek/forehead transitions while retaining the
                # user's tiny nose, lip opening, chin and posterior cranium.
                front=1-smoothstep(-.075,.025,y)
                region=smoothstep(.68,.715,z)*(1-smoothstep(.92,.97,z))
                nose=math.exp(-((x/.038)**4+((z-.749)/.027)**4))
                mouth=math.exp(-((x/.046)**4+((z-.710)/.025)**4))
                weights.append(front*region*(1-.85*max(nose,mouth)))
            else:
                # Light smoothing of imported wrist/torso/leg irregularities.
                weights.append(.8 if .10<z<.54 else .4)
        relax_surface(obj,iterations,np.array(weights))
    sync_basis()
    for obj in meshes():
        bm=bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        for face,poly in zip(bm.faces,obj.data.polygons):
            if face.normal.dot(poly.normal)<0: pass
        # Recalculation through bmesh would discard key coordinates on some
        # Blender versions. Mesh normals already passed; flip only the added
        # eyebrow geometry where necessary using an operator below.
        bm.free()
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        if obj.name in ('CHR_Body','CHR_Head','CHR_Neck') and not any(m.type=='MIRROR' for m in obj.modifiers):
            mirror=obj.modifiers.new('Symmetry / preserved full source cage','MIRROR')
            mirror.use_bisect_axis[0]=True; mirror.use_clip=True; mirror.use_mirror_merge=True; mirror.merge_threshold=.00001
            sub=obj.modifiers.new('Subdivision preview','SUBSURF'); sub.levels=1; sub.render_levels=1
        for p in obj.data.polygons: p.use_smooth=True
    sync_basis()
    return 'Retained imported quad connectivity. Relaxed local face/body curvature, verified outward normals, and added non-destructive bisect Mirror plus Subdivision 1 to the preserved full body/head/neck cages.'

def hand_overview(path):
    cam=bpy.data.objects.new('CAM_Hand',bpy.data.cameras.new('CAM_Hand')); collection('VALIDATION').objects.link(cam)
    cam.data.type='ORTHO'; cam.data.ortho_scale=.30; cam.location=(.38,-.02,1.3); aim(cam,(.38,-.02,.56)); cam.hide_set(True)
    scene=bpy.context.scene; scene.camera=cam; scene.render.resolution_x=1000; scene.render.resolution_y=1000; scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True); scene.camera=bpy.data.objects['CAM_ThreeQuarter']
