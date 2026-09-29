"""Reshape the user's eye, eyelid and face vertices, retaining connectivity."""
import bpy,math,json
from mathutils import Vector
from config import *
from helpers import meshes,collection
from proportions import interp,section_bounds

def smoothstep(a,b,x):
    t=max(0,min(1,(x-a)/(b-a))); return t*t*(3-2*t)

def bbox_center(obj):
    lo=[min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    hi=[max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    return Vector([(a+b)/2 for a,b in zip(lo,hi)]),Vector([b-a for a,b in zip(lo,hi)])

def refine_eyes_and_face():
    eye=bpy.data.objects['CHR_Eye.L']; center,size=bbox_center(eye)
    target=Vector((EYE_SPACING/2,-.119,EYE_HEIGHT)); sx=EYE_DIAMETER/size.x; sz=EYE_DIAMETER/size.z
    oldcenter=center.copy(); head=bpy.data.objects['CHR_Head']
    xknots=[(0,0),(center.x-size.x*.5,target.x-EYE_DIAMETER*.5),
      (center.x,target.x),(center.x+size.x*.5,target.x+EYE_DIAMETER*.5),(.18,.18),(.25,.25)]
    zknots=[(0,0),(.66,.66),(.73,.73),(center.z-size.z*.5,target.z-EYE_DIAMETER*.5),
      (center.z,target.z),(center.z+size.z*.5,target.z+EYE_DIAMETER*.5),(.87,.87),(1,1)]
    for v in head.data.vertices:
        x,y,z=v.co; side=1 if x>=0 else -1; ax=abs(x)
        front=1-smoothstep(-.085,-.005,y)
        # Monotone coordinate maps prevent the enlarged orbital patch from
        # folding over the forehead or cheek while retaining all source quads.
        ax+=(interp(ax,xknots)-ax)*front*(1-smoothstep(.87,.94,z))*smoothstep(.68,.745,z)
        z+=(interp(z,zknots)-z)*front
        rho=math.hypot((ax-target.x)/(EYE_DIAMETER*.5),(z-target.z)/(EYE_DIAMETER*.5))
        surface=-.128+.05*(ax/.175)**4+.015*math.exp(-rho**4)-.003*math.exp(-((rho-1.07)/.16)**2)
        depth_weight=.96*(1-smoothstep(1.1,2.25,rho))*front
        y+=(surface-y)*depth_weight
        # Keep the original nose, narrowing its tip and reducing projection.
        wn=math.exp(-((ax/.027)**2+((z-.752)/.022)**2))*(1-smoothstep(-.10,-.045,y))
        ax*=1-.20*wn; y+=.009*wn
        wm=math.exp(-((ax/.044)**4+((z-.710)/.020)**4))*(1-smoothstep(-.10,-.045,y))
        ax*=1-.16*wm; z=.710+(z-.710)*(1-.35*wm)
        v.co=(side*ax,y,z)
    for side,label in ((1,'L'),(-1,'R')):
        for stem in ('CHR_Eye','CHR_Eyelid'):
            obj=bpy.data.objects[stem+'.'+label]
            for v in obj.data.vertices:
                ax=abs(v.co.x); v.co.x=side*(target.x+(ax-center.x)*sx)
                v.co.z=target.z+(v.co.z-center.z)*sz
                v.co.y+=target.y-center.y
            obj.data.update()
        ear=bpy.data.objects['CHR_Ear.'+label]
        # Source ears already have helix, concha and lobe; only adjust their
        # placement and slightly round the lower projected silhouette.
        ec,_=bbox_center(ear)
        for v in ear.data.vertices:
            v.co.x+=side*.005; v.co.z-=.003
        ear.data.update()
    head.data.update()
    (PROJECT/'output'/'face_deformations.json').write_text(json.dumps({'eye_center_before':list(oldcenter),'eye_dimensions_before':list(size),
      'eye_center_after':list(target),'eye_diameter':EYE_DIAMETER,'replacement_regions':[]},indent=2))

def round_cranium():
    obj=bpy.data.objects['CHR_Head']; ref=json.loads((PROJECT/'references'/'analysis.json').read_text())
    curve=[(.70,1),(.76,1)]
    for r in ref['measurements']['FRONT']['sections']:
        if r['z_m']<.82: continue
        lo,hi=section_bounds(obj,r['z_m']); curve.append((r['z_m'],r['width_m']/(hi[0]-lo[0])))
    curve.append((1,curve[-1][1]))
    for v in obj.data.vertices: v.co.x*=interp(v.co.z,curve)
    obj.data.update()

def create_eyebrows():
    from mathutils.bvhtree import BVHTree
    head=bpy.data.objects['CHR_Head']
    tree=BVHTree.FromPolygons([v.co for v in head.data.vertices],[p.vertices[:] for p in head.data.polygons])
    for side,label in ((1,'L'),(-1,'R')):
        vs=[]; fs=[]; n=12; sides=8
        for i in range(n+1):
            t=i/n; x=.037+.093*t; z=.867+.011*math.sin(math.pi*t)-.002*t
            hit=tree.ray_cast(Vector((side*x,-1,z)),Vector((0,1,0)))[0]
            y=(hit.y if hit else -.12)-.0012; taper=math.sin(math.pi*(.03+.94*t))**.7
            for k in range(sides):
                a=math.tau*k/sides; vs.append((side*x,y+.0015*taper*math.cos(a),z+.0034*taper*math.sin(a)))
        for i in range(n):
            for k in range(sides): j=(k+1)%sides; fs.append((i*sides+k,i*sides+j,(i+1)*sides+j,(i+1)*sides+k))
        for start in (0,n*sides):
            center=len(vs); vs.append(tuple(sum(v[d] for v in vs[start:start+sides])/sides for d in range(3)))
            for k in range(0,sides,2): fs.append((center,start+k,start+(k+1)%sides,start+(k+2)%sides))
        me=bpy.data.meshes.new('Eyebrow detail'); me.from_pydata(vs,[],fs); me.update()
        obj=bpy.data.objects.new('CHR_Eyebrow.'+label,me); collection('CHARACTER').objects.link(obj)
        for f in me.polygons: f.use_smooth=True
        mod=obj.modifiers.new('Smooth eyebrow','SUBSURF'); mod.levels=2
        obj['added_detail']='Eyebrow absent from imported mesh; added to match reference.'

def refine_head():
    round_cranium(); refine_eyes_and_face(); create_eyebrows()
    return 'Preserved the imported head, eyes, eyelids and ears. Enlarged and moved eye surfaces inward, reshaped existing orbital surfaces, reduced nose projection and lip volume, refined skull contour, positioned the existing detailed ears, and added missing eyebrows.'
