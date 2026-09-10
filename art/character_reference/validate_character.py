import bpy, os, math, json
out=os.path.join(os.getcwd(),'art','character_reference')
assert bpy.data.objects.get('Head | shaped cheeks and chin') is not None
assert bpy.data.objects.get('Jumpsuit | continuous trousers') is not None
assert bpy.data.objects.get('Pony curl clump 284') is not None
images=[im for im in bpy.data.images if im.source=='FILE']
assert images and all(im.packed_file for im in images), 'Reference image must be packed'
meshes=[ob for ob in bpy.data.objects if ob.type=='MESH']
curves=[ob for ob in bpy.data.objects if ob.type=='CURVE']
for ob in meshes:
    assert len(ob.data.vertices)>0, ob.name
    assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co), ob.name
    assert len(ob.data.materials)>0, ob.name
for name in ['three_quarter','front','side','back']:
    assert os.path.getsize(os.path.join(out,name+'.png'))>10000
report={'blend_reopened':True,'packed_reference':True,'mesh_objects':len(meshes),'curve_objects':len(curves),'curl_clumps':len([ob for ob in meshes if ob.name.startswith('Pony curl clump')]),'rigged':False,'previews':['three_quarter.png','front.png','side.png','back.png']}
with open(os.path.join(out,'validation.json'),'w') as f: json.dump(report,f,indent=2)
print('MODEL_VALIDATED',json.dumps(report))

