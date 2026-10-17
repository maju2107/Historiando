"""Record the actual shipped GLB, texture sizes and canonical native manifest."""
import json,struct,hashlib,math
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[2];A=R/'art/kai';G=R/'assets/characters/kai'
data=(G/'kai.glb').read_bytes();size,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+size]);offset=20+size;bin_size,kind=struct.unpack_from('<II',data,offset);binary=data[offset+8:offset+8+bin_size]
components={5126:('f',4),5125:('I',4),5123:('H',2),5121:('B',1)};counts={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def values(index):
 a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']];fmt,width=components[a['componentType']];n=counts[a['type']];start=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',n*width)
 return [struct.unpack_from('<'+fmt*n,binary,start+i*stride) for i in range(a['count'])]
triangles=0;verts=0;maximum_error=0;unweighted=0
for mesh in doc['meshes']:
 for primitive in mesh['primitives']:
  attrs=primitive['attributes'];verts+=doc['accessors'][attrs['POSITION']]['count'];triangles+=doc['accessors'][primitive['indices']]['count']//3
  for row in values(attrs['WEIGHTS_0']):
   total=sum(row);maximum_error=max(maximum_error,abs(total-1));unweighted+=int(total<.001)
  assert all(all(math.isfinite(n) for n in row) for row in values(attrs['POSITION']))
clips=sorted(a['name'] for a in doc['animations']);shapes=doc['meshes'][0].get('extras',{}).get('targetNames',[])
assert len(clips)==12 and len(shapes)==17 and len(doc['skins'][0]['joints'])==60
assert maximum_error<.0001 and unweighted==0
report={'file':'assets/characters/kai/kai.glb','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'triangles':triangles,'vertices':verts,'bones':60,'clips':clips,'facial_shapes':shapes,'materials':len(doc.get('materials',[])),'maximum_influences':4,'maximum_weight_sum_error':maximum_error,'unweighted_vertices':unweighted,'textures':{p.name:Image.open(p).size for p in [G/'kai_albedo.png',G/'kai_orm.png']},'issues':[]}
(A/'runtime_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
files=[]
for p in sorted(A.rglob('*')):
 if not p.is_file() or p.name=='manifest.json' or p.suffix in ['.blend1','.blend2','.import']:continue
 b=p.read_bytes();files.append({'path':p.relative_to(A).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(A/'manifest.json').write_text(json.dumps({'asset':'Kai','source':'kai.blend','status':'Rigged, weighted and expressive island-cutscene NPC; runtime GLB and baked atlases installed','files':files,'runtime':report},indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
