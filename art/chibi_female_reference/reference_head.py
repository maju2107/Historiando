"""Reference-directed 32-column head with a quad-grid crown, not a pole fan."""
import math
from mathutils import Vector

def build_head(verts, faces, regions, neck, interp):
    def vertex(co, region):
        i=len(verts); verts.append(tuple(co)); regions.setdefault(region,[]).append(i)
        return i
    def hc(x,y,z):
        return (x*1.09,y*1.03,2.30+(z-2.465)*(1.30/1.135))
    def hv(co,region): return vertex(hc(*co),region)
    def bridge(a,b):
        assert len(a)==len(b)
        for i in range(len(a)):
            j=(i+1)%len(a); faces.append((a[i],a[j],b[j],b[i]))
    def cap(loop):
        center=vertex(sum((Vector(verts[i]) for i in loop),Vector())/len(loop),'Head / caps')
        for i in range(0,len(loop),2):
            faces.append((center,loop[i],loop[(i+1)%len(loop)],loop[(i+2)%len(loop)]))

    # These rows correspond to the chin, lips, nose, eyes and forehead lines
    # visible in the frontal reference, rather than uniform latitude bands.
    profiles=[(2.465,.205,.174,-.040),(2.520,.361,.296,-.020),
      (2.590,.446,.390,-.008),(2.660,.494,.434,-.006),
      (2.730,.533,.468,-.007),(2.820,.563,.500,-.008),
      (2.920,.579,.520,-.006),(3.020,.584,.523,-.003),
      (3.120,.575,.516,.004),(3.220,.545,.491,.012),
      (3.300,.495,.451,.018)]

    def face_y(x,z):
        rx=interp(z,[(p[0],p[1]) for p in profiles]); ry=interp(z,[(p[0],p[2]) for p in profiles])
        cy=interp(z,[(p[0],p[3]) for p in profiles]); c=min(.9999,abs(x)/rx)**(1/.92)
        y=cy-ry*max(0,1-c*c)**.325
        y-=.016*math.exp(-((abs(x)-.30)/.18)**2-((z-2.73)/.11)**2)
        return y

    # Frontal columns spaced from visible reference landmarks. Back columns
    # follow the same 32-column perimeter; the crown uses an 8x8 quad grid.
    angles=[math.tau*j/32 for j in range(32)]
    xx=[-.580,-.550,-.500,-.430,-.340,-.250,-.150,-.075,0,
         .075,.150,.250,.340,.430,.500,.550,.580]
    for j,x in enumerate(xx[:-1]):
        c=math.copysign((abs(x)/.580)**(1/.92),x) if x else 0
        angles[16+j]=math.tau-math.acos(max(-1,min(1,c)))

    head=[]; raw={}
    for z,rx,ry,cy in profiles:
        ring=[]
        for a in angles:
            sy=math.sin(a); cx=math.cos(a)
            x=rx*math.copysign(abs(cx)**.92,cx)
            y=cy+ry*math.copysign(abs(sy)**(.65 if sy<0 else .90),sy)
            if sy<-.65: y=face_y(x,z)
            i=hv((x,y,z),'Head / cranium'); raw[i]=(x,y,z); ring.append(i)
        head.append(ring)

    cuts=[('Eye.L',4,8,25,29),('Eye.R',4,8,19,23),
          ('Mouth',2,4,22,26),('Nose',4,6,23,25),
          ('Ear.L',3,7,31,33),('Ear.R',3,7,15,17)]
    for r in range(len(head)-1):
        for c in range(32):
            if any(r0<=r<r1 and c in [k%32 for k in range(c0,c1)] for _,r0,r1,c0,c1 in cuts):
                continue
            faces.append((head[r][c],head[r][(c+1)%32],head[r+1][(c+1)%32],head[r+1][c]))

    # 16 neck edges distribute into 32 head edges with three quads per sector.
    for k in range(8):
        b0,b1,b2=(neck[(2*k+j)%16] for j in range(3))
        t0,t1,t2,t3,t4=(head[0][(4*k+j)%32] for j in range(5))
        faces.extend(((b0,b1,t1,t0),(b1,t3,t2,t1),(b1,b2,t4,t3)))

    # Map an evenly spaced square grid onto the upper skull. It has no
    # high-valence vertex and no tiny triangles or compressed polar rings.
    def disk(u,v): return (u*math.sqrt(1-v*v/2),v*math.sqrt(1-u*u/2))
    perimeter=([(8,j) for j in range(4,9)]+[(i,8) for i in range(7,-1,-1)]+
               [(0,j) for j in range(7,-1,-1)]+[(i,0) for i in range(1,9)]+[(8,j) for j in range(1,4)])
    angle_knots=[]
    for j,(i,k) in enumerate(perimeter):
        x,y=disk((i-4)/4,(k-4)/4)
        a=math.atan2(y,x)%math.tau
        angle_knots.append((a,angles[j]))
    angle_knots.append((math.tau,math.tau))
    grid={ij:head[-1][j] for j,ij in enumerate(perimeter)}
    for i in range(1,8):
        for j in range(1,8):
            x,y=disk((i-4)/4,(j-4)/4); radius=math.hypot(x,y)
            a=interp(math.atan2(y,x)%math.tau,angle_knots)
            cx,sy=math.cos(a),math.sin(a)
            x=.495*radius*math.copysign(abs(cx)**.92,cx)
            y=.018+.451*radius*math.copysign(abs(sy)**(.65 if sy<0 else .90),sy)
            z=3.10+math.sqrt(.25-.21*radius*radius)
            grid[i,j]=hv((x,y,z),'Head / crown grid')
    for i in range(8):
        for j in range(8):
            faces.append((grid[i,j],grid[i+1,j],grid[i+1,j+1],grid[i,j+1]))

    def boundary(r0,r1,c0,c1):
        return ([head[r0][c%32] for c in range(c0,c1+1)]+[head[r][c1%32] for r in range(r0+1,r1+1)]+
                [head[r1][c%32] for c in range(c1-1,c0-1,-1)]+[head[r][c0%32] for r in range(r1-1,r0,-1)])

    eye_centers=[]
    for name,r0,r1,c0,c1 in cuts:
        previous=boundary(r0,r1,c0,c1)
        if name.startswith('Eye'):
            side=1 if name.endswith('L') else -1; cx=side*.268; cz=2.945
            aa=[math.atan2((raw[i][2]-cz)/.19,(raw[i][0]-cx)/.20) for i in previous]
            for rx,rz,mode,off in ((.180,.172,'face',-.001),(.167,.158,'face',-.007),
                  (.154,.147,'rim',0),(.152,.145,'rim',.007),
                  (.184,.187,'bowl',-.295),(.111,.114,'bowl',-.160),(.035,.036,'bowl',-.140)):
                ring=[]
                for a in aa:
                    x=cx+rx*math.cos(a); z=cz+rz*math.sin(a)
                    y=face_y(x,z)+off if mode=='face' else (-.503+side*.16*(x-cx)+off if mode=='rim' else off+side*.16*(x-cx))
                    ring.append(hv((x,y,z),'Head / eyelids & sockets.'+name[-1]))
                bridge(previous,ring); previous=ring
            cap(previous); eye_centers.append((side,(cx,-.446,cz)))
        elif name=='Mouth':
            cz=2.700
            aa=[math.atan2((raw[i][2]-cz)/.07,raw[i][0]/.17) for i in previous]
            for rx,rz,yy in ((.142,.026,None),(.108,.018,-.478),(.093,.0045,-.481),
                             (.087,.004,-.465),(.060,.009,-.410),(.021,.005,-.398)):
                ring=[]
                for a in aa:
                    x=rx*math.cos(a); z=cz+rz*math.sin(a)+.002*(x/rx)**2
                    y=face_y(x,z)-.002 if yy is None else yy
                    ring.append(hv((x,y,z),'Head / lips & mouth'))
                bridge(previous,ring); previous=ring
            cap(previous)
        elif name=='Nose':
            aa=[math.atan2((raw[i][2]-2.822)/.10,raw[i][0]/.086) for i in previous]
            for rx,rz,yy in ((.079,.063,-.516),(.065,.045,-.542),(.044,.028,-.567),(.018,.012,-.572)):
                ring=[hv((rx*math.cos(a),yy,2.817+rz*math.sin(a)),'Head / nose') for a in aa]
                bridge(previous,ring); previous=ring
            cap(previous)
        else:
            side=1 if name.endswith('L') else -1
            center=Vector((side*.624,0,2.847)); axis=Vector((side*.65,.760,0)); normal=Vector((side*.760,-.65,0))
            aa=[math.atan2((raw[i][2]-2.847)/.12,raw[i][1]/.09) for i in previous]
            attachment=[]
            for idx,a in zip(previous,aa):
                u=.122*math.cos(a)*(1+.10*math.sin(a))+.09*.183*math.sin(a)
                target=center+axis*u+Vector((0,0,.183*math.sin(a)))
                co=Vector(raw[idx])*.82+target*.18
                attachment.append(hv(co,'Head / ear attachment.'+name[-1]))
            bridge(previous,attachment); previous=attachment
            for rx,rz,depth in ((.122,.183,0),(.112,.176,.032),(.083,.147,.050),
                               (.058,.111,-.006),(.037,.068,-.041),(.015,.027,-.046)):
                ring=[]
                for a in aa:
                    u=rx*math.cos(a)*(1+.10*math.sin(a))+.09*rz*math.sin(a)
                    co=center+axis*u+Vector((0,0,rz*math.sin(a)))+normal*depth
                    if rx<=.058:
                        angle=math.atan2(math.sin(a-math.pi),math.cos(a-math.pi))
                        tragus=math.exp(-(angle/.70)**2)*(rx/.058)
                        co+=normal*(.081*tragus)+axis*(.023*tragus)
                    ring.append(hv(co,'Head / ears.'+name[-1]))
                bridge(previous,ring); previous=ring
            cap(previous)
    return hc,hv,face_y,eye_centers
