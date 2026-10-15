"""Inspect and package the separately saved semi-realistic revision."""
from pathlib import Path
import json,struct,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[2]
d=ROOT/'art/topazio_imperial/semi_realista'
b=(d/'topazio_imperial_semi.glb').read_bytes()
magic,version,length=struct.unpack_from('<4sII',b)
assert magic==b'glTF' and version==2 and length==len(b)
chunklen,kind=struct.unpack_from('<I4s',b,12)
assert kind==b'JSON'
g=json.loads(b[20:20+chunklen])
assert len(g['meshes'])==1 and len(g['materials'])==1
assert len(g['images'])>=3 and all('bufferView' in im for im in g['images'])
assert not any('uri' in buf for buf in g['buffers'])
mat=g['materials'][0]
assert mat.get('alphaMode','OPAQUE')=='OPAQUE'
assert 'normalTexture' in mat
assert 'baseColorTexture' in mat['pbrMetallicRoughness']
assert 'metallicRoughnessTexture' in mat['pbrMetallicRoughness']
triangles=sum(g['accessors'][p['indices']]['count']//3 for mesh in g['meshes'] for p in mesh['primitives'])
assert triangles<=6000
m=json.loads((d/'manifest.json').read_text(encoding='utf-8'))
assert triangles==m['triangles']
m['checks'].update({'glb_header_and_lengths':True,'embedded_pbr_maps':True,
    'godot_import_and_instantiation':f'Godot 4.7.1: one mesh, {triangles} triangles, color/normal/roughness maps, 32-point convex collision',
    'visual_review':'Blender hero and detail renders inspected'})
for file in d.iterdir():
    if file.name in ('README.md','LICENSE.txt'):
        m['files'][file.name]={'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
for name,receipt in m['files'].items():
    assert hashlib.sha256((d/name).read_bytes()).hexdigest()==receipt['sha256']
(d/'manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False),encoding='utf-8')
target=d/'topazio_imperial_semi_pacote.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(m['files']): archive.write(d/name,'topazio_imperial_semi/'+name)
    archive.write(d/'manifest.json','topazio_imperial_semi/manifest.json')
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
print(f'PBR_GLB_OK ARCHIVE_OK triangles={triangles} package_bytes={target.stat().st_size}')
