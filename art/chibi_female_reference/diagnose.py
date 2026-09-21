import bpy,json,collections
from pathlib import Path
from mathutils import kdtree
out=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(out/'Chibi_Feminina.blend'))
obj=bpy.data.objects['Chibi - corpo e cabeca']; m=obj.data
rep=json.loads((out/'validation.json').read_text())
def group(p):
    c=collections.Counter(obj.vertex_groups[g.group].name for i in p.vertices for g in m.vertices[i].groups)
    return c.most_common(1)[0][0] if c else '?'
count=collections.Counter()
for a,b in rep['body_control']['self_intersections']:
    count[(group(m.polygons[a]),group(m.polygons[b]))]+=1
print('INTERSECTION GROUPS',count)
for a,b in rep['body_control']['self_intersections'][:8]:
    print('FACES',a,b,tuple(m.polygons[a].center),tuple(m.polygons[b].center))
kd=kdtree.KDTree(len(m.vertices))
for v in m.vertices: kd.insert(v.co,v.index)
kd.balance(); errors=[]
for v in m.vertices:
    co,i,d=kd.find((-v.co.x,v.co.y,v.co.z))
    if d>1e-5: errors.append((d,v.index,tuple(v.co),[obj.vertex_groups[g.group].name for g in v.groups]))
print('SYMMETRY',len(errors),sorted(errors,reverse=True)[:10])
print('COUNTS',[(k,len(rep[k]['self_intersections']),rep[k]['max_symmetry_error']) for k in ('body_control','body_subdivision')])
