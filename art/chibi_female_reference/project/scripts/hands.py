"""Replace only the saved positive-X hand with four fingers and a thumb."""
import bpy,bmesh,math,cmath
from mathutils import Vector

def create_hands():
    obj=bpy.data.objects['CHR_Body']; bm=bmesh.new(); bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table(); deform=bm.verts.layers.deform.verify()
    arm_index=obj.vertex_groups['Arm.L'].index
    arm=[v for v in bm.verts if v[deform].get(arm_index,0)>.1]
    wrist=sorted(arm,key=lambda v:v.index)[-8:]
    center=sum((v.co for v in wrist),Vector())/8
    def angular_distance(a,b): return abs(math.atan2(math.sin(a-b),math.cos(a-b)))
    ordered=[]
    for k in range(8):
        target=(k-1)*math.pi/4
        ordered.append(min(wrist,key=lambda v:angular_distance(math.atan2(v.co.y-center.y,center.z-v.co.z),target)))
    if len(set(ordered))!=8: raise RuntimeError('Saved wrist is not an eight-vertex loop')
    wrist=ordered; barrier=set(wrist)
    palm_group=obj.vertex_groups['Hand / palm.L'].index
    seed=next(v for v in bm.verts if v[deform].get(palm_group,0)>.1)
    pending=[seed]; hand=set()
    while pending:
        v=pending.pop()
        if v in hand or v in barrier: continue
        if v.co.x<center.x-.03: raise RuntimeError('Hand traversal escaped wrist boundary')
        hand.add(v); pending.extend(e.other_vert(v) for e in v.link_edges)
    bmesh.ops.delete(bm,geom=list(hand),context='VERTS')

    groups={}
    def vertex(co,name):
        if name not in groups:
            group=obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name); groups[name]=group.index
        v=bm.verts.new(co); v[deform][groups[name]]=1.0; return v
    def bridge(a,b):
        for i in range(len(a)):
            j=(i+1)%len(a); bm.faces.new((a[i],a[j],b[j],b[i]))
    def cap(loop,name):
        v=vertex(sum((p.co for p in loop),Vector())/len(loop),name)
        for k in range(0,len(loop),2): bm.faces.new((v,loop[k],loop[(k+1)%len(loop)],loop[(k+2)%len(loop)]))

    section=([(-1,-1+i/4) for i in range(9)]+[(0,1)]+
             [(1,1-i/4) for i in range(9)]+[(0,-1)])
    palm=[]
    for row,(dist,width,thick) in enumerate(((.016,.030,.019),(.043,.044,.022),(.075,.052,.022),(.103,.050,.016))):
        ring=[]
        for u,v in section:
            x=center.x+dist
            if row==3: x+=.003-.010*((v+.10)/1.1)**2
            roundness=math.sqrt(max(.20,1-(.83*v)**2))
            co=Vector((x,center.y+v*width,center.z+u*thick*roundness+.003*math.sin(math.pi*row/4)))
            ring.append(vertex(co,'Hand / palm.L'))
        palm.append(ring)
    mapping=[(0,1,2),(3,4,5),(6,7,8),(9,),(10,11,12),(13,14,15),(16,17,18),(19,)]
    for k,indices in enumerate(mapping):
        j=(k+1)%8
        bm.faces.new((wrist[k],wrist[j],palm[0][mapping[j][0]],palm[0][indices[-1]]))
        if len(indices)==3: bm.faces.new((wrist[k],*[palm[0][i] for i in indices]))
    for row in range(3):
        for k in range(20):
            if row in (0,1) and k in (18,19): continue
            j=(k+1)%20; bm.faces.new((palm[row][k],palm[row][j],palm[row+1][j],palm[row+1][k]))

    def tube(loop,origin,tangent,profiles,name,curl=0):
        tangent=Vector(tangent).normalized()
        up=(Vector((0,0,1))-tangent*tangent.z).normalized()
        across=tangent.cross(up).normalized()
        root=sum((v.co for v in loop),Vector())/len(loop)
        angles=[math.atan2((v.co-root).dot(up),(v.co-root).dot(across)) for v in loop]
        turn=sum(math.atan2(math.sin(b-a),math.cos(b-a)) for a,b in zip(angles,angles[1:]+angles[:1]))
        sign=1 if turn>0 else -1
        phase=cmath.phase(sum(cmath.exp(1j*(a-sign*k*math.pi/4)) for k,a in enumerate(angles)))
        previous=loop; maxdist=profiles[-1][0]
        for dist,ry,rz in profiles:
            pos=Vector(origin)+tangent*dist-up*(curl*(dist/maxdist)**2)
            ring=[]
            for k in range(8):
                a=phase+sign*k*math.pi/4
                ring.append(vertex(pos+across*(ry*math.cos(a))+up*(rz*math.sin(a)),name))
            bridge(previous,ring); previous=ring
        cap(previous,name)

    end=palm[-1]; web={0:end[19],4:end[9]}
    for boundary in (1,2,3):
        co=(end[2*boundary].co+end[18-2*boundary].co)/2+Vector((.0015,0,0))
        web[boundary]=vertex(co,'Hand / webs.L')
    for f,(name,length,radius,splay) in enumerate((('index',.058,.0090,-.13),('middle',.066,.0095,-.025),
                                                 ('ring',.061,.0092,.05),('little',.049,.0080,.18))):
        a=2*f
        loop=[end[a],end[a+1],end[a+2],web[f+1],end[18-a-2],end[18-a-1],end[18-a],web[f]]
        origin=sum((v.co for v in loop),Vector())/8
        profiles=[(length*t,radius*factor,radius*.93*factor) for t,factor in
          ((.15,1.0),(.34,.99),(.43,.98),(.52,.94),(.67,.92),(.76,.89),(.86,.82),(.95,.62),(1,.20))]
        tube(loop,origin,(1,splay,-.12),profiles,'Finger / '+name+'.L',curl=.002)
    loop=[palm[0][18],palm[0][19],palm[0][0],palm[1][0],palm[2][0],palm[2][19],palm[2][18],palm[1][18]]
    origin=sum((v.co for v in loop),Vector())/8
    profiles=[(d,r,r*.90) for d,r in ((.014,.014),(.023,.0135),(.031,.013),(.040,.012),
                                    (.050,.0115),(.060,.0105),(.068,.0075),(.072,.003))]
    tube(loop,origin,(.56,-.80,-.21),profiles,'Finger / thumb.L',curl=.001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    for p in obj.data.polygons: p.use_smooth=True
    obj['digits_per_hand']='Four fingers plus one thumb; opposite hand supplied by Mirror.'
    return 'Replaced only hand geometry beyond the existing wrist. Built four separately articulated fingers plus a short rounded thumb, connected through a quad palm and webs; Mirror supplies the opposite hand. Feet retained after silhouette comparison.'
