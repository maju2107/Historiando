# Rounded, continuous scalp with seven gently fluted swept-back rolls.
verts=[];faces=[];n=160;nr=72
for i in range(nr+1):
    for j in range(n):
        t=2*pi*j/n;front=max(0,-sin(t))
        lobe=(.5+.5*cos(7*pi*cos(t)))**2
        edge=1.97-.83*front+.023*front*lobe
        ph=.003+(edge-.003)*i/nr
        lift=.013+.046*lobe*front*(sin(ph)**.8)*math.exp(-((ph-.83)/.67)**2)
        # Rolls grow out of the scalp; there are no floating flat-ended strips.
        verts.append(((HX+lift)*sin(ph)*cos(t),-.006+(HY+lift)*sin(ph)*sin(t),HZ+(HH+lift)*cos(ph)))
for i in range(nr):
    for j in range(n):
        a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
ob=mesh('Slicked-back rounded rolls',verts,faces,slick,'03_HAIR',1)
m=ob.modifiers.new('Soft hairline thickness','SOLIDIFY');m.thickness=.023
m=ob.modifiers.new('Rounded hairline','BEVEL');m.width=.011;m.segments=3
