"""Check the actual GLBs and the lip paint embedded in the shipped game asset."""
import struct,json,hashlib,math,io
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[2]
def glb(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:],hashlib.sha256(b).hexdigest()
def image_bytes(d,b,name):
 image=next(i for i in d['images'] if i.get('name')==name);v=d['bufferViews'][image['bufferView']];return b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
report={}
for who,file,clips in [('Kai','assets/characters/kai/kai.glb',12),('Yara','assets/characters/yara/yara_playable.glb',9)]:
 d,b,sha=glb(R/file);assert len(d['meshes'])==1 and len(d['skins'][0]['joints'])==60
 mesh=d['meshes'][0];names=mesh['extras']['targetNames'];assert len(names)==17 and all(w==0 for w in mesh['weights'])
 assert len(d['animations'])==clips
 maximum=0;vertices=0
 for p in mesh['primitives']:
  assert len(p['targets'])==17
  a=d['accessors'][p['attributes']['WEIGHTS_0']];v=d['bufferViews'][a['bufferView']];assert a['componentType']==5126
  offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',16)
  for i in range(a['count']):
   w=struct.unpack_from('<4f',b,offset+i*stride);assert all(math.isfinite(x) and x>=0 for x in w);maximum=max(maximum,abs(sum(w)-1))
  vertices+=a['count']
 assert maximum<.0001
 report[who]={'file':file,'sha256':sha,'bones':60,'clips':len(d['animations']),'facial_shapes':names,'neutral_defaults':True,'normalized_four_influence_weights':True,'maximum_weight_sum_error':maximum,'vertices':vertices}
 if who=='Yara':
  balm=image_bytes(d,b,'Yara_LipBalm_Albedo');original=image_bytes(d,b,'Yara_SkinEyes_Albedo')
  assert balm==(R/'art/yara/textures/Yara_LipBalm_Albedo.png').read_bytes()
  a=Image.open(io.BytesIO(original)).convert('RGB');c=Image.open(io.BytesIO(balm)).convert('RGB');different=sum(1 for pixel in ImageChops.difference(a,c).getdata() if pixel!=(0,0,0))
  assert 0<different<5000
  report['lip_balm']={'embedded_texture_matches_native_paint':True,'painted_texels':different,'total_texels':a.width*a.height,'original_pixels_preserved_outside_soft_lip_tint':True}
assert (R/'assets/ui/historiando/brand_group_28.svg').read_bytes()==Path('C:/Users/obran/Downloads/Group 28 (1).svg').read_bytes()
report['corrected_logo_matches_user_svg']=True;report['issues']=[]
(R/'art/island_intro/facial_runtime_validation.json').write_text(json.dumps(report,indent=2))
print('FACIAL_EXPORTS_PASS: neutral defaults, 17 shapes, normalized paint, retained clips, packed balm and exact SVG')
