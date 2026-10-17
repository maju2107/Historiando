"""Reflow concentric lips in the current sources; transfer the evaluated changes
to the painted game skins without rebaking or touching hair and clothing.
All inputs are the checkpoint made at the start of this revision.
"""
import bpy,bmesh,math,json,sys,traceback
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
W=Path('C:/Users/obran/Historiando_Backups/expressive_faces_2026-10-16')
OLD=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
SHAPES=['MouthOpen','MouthRound','Smile','Concern','BrowUp','BrowAsym','Blink','EyesWide','VisemeWide','VisemeU','LipPress','LipBite','Grin','Smirk','Sad','CheekRaise','Squint']
def log(s):W.joinpath('face_progress.txt').write_text(s);print(s,flush=True)
def cavity_material(who):
 m=bpy.data.materials.get(who+' / oral cavity') or bpy.data.materials.new(who+' / oral cavity')
 m.diffuse_color=(.045,.009,.020,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.85
 return m
def ink_material(name):
 m=bpy.data.materials.new(name);m.diffuse_color=(.012,.006,.010,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.68
 return m
LID_SHAPES=['Blink','EyesWide','Grin','CheekRaise','Squint','Smile','Smirk']
def fit_lid(p,old,shape,surface,margin=.001):
 if shape not in LID_SHAPES or old.y>-.075 or not .738<old.z<.838 or abs(abs(old.x)-.079)>.080 or abs(p.z-old.z)<.00015:return p
 hit,normal,index,distance=surface.ray_cast(Vector((p.x,-.25,p.z)),Vector((0,1,0)),.18)
 if hit is None and shape=='Blink':return old.copy()
 if hit is not None:p.y=min(p.y,hit.y-margin)
 return p
def closed_lash(p,target):
 target=target.copy();closure=.783+.003*(abs(p.x)-.079)/.055
 if p.z>=.786:target.z=closure-.0003+.0018*smooth((p.z-.797)/.018)+max(0,p.z-.824)*.5
 else:target.z=closure+.0003-.0014*smooth((.768-p.z)/.018)
 return target
def eye_geometry(who):
 vertices=[];polygons=[]
 if who=='Yara':
  o=bpy.data.objects['Yara_PaintedSkin'];polys=[p for p in o.data.polygons if p.material_index in [2,3]];ids=sorted({i for p in polys for i in p.vertices});lookup={old:new for new,old in enumerate(ids)}
  vertices=[list(o.data.vertices[i].co) for i in ids];polygons=[[lookup[i] for i in p.vertices] for p in polys]
 else:
  for o in [bpy.data.objects['KAI_Base_Eye.L'],bpy.data.objects['KAI_Base_Eye.R']]:
   clear_keys(o)
   states=[(m,m.show_viewport,getattr(m,'levels',None)) for m in o.modifiers]
   for m in o.modifiers:
    m.show_viewport=m.type in ['SUBSURF','MIRROR']
    if m.type=='SUBSURF':m.levels=1
   bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();offset=len(vertices)
   vertices.extend([list(o.matrix_world@v.co) for v in me.vertices]);polygons.extend([[i+offset for i in p.vertices] for p in me.polygons]);e.to_mesh_clear()
   for m,visible,level in states:
    m.show_viewport=visible
    if level is not None:m.levels=level
 return {'vertices':vertices,'polygons':polygons}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def clear_keys(o):
 if o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:k.value=0
  o.active_shape_key_index=0;o.show_only_shape_key=False
  for k in list(o.data.shape_keys.key_blocks)[::-1]:o.shape_key_remove(k)
 o.shape_key_add(name='Basis',from_mix=False)
def delta(p,kind,shape):
 x,y,z=p;v=Vector();front=smooth((-y-.085)/.045)
 # A tiny whole-globe retraction keeps the sclera behind the sealed corners;
 # its volume and UVs remain unchanged throughout the blink.
 if kind=='eye' and shape=='Blink':v.y=.004
 # Wide support for cheeks and jaw: no abrupt boundary around the lips.
 if kind=='skin':
  jaw=(1-smooth(abs(x)/.12))*(1-smooth(abs(z-.681)/.060))*front
  if shape=='MouthOpen':v.z-=.010*jaw;v.y+=.002*jaw
  if shape=='Grin':v.z-=.004*jaw
  cheek=(1-smooth(abs(abs(x)-.084)/.065))*(1-smooth(abs(z-.748)/.046))*front
  if shape in ['Smile','Grin','CheekRaise','Smirk']:
   a={'Smile':.006,'Grin':.009,'CheekRaise':.009,'Smirk':.004}[shape]
   v.z+=a*cheek;v.y-=.0018*cheek
 if kind in ['skin','brow']:
  brow=(1-smooth(abs(z-.844)/.034))*(1-smooth(abs(abs(x)-.083)/.068))*front
  if shape=='BrowUp':v.z+=.024*brow
  if shape in ['BrowAsym','Smirk']:v.z+=.018*brow*(1 if x>0 else -.40)
  if shape in ['Concern','Sad']:v.z+=.018*brow*(1-1.8*smooth(abs(x)/.14))
 if kind in ['skin','lash']:
  eye=(1-smooth(abs(abs(x)-.079)/.062))*front
  if .742<z<.837:
   if shape=='EyesWide':v.z+=(.017 if z>.786 else -.005)*eye*(1-smooth(abs(z-.792)/.050))
   if shape in ['CheekRaise','Squint','Grin']:
    a=.009 if shape!='Grin' else .004
    v.z+=(a if z<.786 else -a*.48)*eye*(1-smooth(abs(z-.785)/.050))
 # Keep the eyeball volume. The eyelid moves over it instead of squashing it.
 if shape=='Blink' and kind=='lash' and .738<z<.839:
  eye=(1-smooth(max(0,abs(abs(x)-.079)-.075)/.030))*smooth((-y-.065)/.030)
  closure=.783+.003*(abs(x)-.079)/.055
  v.z-=(z-closure)*.995*eye*(1-smooth(max(0,abs(z-.786)-.035)/.025))
 return v

def mouth_config(shape):
 # half width, opening half-height, corner elevation, centre displacement, pucker
 return {
 'Basis':(.029,.0018,.001,0,0),
 'MouthOpen':(.033,.020,.002,-.007,0),
 'MouthRound':(.019,.018,0,-.004,.004),
 'VisemeWide':(.041,.010,.004,-.002,0),
 'VisemeU':(.013,.010,0,-.003,.008),
 'LipPress':(.030,.0003,.001,.001,.001),
 'LipBite':(.033,.004,.002,.001,0),
 'Smile':(.036,.0018,.011,0,0),
 'Grin':(.041,.014,.010,-.003,0),
 'Smirk':(.034,.0018,0,0,0),
 'Concern':(.030,.0016,-.006,0,0),
 'Sad':(.030,.0017,-.009,-.002,.001),
 }.get(shape,(.029,.0018,.001,0,0))

def ring_position(r,j,shape,who):
 theta=-math.pi/2+j*math.pi/6;c=math.cos(theta);s=math.sin(theta)
 width,height,corner,cz,pucker=mouth_config(shape)
 center=.7025 if who=='Kai' else .7015
 # Five lip/support loops and two deep oral loops, evenly spaced in angle.
 widths=[.049,.037,width,width*.98,width*.86,width*.42]
 heights=[(.019 if s<0 else .0155),.010,height+.0015,height,height*.96,height*.70]
 # Outer loops carry a gradual fraction of the aperture and lip-corner motion.
 influence=[.18,.55,1,1,.92,.70][r]
 widths[0]+=(width-.029)*.18;widths[1]+=(width-.029)*.55
 heights[0]+=(height-.0018)*(.80 if s<0 else .28)
 heights[1]+=(height-.0018)*(.95 if s<0 else .65)
 x=widths[r]*c
 z=center+heights[r]*s+cz*influence+corner*c*c*influence
 if shape=='Smirk':z+=.011*c*c*influence
 # Match the surrounding face curvature instead of making a protruding lip
 # cylinder. The two outer rings blend into the cheeks and philtrum; the inner
 # rim has just 1.5 mm of soft relief. Lower support loops open with the jaw.
 face_y=(-.1395 if who=='Kai' else -.1425)+.020*(x/.13)**2+.006*((z-.710)/.070)**2
 if r<4:y=face_y-[0,.0006,.0015,-.0020][r]-pucker*influence
 else:y=([-.116,-.102][r-4]-(.003 if who=='Yara' else 0))+.004*c*c-pucker*influence
 return Vector((x,y,z))

def prepare_body(o,who,eyes=None):
 clear_keys(o);base=[v.co.copy() for v in o.data.vertices]
 for r,start in enumerate([1051,1058,1065,1072,1079,1086]):
  for j in range(7):o.data.vertices[start+j].co=ring_position(r,j,'Basis',who)
 # Restore the upper-lip / philtrum loop order to eliminate the folded quad.
 o.data.vertices[812].co.z=max(o.data.vertices[812].co.z,.727)
 o.data.vertices[1093].co=Vector((0,-.097,.7025 if who=='Kai' else .7015))
 for v in o.data.vertices:o.data.shape_keys.key_blocks['Basis'].data[v.index].co=v.co
 for name in SHAPES:
  key=o.shape_key_add(name=name,from_mix=False);key.value=0
  for v in o.data.vertices:key.data[v.index].co=v.co+delta(v.co,'skin',name)
  for r,start in enumerate([1051,1058,1065,1072,1079,1086]):
   for j in range(7):key.data[start+j].co=ring_position(r,j,name,who)
  if name=='Blink':
   # The authoring cage has seven 16-vertex orbital loops. Keep the outside
   # orbit (938..953), nose bridge and brow fixed; close the inner lid loops
   # over the globe with a gradual transition through the support loop.
   for i in range(954,1051):
    old=o.data.vertices[i].co;p=old.copy();closure=.783+.003*(abs(old.x)-.079)/.055
    amount=.40 if i<970 else 1.0
    overlap=(-.002 if old.z>closure else .002) if i<1002 else 0
    p.z=old.z+(closure+overlap-old.z)*amount;key.data[i].co=p
  if eyes:
   for v in o.data.vertices:key.data[v.index].co=fit_lid(key.data[v.index].co.copy(),v.co,name,eyes,.002)
 o['facial_lid_topology']='Fixed outer orbit; closing support/rim/backing loops 954..1050; eyeball profile correction'
 return base

def eval_mesh(o):
 bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();p=[v.co.copy() for v in m.vertices];e.to_mesh_clear();return p

def facial_groups(o,bones,indices=None):
 counts={'head_repainted':0,'lip_mask':0}
 for v in o.data.vertices:
  if indices is not None and v.index not in indices:continue
  x,y,z=v.co
  if y>-.075 or not .64<z<.89:continue
  lip=(1-smooth(abs(x)/.065))*(1-smooth(abs(z-.7015)/.044))*smooth((-y-.075)/.05)
  jaw=(1-smooth(abs(x)/.12))*(1-smooth(abs(z-.68)/.065))
  for name,w in [('Face_Lips',lip),('Face_Jaw',jaw),('Face_Cheek.L',max(0,x)*10*(1-smooth(abs(z-.75)/.055))),('Face_Cheek.R',max(0,-x)*10*(1-smooth(abs(z-.75)/.055)))]:
   if w>.0001:(o.vertex_groups.get(name) or o.vertex_groups.new(name=name)).add([v.index],min(1,w),'REPLACE')
  if lip>.001:counts['lip_mask']+=1
  # The whole facial surface follows the head; no neck spill into the chin/lips.
  if .65<z and abs(x)<.17:
   for g in list(v.groups):
    if o.vertex_groups[g.group].name in bones:o.vertex_groups[g.group].remove([v.index])
   (o.vertex_groups.get('Head') or o.vertex_groups.new(name='Head')).add([v.index],1,'REPLACE');counts['head_repainted']+=1
 return counts

def save_eval_fields(who):
 path=W/('kai_before.blend' if who=='Kai' else 'yara_before.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));name='KAI_Base_Body' if who=='Kai' else 'CHR_Body';o=bpy.data.objects[name]
 state=[(m,m.show_viewport,getattr(m,'levels',None)) for q in bpy.data.objects for m in q.modifiers]
 for q in bpy.data.objects:
  for m in q.modifiers:m.show_viewport=False
 for m in o.modifiers:
  if m.type=='MIRROR':m.show_viewport=True
  if m.type=='SUBSURF':m.show_viewport=True;m.levels=1
 eye_data=eye_geometry(who);eyes=BVHTree.FromPolygons(eye_data['vertices'],eye_data['polygons'])
 clear_keys(o);old=eval_mesh(o)
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();interior=sorted({i for p in me.polygons if p.material_index==1 for i in p.vertices});polygons=[list(p.vertices) for p in me.polygons];e.to_mesh_clear()
 prepare_body(o,who,eyes);o.data.materials[1]=cavity_material(who);new=eval_mesh(o);fields={'Basis':new}
 for name in SHAPES:
  k=o.data.shape_keys.key_blocks[name];k.value=1;fields[name]=eval_mesh(o);k.value=0
 assert len(old)==len(new)
 # Store a field from the exact original evaluated control cage.
 bpy.context.view_layer.update()
 data={'old':[list(p) for p in old],'interior':interior,'polygons':polygons,'eyes':eye_data,'fields':{n:[list(p) for p in ps] for n,ps in fields.items()}}
 W.joinpath(who.lower()+'_fields.json').write_text(json.dumps(data))
 # Source authoring retains the concentric quad cage and its editable masks.
 bones=set(bpy.data.objects['KAI_Rig' if who=='Kai' else 'YARA_Rig'].data.bones.keys())
 facial_groups(o,bones)
 if who=='Kai':
  tree=KDTree(len(new))
  for i,p in enumerate(new):tree.insert(p,i)
  tree.balance()
  for q in bpy.data.objects:
   kind='brow' if 'KAI_Base_Eyebrow.' in q.name else 'lash' if 'KAI_Connected cartoon lashes' in q.name else 'eye' if 'KAI_Base_Eye.' in q.name else ''
   if not kind:continue
   clear_keys(q)
   for name in SHAPES:
    k=q.shape_key_add(name=name,from_mix=False);k.value=0
    for v in q.data.vertices:
     p=q.matrix_world@v.co;d=delta(p,kind,name)
     if kind=='lash':
      near=tree.find_n(p,3);ws=[1/max(.00000001,a[2]**2) for a in near];total=sum(ws);d=sum(((fields[name][a[1]]-new[a[1]])*(w/total) for a,w in zip(near,ws)),Vector())
     target=p+d
     if kind=='lash' and name=='Blink':target=closed_lash(p,target)
     k.data[v.index].co=q.matrix_world.inverted()@target
    drv=k.driver_add('value').driver;var=drv.variables.new();var.name='expression';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=o.data.shape_keys;var.targets[0].data_path='key_blocks["'+name+'"].value';drv.expression='expression'
 # Restore visibility exactly as it was in the saved source, not the evaluator.
 # Other meshes were disabled for evaluation; recover their original flags.
 for m,visible,level in state:
  m.show_viewport=visible
  if level is not None:m.levels=level
 if who=='Kai':
  # Reloading a checkpoint for the runtime later leaves the source's viewport
  # modifier flags intact through an explicit checkpoint flag map.
  add_oral(o,bpy.data.objects['KAI_Rig'],who,join=False)
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/kai/kai.blend'))
 return data

def kind_for(name):
 if 'KAI_Base_Body' in name:return 'skin'
 if 'KAI_Base_Eye.' in name:return 'eye'
 if 'KAI_Base_Eyebrow' in name:return 'brow'
 if 'KAI_Connected cartoon lashes' in name:return 'lash'
 return ''

def paint_lip_balm(skin):
 # Paint in the existing skin UV space, with a soft vertex-derived mask. The
 # original pixels outside the lip footprint are copied without resampling.
 material=skin.data.materials[0]
 node=next(n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.image.name.lower())
 source=node.image;width,height=source.size
 # Use a fresh image: image.copy() retains stale packed PNG bytes, while
 # unpacking that copy can discard its pixels if the original path is absent.
 image=bpy.data.images.new('Yara / soft rose lip balm',width=width,height=height,alpha=True)
 image.colorspace_settings.name=source.colorspace_settings.name
 mask=np.zeros((height,width),dtype=np.float32)
 weights=[]
 for v in skin.data.vertices:
  x,y,z=v.co;w=(1-smooth((abs(x)-.013)/.023))*(1-smooth((abs(z-.7015)-.0013)/.0065))*smooth((-y-.10)/.035)
  weights.append(w)
 skin.data.calc_loop_triangles();uv=skin.data.uv_layers.active.data
 for tri in skin.data.loop_triangles:
  if skin.data.polygons[tri.polygon_index].material_index!=0:continue
  ws=np.array([weights[i] for i in tri.vertices])
  if max(ws)<.0001:continue
  ps=np.array([(uv[i].uv.x*(width-1),uv[i].uv.y*(height-1)) for i in tri.loops]);lo=np.maximum(np.floor(ps.min(axis=0)).astype(int),0);hi=np.minimum(np.ceil(ps.max(axis=0)).astype(int),[width-1,height-1])
  if np.any(hi<lo):continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));a,b,c=ps;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;t=1-u-v
  valid=(u>=-.001)&(v>=-.001)&(t>=-.001);value=np.where(valid,u*ws[0]+v*ws[1]+t*ws[2],0)
  block=mask[lo[1]:hi[1]+1,lo[0]:hi[0]+1];np.maximum(block,value,out=block)
 pixels=np.empty(width*height*4,dtype=np.float32);source.pixels.foreach_get(pixels);pixels=pixels.reshape((height,width,4));alpha=mask[:,:,None]*.36
 pixels[:,:,:3]=pixels[:,:,:3]*(1-alpha)+np.array([.72,.24,.28],dtype=np.float32)*alpha
 image.pixels.foreach_set(pixels.ravel());image.update();folder=R/'art/yara/textures';folder.mkdir(exist_ok=True)
 image.filepath_raw=str(folder/'Yara_LipBalm_Albedo.png');image.file_format='PNG';image.save();image.pack();node.image=image
 material['lip_finish']='Subtle rose balm; soft UV-painted boundary; existing skin painting retained outside lips'
 W.joinpath('lip_balm_paint.json').write_text(json.dumps({'image':image.name,'uv_layer':skin.data.uv_layers.active.name,'pixels_painted':int(np.count_nonzero(mask)),'maximum_tint_opacity':float(mask.max()*.36),'vector_link':[(l.from_node.name,l.from_socket.name) for l in node.inputs['Vector'].links]},indent=2))
 return int(np.count_nonzero(mask))

def add_oral(skin,rig,who,join=True):
 # Real curved mouth geometry: closed lips occlude the teeth at rest.
 # Teeth are a continuous simplified dental arch, not individual floating dots.
 made=[];center=.7025 if who=='Kai' else .7015
 for part,color in [('Teeth',(1,.89,.72,1)),('Tongue',(.65,.19,.28,1))]:
  verts=[];faces=[];N=20
  if part=='Teeth':
   for row in range(3):
    for i in range(N+1):
     u=(i/N*2-1);verts.append((.027*u,-.133+.005*u*u,center+.006-row*.0022+.0015*u*u))
   for row in range(2):
    for i in range(N):a=row*(N+1)+i;faces.append((a,a+1,a+N+2,a+N+1))
  else:
   verts=[(0,-.129,center-.0165)]
   for row in range(1,8):
    lat=-math.pi/2+row*math.pi/8
    for i in range(N):
     a=2*math.pi*i/N;verts.append((.018*math.cos(lat)*math.cos(a),-.129+.005*math.cos(lat)*math.sin(a),center-.013+.0035*math.sin(lat)))
   top=len(verts);verts.append((0,-.129,center-.0095))
   for i in range(N):faces.append((0,1+(i+1)%N,1+i));faces.append((top,1+6*N+i,1+6*N+(i+1)%N))
   for row in range(6):
    for i in range(N):a=1+row*N+i;b=1+row*N+(i+1)%N;faces.append((a,b,b+N,a+N))
  me=bpy.data.meshes.new(who+' / rounded '+part);me.from_pydata(verts,[],faces);me.update();q=bpy.data.objects.new(who+'_'+part,me);bpy.context.collection.objects.link(q)
  mat=bpy.data.materials.new(who+' / '+part);mat.diffuse_color=color;mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Roughness'].default_value=.58;q.data.materials.append(mat)
  for p in me.polygons:p.use_smooth=True
  q.vertex_groups.new(name='Head').add(list(range(len(verts))),1,'REPLACE');arm=q.modifiers.new('Head skin','ARMATURE');arm.object=rig
  q.shape_key_add(name='Basis',from_mix=False)
  # Rest geometry is completely tucked behind the closed lips.
  for v in q.data.shape_keys.key_blocks['Basis'].data:v.co.y+=.018
  for v in q.data.vertices:v.co.y+=.018
  for shape in SHAPES:
   k=q.shape_key_add(name=shape,from_mix=False);k.value=0
   expose=shape in ['MouthOpen','VisemeWide','Grin','LipBite']
   if expose:
    for i,p in enumerate(verts):k.data[i].co=Vector(p)
   if part=='Tongue' and shape=='MouthOpen':
    for p in k.data:p.co.z-=.004
  made.append(q)
 if join:
  bpy.ops.object.select_all(action='DESELECT');skin.hide_set(False);skin.select_set(True)
  for q in made:q.select_set(True)
  bpy.context.view_layer.objects.active=skin;bpy.ops.object.join()
 else:
  for q in made:
   for shape in SHAPES:
    drv=q.data.shape_keys.key_blocks[shape].driver_add('value').driver;v=drv.variables.new();v.name='expression';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=skin.data.shape_keys;v.targets[0].data_path='key_blocks["'+shape+'"].value';drv.expression='expression'

def runtime(who,data):
 if who=='Kai':
  bpy.ops.wm.open_mainfile(filepath=str(OLD/'runtime_uv.blend'));uv=bpy.data.objects['Kai_Skin'];parts={}
  for p in uv.data.polygons:
   kind=kind_for(uv.data.materials[p.material_index].name)
   if kind:parts.setdefault(kind,set()).update(p.vertices)
  bpy.ops.wm.open_mainfile(filepath=str(W/'kai_runtime_before.blend'));skin=bpy.data.objects['Kai_Skin'];rig=bpy.data.objects['KAI_Rig']
 else:
  bpy.ops.wm.open_mainfile(filepath=str(W/'yara_before.blend'));skin=bpy.data.objects['Yara_PaintedSkin'];rig=bpy.data.objects['YARA_Rig'];parts={}
  for p in skin.data.polygons:
   name=skin.data.materials[p.material_index].name.lower();kind='skin' if 'skin' in name or 'mouth' in name else 'lash' if 'eyebrow' in name else 'eye' if 'cartoon eye' in name else ''
   if kind:parts.setdefault(kind,set()).update(p.vertices)
  # Ink materials contain disconnected brows and lashes. Classify whole
  # connected components so the tips of long lashes never become eyebrows.
  black=parts.get('lash',set());adj={i:set() for i in black}
  for p in skin.data.polygons:
   if all(i in black for i in p.vertices):
    for a,b in p.edge_keys:adj[a].add(b);adj[b].add(a)
  unseen=set(black);brows=set()
  while unseen:
   start=unseen.pop();component={start};stack=[start]
   while stack:
    for j in adj[stack.pop()]:
     if j in unseen:unseen.remove(j);component.add(j);stack.append(j)
   heights=[skin.data.vertices[i].co.z for i in component]
   if sum(heights)/len(heights)>.835 and min(heights)>.822:brows.update(component)
  parts['brow']=brows;parts['lash']=black-brows
 for q in bpy.data.objects:
  for m in q.modifiers:m.show_viewport=False
 original=[v.co.copy() for v in skin.data.vertices];clear_keys(skin)
 old=[Vector(p) for p in data['old']];fields={n:[Vector(p) for p in ps] for n,ps in data['fields'].items()}
 eyes=BVHTree.FromPolygons(data['eyes']['vertices'],data['eyes']['polygons'])
 tree=KDTree(len(old))
 for i,p in enumerate(old):tree.insert(p,i)
 tree.balance();mapping={};distances=[]
 old_surface=BVHTree.FromPolygons(old,data['polygons']);mouth_correction={}
 lash_mapping={}
 for i in parts.get('lash',[]):
  p=original[i]
  near=tree.find_n(p,3);ws=[1/max(.00000001,a[2]**2) for a in near];total=sum(ws);lash_mapping[i]=[(a[1],w/total) for a,w in zip(near,ws)]
 for i in parts.get('skin',[]):
  p=original[i]
  if abs(p.x)<.19 and .64<p.z<.90 and p.y<-.075:
   near=tree.find_n(p,3);distances.append(near[0][2])
   if who=='Yara' and abs(p.x)<.047 and .674<p.z<.726:
    at,normal,face,dist=old_surface.find_nearest(p)
    if at is not None:
     falloff=(1-smooth(abs(p.x)/.048))*(1-smooth(abs(p.z-.7015)/.028))
     mouth_correction[i]=normal*normal.dot(p-at)*falloff*.95
   if near[0][2]<.00001:mapping[i]=[(near[0][1],1.0)]
   else:
    # Local interpolation keeps manual variations in the painted skin.
    ws=[1/max(.00000001,q[2]**2) for q in near];total=sum(ws);mapping[i]=[(q[1],w/total) for q,w in zip(near,ws)]
 def sample(i,name):
  d=Vector()
  for idx,w in mapping[i]:d+=(fields[name][idx]-old[idx])*w
  return d
 basis=skin.data.shape_keys.key_blocks['Basis']
 for i in mapping:skin.data.vertices[i].co=original[i]+sample(i,'Basis')-mouth_correction.get(i,Vector());basis.data[i].co=skin.data.vertices[i].co
 for name in SHAPES:
  k=skin.shape_key_add(name=name,from_mix=False);k.value=0
  for kind,ids in parts.items():
   for i in ids:
    p=original[i]
    if kind=='skin' and i in mapping:k.data[i].co=fit_lid(p+sample(i,name)-mouth_correction.get(i,Vector()),p,name,eyes)
    elif kind!='skin':
     d=delta(p,kind,name)
     if i in lash_mapping:d=sum(((fields[name][idx]-fields['Basis'][idx])*w for idx,w in lash_mapping[i]),Vector())
     target=skin.data.vertices[i].co+d
     if i in lash_mapping and name=='Blink':target=closed_lash(p,target)
     k.data[i].co=target
 body_polys=[list(p.vertices) for p in skin.data.polygons if all(i in parts['skin'] for i in p.vertices)]
 for name in LID_SHAPES:
  k=skin.data.shape_keys.key_blocks[name];surface=BVHTree.FromPolygons([v.co for v in k.data],body_polys)
  for i in lash_mapping:
   at,normal,face,dist=surface.find_nearest(k.data[i].co)
   if at is not None and dist<.007 and normal.y<-.05:k.data[i].co=at+normal*.00055
 # Give the throat its own stable dark material, rather than stretching baked
 # skin shading across the newly opened cavity.
 interior=set(data['interior']);cavity_ids={i for i,near in mapping.items() if near[0][0] in interior}
 slot=len(skin.data.materials);skin.data.materials.append(cavity_material(who))
 for p in skin.data.polygons:
  if all(i in cavity_ids for i in p.vertices):p.material_index=slot
 # Thin baked ink islands bled pale atlas gutters when the lids closed. Use
 # stable solid ink for lashes, retaining the painted brows on separate slots.
 if who=='Kai':
  ink_slot=len(skin.data.materials);skin.data.materials.append(ink_material('Kai / animated cartoon lashes'))
  for p in skin.data.polygons:
   if all(i in parts['lash'] for i in p.vertices):p.material_index=ink_slot
 else:
  for old_slot,side in [(4,'L'),(5,'R')]:
   brow=skin.data.materials[old_slot].copy();brow.name='Yara / painted eyebrow.'+side;brow_slot=len(skin.data.materials);skin.data.materials.append(brow)
   for p in skin.data.polygons:
    if p.material_index==old_slot and all(i in parts['brow'] for i in p.vertices):p.material_index=brow_slot
   skin.data.materials[old_slot]=ink_material('Yara / animated lashes / CHR_Eyebrow.'+side)
 counts=facial_groups(skin,set(rig.data.bones.keys()),parts.get('skin',set()))
 # Recover the mouth's quad ribbons from the triangulated painted skin. UV and
 # all shape-key layers are retained by BMesh; export triangulates as usual.
 bm=bmesh.new();bm.from_mesh(skin.data)
 fs=[f for f in bm.faces if len(f.verts)==3 and all(abs(v.co.x)<.055 and .66<v.co.z<.732 and v.co.y<-.09 for v in f.verts)]
 if fs:bmesh.ops.join_triangles(bm,faces=fs,angle_face_threshold=.7,angle_shape_threshold=.8,cmp_uvs=True,cmp_materials=True)
 bm.verts.ensure_lookup_table()
 patch=[f for f in bm.faces if all(v.index in parts['skin'] and abs(v.co.x)<.060 and .663<v.co.z<.729 and v.co.y<-.09 for v in f.verts)]
 edges=list({e for f in patch for e in f.edges});border={v for f in patch for v in f.verts if any(q not in patch for q in v.link_faces)}
 original_count=len(bm.verts)
 if edges:
  bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True)
  # Volume-preserving fairing across all absolute shape layers gives the lip
  # transition more resolution without moving hair, clothes or the face outline.
  movable=[v for v in bm.verts if v not in border and abs(v.co.x)<.060 and .663<v.co.z<.729 and v.co.y<-.09]
  layers=list(bm.verts.layers.shape.values())
  for layer in layers:
   for factor in [.40,-.42,.40,-.42]:
    updates=[]
    for v in movable:
     adjacent=[e.other_vert(v) for e in v.link_edges]
     if not adjacent:continue
     weight=(1-smooth(abs(v.co.x)/.065))*(1-smooth(abs(v.co.z-.7015)/.043))
     average=sum((q[layer] for q in adjacent),Vector())/len(adjacent);updates.append((v,v[layer]+(average-v[layer])*factor*weight))
    for v,p in updates:v[layer]=p
  basis_layer=bm.verts.layers.shape.get('Basis')
  if basis_layer:
   for v in bm.verts:v.co=v[basis_layer]
 added_lip_vertices=len(bm.verts)-original_count
 bm.to_mesh(skin.data);bm.free()
 add_oral(skin,rig,who)
 # Blender's join operator may copy the active shape values from its operands.
 # Runtime clips must start in neutral and never bake an expression as rest.
 for key in skin.data.shape_keys.key_blocks:key.value=0.0
 skin.active_shape_key_index=0
 # Restore rig modifiers, keep baked geometry helpers out of the export.
 for m in skin.modifiers:
  if m.type=='ARMATURE':m.show_viewport=True
 bpy.ops.object.select_all(action='DESELECT');skin.hide_set(False);skin.select_set(True);rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.context.preferences.filepaths.save_version=0
 if who=='Yara':
  # Keep the low-poly authoring cage updated as well as the painted skin.
  control=bpy.data.objects.get('CHR_Body')
  if control:prepare_body(control,who,eyes);control.data.materials[1]=cavity_material(who);facial_groups(control,set(rig.data.bones.keys()))
  paint_lip_balm(skin)
  bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/yara/yara.blend'))
  for a in list(bpy.data.actions):
   if a.name.startswith('RigCheck_'):bpy.data.actions.remove(a)
  target=R/'assets/characters/yara/yara_playable.glb'
 else:
  bpy.ops.wm.save_as_mainfile(filepath=str(W/'kai_game_export.blend'));target=R/'assets/characters/kai/kai.glb'
 log('Exporting '+who+' rounded lips and seventeen expressions')
 bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False,export_morph=True)
 return {'shapes':SHAPES,'face_weights':counts,'mapped_face_vertices':len(mapping),'maximum_mapping_distance':max(distances),'quad_mouth_faces':len(fs),'added_lip_vertices':added_lip_vertices,'vertex_count':len(skin.data.vertices),'outside_face_preserved':True}

def main():
 reports={}
 for who in ['Kai','Yara']:
  log('Reflowing '+who+' concentric lip cage');data=save_eval_fields(who);reports[who]=runtime(who,data)
 W.joinpath('face_build.json').write_text(json.dumps(reports,indent=2));log('Both facial sources and game exports saved')
if __name__=='__main__':
 try:main()
 except Exception:W.joinpath('face_error.txt').write_text(traceback.format_exc());raise
