"""Refine the original Blender crystal into a separate semi-realistic prop."""
from pathlib import Path
import sys, json, math, hashlib, traceback
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/topazio_imperial/semi_realista'
OUT.mkdir(parents=True,exist_ok=True)
log=(OUT/'build.log').open('w',encoding='utf-8',buffering=1)
sys.stdout=log; sys.stderr=log
import bpy, bmesh
import numpy as np
from mathutils import Vector

def save_map(name,rgb,noncolor=False):
    size=rgb.shape[0]
    im=bpy.data.images.new(name,width=size,height=size,alpha=True)
    if noncolor: im.colorspace_settings.name='Non-Color'
    rgba=np.concatenate((np.clip(rgb,0,1),np.ones((size,size,1),dtype=np.float32)),axis=-1).astype(np.float32)
    assert np.isfinite(rgba).all()
    im.pixels.foreach_set(rgba.ravel()); im.filepath_raw=str(OUT/(name+'.png')); im.file_format='PNG'; im.save(); im.pack()
    return im

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/topazio_imperial/topazio_imperial.blend'))
    scene=bpy.context.scene
    obj=bpy.data.objects['Topazio_Imperial']; mesh=obj.data
    obj.name='Topazio_Imperial_SemiRealista'
    obj['asset_name']='topazio_imperial_semi_realista'
    obj['description']='Imperial topaz with growth striations, mineral inclusions, fractures and chipped edges.'
    # Small asymmetries retain the original prism silhouette.
    for v in mesh.vertices:
        x,y,z=v.co
        if 0.035<z<.69:
            v.co.x += .0014*math.sin(z*39+y*71)
            v.co.y += .0012*math.sin(z*31+x*83)
        if z>.66:
            v.co.z += .0018*math.sin(x*75+y*99)
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    # Actual subtractive chips rather than painted damage on an intact outline.
    chips=[((.140,-.073,.055),(.052,.045,.047),(.4,.2,.65)),
           ((-.132,-.087,.066),(.046,.034,.033),(.3,-.6,.3)),
           ((.136,-.084,.415),(.030,.027,.040),(.5,.3,-.6)),
           ((-.112,-.111,.594),(.027,.026,.036),(.4,.5,.5)),
           ((.106,-.059,.697),(.048,.042,.042),(.2,.5,.4)),
           ((-.068,.073,.715),(.038,.043,.035),(.6,.2,.2)),
           ((.125,.070,.093),(.041,.035,.044),(.7,.3,.6)),
           ((-.094,.099,.632),(.039,.037,.040),(.5,-.4,.3))]
    for k,(pos,dim,rot) in enumerate(chips):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.5,location=pos,rotation=rot)
        cutter=bpy.context.object; cutter.name=f'_temporary_chip_{k}'; cutter.dimensions=dim
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new(f'Natural chip {k}','BOOLEAN'); mod.operation='DIFFERENCE'; mod.solver='EXACT'; mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
    # Export the soft edge glints as mesh geometry, independent of Blender nodes.
    bevel=obj.modifiers.new('Micro bevel on fractured edges','BEVEL')
    bevel.width=.00065; bevel.segments=1; bevel.limit_method='ANGLE'; bevel.angle_limit=.45
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh)
    nonmanifold=sum(not e.is_manifold for e in bm.edges); volume=bm.calc_volume(signed=True); bm.free()
    assert nonmanifold==0 and volume>0
    mesh.update(); mesh.calc_loop_triangles(); assert len(mesh.loop_triangles)<=6000

    # PBR atlas, dense directional growth texture with sparse larger inclusions.
    n=2048; y,x=np.mgrid[0:n,0:n].astype(np.float32); u=x/(n-1); v=y/(n-1)
    sector=np.minimum((u*8).astype(int),7); t=u*8-sector; h=np.clip(v/.8,0,1)
    rng=np.random.default_rng(41261)
    def noise(scale_x,scale_y,seed):
        r=np.random.default_rng(seed); gx=int(scale_x)+2; gy=int(scale_y)+2
        grid=r.random((gy,gx),dtype=np.float32)
        sx=u*scale_x; sy=v*scale_y; ix=sx.astype(int); iy=sy.astype(int)
        fx=sx-ix; fy=sy-iy; fx=fx*fx*(3-2*fx); fy=fy*fy*(3-2*fy)
        return (grid[iy,ix]*(1-fx)+grid[iy,ix+1]*fx)*(1-fy)+(grid[iy+1,ix]*(1-fx)+grid[iy+1,ix+1]*fx)*fy
    coarse=noise(30,12,11); mid=noise(120,90,15); fine=noise(650,850,18); grain=noise(1650,1700,29)
    field=.52*coarse+.28*mid+.15*fine+.05*grain
    stops=[0,.13,.38,.66,.86,1]
    palette=np.array([[.34,.061,.007],[.73,.21,.014],[.96,.46,.048],
                      [.93,.52,.076],[.75,.22,.024],[.56,.10,.014]])
    color=np.stack([np.interp(h,stops,palette[:,i]) for i in range(3)],axis=-1).astype(np.float32)
    tint=np.array([1.0,.83,.91,.83,.99,.88,1.02,.88])[sector]
    color*=tint[...,None]
    color*= (.78+.47*field)[...,None]
    cloudy=np.clip((coarse-.48)*3,0,1)*np.clip(np.sin(h*np.pi),0,1)
    color+=cloudy[...,None]*np.array([.055,.075,.03])
    height=.022*mid+.0015*fine+.00015*grain+.010*noise(1300,30,37)
    stripes=np.zeros_like(u); bright=np.zeros_like(u)
    for i in range(28):
        pos=float(rng.uniform(.02,.98)); width=float(rng.uniform(.0012,.0050))
        path=pos+.006*np.sin(h*rng.uniform(4,15)+sector*rng.uniform(1,5))
        segment=np.clip((h-rng.uniform(0,.36))*15,0,1)*np.clip((rng.uniform(.65,1.1)-h)*15,0,1)
        groove=np.exp(-((t-path)/width)**2)*segment
        stripes+=groove*rng.uniform(.2,.7)
        bright+=np.exp(-((t-path-width*1.8)/(width*.8))**2)*segment*.25
    height-=stripes*.055; height+=bright*.025
    color*=np.clip(1-stripes*.34,.48,1)[...,None]
    color+=bright[...,None]*np.array([.05,.075,.042])
    cracks=np.zeros_like(u); cracklight=np.zeros_like(u)
    for k in range(5):
        anchor=rng.uniform(.15,.88)+.025*np.sin(sector*2.15+k)
        slope=rng.uniform(-.13,.13)
        path=anchor+(t-.5)*slope+.003*np.sin(t*45+k+sector)
        width=rng.uniform(.0009,.0015)
        mask=np.exp(-((t-rng.uniform(.25,.75))/rng.uniform(.16,.34))**6)
        cracks+=np.exp(-((h-path)/width)**2)*mask
        cracklight+=np.exp(-((h-path-width*2)/width)**2)*mask
    # Scattered shallow mineral scars, naturally concentrated near broken ends.
    scars=np.zeros_like(u)
    for k in range(43):
        cx=rng.uniform(.02,.98); cy=rng.uniform(.03,.98)
        rx=rng.uniform(.002,.012); ry=rng.uniform(.002,.009)
        spot=np.exp(-((t-cx)/rx)**2-((h-cy)/ry)**2)
        scars+=spot*(.4+coarse)
    enddamage=np.clip((.16-h)*6,0,1)+np.clip((h-.89)*7,0,1)
    roughareas=np.clip((mid-.54)*5,0,1)*enddamage
    height-=.027*cracks+.060*scars+.022*roughareas
    color*=np.clip(1-cracks*.40-scars*.25,.25,1)[...,None]
    color+=cracklight[...,None]*np.array([.065,.08,.047])
    color+=roughareas[...,None]*np.array([.045,.054,.038])
    cap=v>.82
    capcolor=np.array([.77,.24,.026])[None,None,:]*(.7+.6*field)[...,None]
    capcolor+=np.clip((coarse-.58)*3,0,1)[...,None]*np.array([.16,.13,.08])
    color=np.where(cap[...,None],capcolor,color)
    height=np.where(cap,.035*mid+.004*fine-.015*scars,height)
    rough=np.clip(.18+.18*field+.10*stripes+.20*scars+.12*enddamage,.18,.70)
    rough=np.where(cap,np.clip(.29+.32*mid,.29,.65),rough)
    # Tangent-space normal from atlas height, with conservative micro relief.
    dy,dx=np.gradient(height)
    normal=np.stack((-dx*n*.045,-dy*n*.045,np.ones_like(dx)),axis=-1)
    normal/=np.linalg.norm(normal,axis=-1)[...,None]
    maps={'basecolor':save_map('topazio_semi_basecolor',color),
          'roughness':save_map('topazio_semi_roughness',np.repeat(rough[...,None],3,axis=-1),True),
          'normal':save_map('topazio_semi_normal',normal*.5+.5,True)}
    mat=bpy.data.materials.new('Topazio | Semi-realista | Estrias e fraturas PBR'); mat.use_nodes=True
    mat.diffuse_color=(.88,.38,.06,1)
    nt=mat.node_tree; p=nt.nodes.get('Principled BSDF')
    p.inputs['Metallic'].default_value=0; p.inputs['IOR'].default_value=1.62
    p.inputs['Coat Weight'].default_value=.18; p.inputs['Coat Roughness'].default_value=.24
    p.inputs['Emission Strength'].default_value=.015
    for key,im in maps.items():
        tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=im; tex.label=key
        if key=='basecolor':
            nt.links.new(tex.outputs['Color'],p.inputs['Base Color']); nt.links.new(tex.outputs['Color'],p.inputs['Emission Color'])
        elif key=='roughness': nt.links.new(tex.outputs['Color'],p.inputs['Roughness'])
        else:
            node=nt.nodes.new('ShaderNodeNormalMap'); node.inputs['Strength'].default_value=.70
            nt.links.new(tex.outputs['Color'],node.inputs['Color']); nt.links.new(node.outputs['Normal'],p.inputs['Normal'])
    mesh.materials.clear(); mesh.materials.append(mat)
    for poly in mesh.polygons: poly.material_index=0; poly.use_smooth=False
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(OUT/'topazio_imperial_semi.glb'),export_format='GLB',
        use_selection=True,export_yup=True,export_apply=True,export_animations=False,
        export_cameras=False,export_lights=False,export_extras=True)
    # Preserve the existing simple collision envelope around the refined mesh.
    source=(ROOT/'art/topazio_imperial/topazio_imperial_prop.tscn').read_text(encoding='utf-8')
    (OUT/'topazio_imperial_prop.tscn').write_text(source.replace('topazio_imperial.glb','topazio_imperial_semi.glb'),encoding='utf-8')
    scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.cycles.samples=96
    scene.render.filepath=str(OUT/'topazio_imperial_semi_preview.png')
    bpy.context.preferences.filepaths.save_version=0
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type=='VIEW_3D': area.spaces.active.shading.type='MATERIAL'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'topazio_imperial_semi.blend'))
    print('MODEL_AND_PBR_EXPORTED',flush=True)
    bpy.ops.render.render(write_still=True)
    cam=scene.camera; cam.location=(-1.2,1.7,.94); aim(cam,(0,0,.35))
    scene.render.resolution_x=900; scene.render.resolution_y=1100; scene.cycles.samples=64
    scene.render.filepath=str(OUT/'topazio_imperial_semi_back.png'); bpy.ops.render.render(write_still=True)
    # Macro makes the real normal-map relief and chips inspectable.
    cam.location=(1.15,-1.75,1.02); aim(cam,(.03,-.06,.57)); cam.data.ortho_scale=.38
    scene.render.resolution_x=1100; scene.render.resolution_y=900
    scene.render.filepath=str(OUT/'topazio_imperial_semi_detalhe.png'); bpy.ops.render.render(write_still=True)
    data={'blender_version':bpy.app.version_string,'generator':'tools/topazio_imperial/refine_topazio.py',
        'source':'art/topazio_imperial/topazio_imperial.blend','style':'semi-realistic',
        'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'mesh_objects':1,'materials':1,
        'maps':['basecolor','roughness','normal'],'texture_resolution':[2048,2048],
        'dimensions_m':list(obj.dimensions),'nonmanifold_edges':nonmanifold,'volume_m3':volume,
        'alpha_mode':'OPAQUE','pivot':'base center','transmission':0,
        'prompt':'Mais texturas e imperfeicoes no topazio imperial; aspecto natural e semi-realista, mantendo a forma aprovada.',
        'negative_prompt':'Sem joia lapidada, sem ponta de quartzo, sem danos exagerados, sem ruido uniforme.',
        'license':'MIT, original procedural geometry and PBR textures, no reference pixels copied',
        'checks':{'closed_manifold':True,'positive_volume':True,'triangle_budget_6000':True,'finite_texture_pixels':True},'files':{}}
    for file in sorted(OUT.iterdir()):
        if file.suffix in ('.blend','.glb','.tscn','.png'):
            data['files'][file.name]={'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
    (OUT/'manifest.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(data,indent=2),flush=True); print('BUILD_COMPLETE',flush=True)

try: main()
except Exception:
    traceback.print_exc(); (OUT/'FAILED.txt').write_text(traceback.format_exc(),encoding='utf-8'); raise
finally: log.flush()
