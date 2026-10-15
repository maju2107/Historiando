"""Verify the original packaged prop before copying its runtime bytes."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'art/topazio_imperial/semi_realista'
destination=ROOT/'assets/props/topazio_imperial'
manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
assert manifest['license'].startswith('MIT')
assert all(manifest['checks'][k] for k in ('closed_manifold','embedded_pbr_maps','godot_import_and_instantiation'))
with zipfile.ZipFile(source/'topazio_imperial_semi_pacote.zip') as package:
    assert package.testzip() is None
    for name,entry in manifest['files'].items():
        data=package.read('topazio_imperial_semi/'+name)
        assert hashlib.sha256(data).hexdigest()==entry['sha256']
        assert (source/name).read_bytes()==data
assert destination.resolve().is_relative_to(ROOT.resolve())
assert not destination.is_symlink()
destination.mkdir(parents=True,exist_ok=True)
files={}
for name in ('topazio_imperial_semi.glb','LICENSE.txt'):
    target=destination/name
    digest=hashlib.sha256((source/name).read_bytes()).hexdigest()
    if target.exists():
        assert hashlib.sha256(target.read_bytes()).hexdigest()==digest,'Existing asset differs'
    else: shutil.copyfile(source/name,target)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==digest
    files[name]={'sha256':digest,'bytes':target.stat().st_size}
receipt={'source_package':'art/topazio_imperial/semi_realista/topazio_imperial_semi_pacote.zip',
    'source_manifest_sha256':hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest(),
    'destination':'assets/props/topazio_imperial','license':'MIT','triangles':manifest['triangles'],
    'texture_resolution':manifest['texture_resolution'],'files':files,
    'provenance':'Original Blender geometry and procedural PBR maps; no photograph pixels copied',
    'integrity':'Archive CRC and complete source hash roster verified before copying; destination bytes matched'}
(destination/'asset_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print('TOPAZIO_VENDOR_OK',destination,'triangles=',manifest['triangles'])
