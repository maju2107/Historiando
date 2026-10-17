"""Repair Kai's deformation weights, author gesture clips, bake a Godot skin.

The pre-rig editable source is checkpointed outside the repository. Runtime
geometry is built separately; the user's editable meshes are retained.
"""
import bpy,math,json,traceback,sys,shutil
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/kai';GAME=ROOT/'assets/characters/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
WORK.mkdir(exist_ok=True);GAME.mkdir(parents=True,exist_ok=True)
def log(t):
 (WORK/'progress.txt').write_text(t);print(t,flush=True)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def paint(o,idx,ws,bones):
 for g in list(o.data.vertices[idx].groups):
  if o.vertex_groups[g.group].name in bones:o.vertex_groups[g.group].remove([idx])
 ws=sorted([(n,w) for n,w in ws.items() if w>.00001],key=lambda a:-a[1])[:4];total=sum(w for n,w in ws)
 for n,w in ws:
  g=o.vertex_groups.get(n) or o.vertex_groups.new(name=n);g.add([idx],w/total,'REPLACE')
def assign(rig,action):
 rig.animation_data_create();rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
def rig_source():
 backup=WORK/'kai_before_rig.blend'
 if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));rig=bpy.data.objects['KAI_Rig'];bones=set(rig.data.bones.keys());report={'painted':{},'motions':[]}
 # Preserve the body paint and helper bones, limiting/normalizing deform weights.
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  changed=0
  for v in o.data.vertices:
   ws={o.vertex_groups[g.group].name:g.weight for g in v.groups if o.vertex_groups[g.group].name in bones}
   if not ws:continue
   if o.name=='KAI_Sleeveless tank':
    x,z=abs(v.co.x),v.co.z;side='L' if v.co.x>=0 else 'R';shoulder=smooth((z-.515)/.06)*smooth((x-.040)/.048)
    torso=smooth((z-.46)/.10);ws={'Chest':torso*(1-.42*shoulder),'Spine':(1-torso)*(1-.42*shoulder),'Clavicle.'+side:.24*shoulder,'UpperArm.'+side:.18*shoulder}
   elif o.name.startswith('KAI_Elbow strap '):
    side='L' if v.co.x>=0 else 'R';blend=smooth((abs(v.co.x)-.171)/.031);ws={'UpperArm.'+side:1-blend,'LowerArm.'+side:blend}
   elif o.name.startswith(('KAI_Violet elbow guard ','KAI_Pad spot ')):
    # A rigid pad follows the halfway helper instead of folding or sliding
    # entirely with either the upper arm or forearm.
    side='L' if (o.matrix_world@v.co).x>=0 else 'R';ws={'ElbowVolume.'+side:1.0}
   paint(o,v.index,ws,bones);changed+=1
  report['painted'][o.name]=changed
 for mod in bpy.data.objects['KAI_Base_Body'].modifiers:
  if mod.type=='ARMATURE':mod.use_deform_preserve_volume=True
 log('Weights repaired; sampling compatible locomotion')
 with bpy.data.libraries.load(str(ROOT/'art/yara/yara.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if n in ['Idle','Walk','Run','Jump','Fall','VictorySign']]
 donors=list(dst.actions);sampled={};s=bpy.context.scene
 for action in donors:
  name=action.name;assign(rig,action);frames=[]
  for f in range(int(action.frame_range[0]),int(action.frame_range[1])+1):
   s.frame_set(f);frames.append((f,{b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones}))
  sampled[name]=frames
 rig.animation_data_clear()
 for a in donors:bpy.data.actions.remove(a)
 def write_action(name,frames):
  a=bpy.data.actions.new(name);a.use_fake_user=True;assign(rig,a)
  for frame,poses in frames:
   for n,(loc,q,scale) in poses.items():
    pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
    for channel in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=channel,frame=frame,group=n)
  a['kai_clip']=True;report['motions'].append(name);return a
 for name,frames in sampled.items():write_action(name,frames)
 base=sampled['Idle'][0][1]
 def offset(poses,n,axis,angle):
  if n not in poses:return
  loc,q,sc=poses[n];local=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(axis);poses[n]=(loc,q@Quaternion(local,angle),sc)
 for name in ['Talk','Explain','Correct','Shrug','Point','React']:
  frames=[]
  for f in range(0,73,3):
   t=f/72;w=math.sin(math.pi*t)**1.2;poses={n:(l.copy(),q.copy(),sc.copy()) for n,(l,q,sc) in base.items()}
   offset(poses,'Spine',(1,0,0),.025*math.sin(t*2*math.pi));offset(poses,'Head',(1,0,0),w*(.04+.04*math.sin(t*4*math.pi)))
   if name in ['Talk','Explain','Point','Correct']:
    offset(poses,'UpperArm.R',(0,1,0),w*(.50 if name!='Point' else .80));offset(poses,'LowerArm.R',(0,0,1),w*(1.0 if name!='Correct' else 1.25))
    offset(poses,'Hand.R',(1,0,0),w*.18*math.sin(t*4*math.pi));offset(poses,'Head',(0,0,1),w*.10*math.sin(t*2*math.pi))
    if name in ['Correct','Point']:
     for finger in ['Middle','Ring','Little','Thumb']:
      for j in [1,2,3]:offset(poses,f'{finger}.{j}.R',(1,0,0),w*.45)
     for j in [1,2,3]:
      n=f'Index.{j}.R'
      if n in poses:l,q,sc=poses[n];poses[n]=(l,q.slerp(Quaternion(),w),sc)
   if name=='Shrug':
    for side,sg in [('L',1),('R',-1)]:
     offset(poses,'Clavicle.'+side,(0,1,0),-sg*w*.10);offset(poses,'UpperArm.'+side,(0,1,0),-sg*w*.48);offset(poses,'LowerArm.'+side,(0,0,1),-sg*w*1.0)
    offset(poses,'Head',(0,1,0),w*.10)
   if name=='React':
    offset(poses,'Head',(0,0,1),w*.23*math.sin(t*3*math.pi));offset(poses,'Chest',(1,0,0),-w*.10)
   frames.append((f,poses))
  write_action(name,frames)
 assign(rig,bpy.data.actions['Idle']);s.render.fps=30;s.frame_start=0;s.frame_end=72;s.frame_set(0);s['kai_rig_revision']='Normalized joint paint, shoulder/clavicle cloth gradients, elbow helper pads; locomotion and cinematic gestures'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'));(OUT/'rig_validation.json').write_text(json.dumps(report,indent=2));log('Rig source saved')
def runtime_geometry():
 bpy.ops.wm.open_mainfile(filepath=str(OUT/'kai.blend'));s=bpy.context.scene;rig=bpy.data.objects['KAI_Rig'];rig.data.pose_position='REST';s.frame_set(0)
 sources=[o for o in bpy.data.objects if o.type=='MESH'];parts=[]
 for o in sources:
  for m in o.modifiers:
   if m.type in ['ARMATURE','CLOTH']:m.show_viewport=False;m.show_render=False
   if m.type=='SUBSURF':m.levels=1 if ('Body' in o.name or 'shorts' in o.name or 'boot' in o.name.lower()) else 0
  o.hide_set(False);o.hide_viewport=False
 bpy.context.view_layer.update()
 for index,o in enumerate(sources):
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());data=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());p=o.copy();p.data=data;p.name='EXPORT_'+o.name;bpy.context.scene.collection.objects.link(p)
  for m in list(p.modifiers):p.modifiers.remove(m)
  # Freeze procedural coordinates before joining independently placed meshes.
  lo=Vector((min(v.co.x for v in data.vertices),min(v.co.y for v in data.vertices),min(v.co.z for v in data.vertices)));hi=Vector((max(v.co.x for v in data.vertices),max(v.co.y for v in data.vertices),max(v.co.z for v in data.vertices)))
  srcuv=data.uv_layers.active;uv=data.uv_layers.new(name='SourceUV')
  if srcuv:
   for a,b in zip(srcuv.data,uv.data):b.uv=a.uv
  for mi,mat in enumerate(list(data.materials)):
   cp=mat.copy();cp.name='Bake / '+o.name+' / '+str(mi);data.materials[mi]=cp;nt=cp.node_tree
   for node in list(nt.nodes):
    if node.type=='UVMAP':node.uv_map='SourceUV'
    if node.type!='TEX_COORD':continue
    for output_name in ['UV','Generated','Object']:
     links=list(node.outputs[output_name].links)
     if not links:continue
     if output_name=='UV':
      u=nt.nodes.new('ShaderNodeUVMap');u.uv_map='SourceUV';socket=u.outputs['UV']
     else:
      name='BakeCoord_'+str(mi)+'_'+node.name+'_'+output_name;attr=data.attributes.new(name,'FLOAT_VECTOR','POINT')
      for v,item in zip(data.vertices,attr.data):
       if output_name=='Generated':item.vector=Vector([(v.co[k]-lo[k])/max(1e-7,hi[k]-lo[k]) for k in range(3)])
       else:item.vector=node.object.matrix_world.inverted()@(p.matrix_world@v.co) if node.object else v.co
      a=nt.nodes.new('ShaderNodeAttribute');a.attribute_name=name;socket=a.outputs['Vector']
     for link in links:nt.links.new(socket,link.to_socket)
  p.select_set(False);bpy.context.view_layer.objects.active=p
  ratio=.22 if 'Clean flowing rear' in o.name else .38 if 'Cream sole' in o.name else .55 if any(q in o.name for q in ['lace','Lace','Eyelet','Pad spot']) else .72 if any('hair' in m.name.lower() for m in data.materials) else 1
  if ratio<1:
   dec=p.modifiers.new('Runtime silhouette budget','DECIMATE');dec.ratio=ratio;bpy.ops.object.modifier_apply(modifier=dec.name)
  parts.append(p)
  if index%35==0:log(f'Runtime geometry {index}/{len(sources)}')
 for o in sources:o.hide_set(True);o.hide_render=True
 bpy.ops.object.select_all(action='DESELECT')
 for p in parts:p.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();skin=bpy.context.object;skin.name='Kai_Skin'
 uv=skin.data.uv_layers.new(name='GameUV');skin.data.uv_layers.active=uv
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519,island_margin=.003,area_weight=.4,correct_aspect=True,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
 skin.data.calc_loop_triangles();log('UV atlas ready: '+str(len(skin.data.loop_triangles))+' triangles')
 bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'runtime_uv.blend'))
def bake_export():
 bpy.ops.wm.open_mainfile(filepath=str(WORK/'runtime_uv.blend'));s=bpy.context.scene;skin=bpy.data.objects['Kai_Skin'];rig=bpy.data.objects['KAI_Rig'];s.render.engine='CYCLES';s.cycles.samples=8;s.render.threads_mode='FIXED';s.render.threads=6
 s.render.bake.margin=12;s.render.bake.use_clear=True
 bpy.ops.object.select_all(action='DESELECT');skin.hide_set(False);skin.select_set(True);bpy.context.view_layer.objects.active=skin
 materials=list(skin.data.materials);saved=[]
 for m in materials:
  nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');shader=out.inputs['Surface'].links[0].from_node
  saved.append((m,shader))
 def bake(name,size,orm=False):
  image=bpy.data.images.new(name,width=size,height=size,alpha=False);image.colorspace_settings.name='Non-Color' if orm else 'sRGB'
  for m,shader in saved:
   nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;nt.nodes.active=tex
   em=nt.nodes.new('ShaderNodeEmission')
   if orm:
    combine=nt.nodes.new('ShaderNodeCombineColor');combine.inputs[0].default_value=1;combine.inputs[1].default_value=.72;combine.inputs[2].default_value=0
    for channel,param in [(1,'Roughness'),(2,'Metallic')]:
     if param in shader.inputs:
      socket=shader.inputs[param]
      if socket.is_linked:nt.links.new(socket.links[0].from_socket,combine.inputs[channel])
      else:combine.inputs[channel].default_value=socket.default_value
    nt.links.new(combine.outputs[0],em.inputs['Color'])
   else:
    socket=shader.inputs.get('Base Color') if shader.type=='BSDF_PRINCIPLED' else shader.inputs.get('Color')
    if socket:
     if socket.is_linked:nt.links.new(socket.links[0].from_socket,em.inputs['Color'])
     else:em.inputs['Color'].default_value=socket.default_value
   nt.links.new(em.outputs[0],out.inputs['Surface'])
  log('Baking '+name);bpy.ops.object.bake(type='EMIT');image.filepath_raw=str(GAME/(name+'.png'));image.file_format='PNG';image.save();return image
 color=bake('kai_albedo',4096);orm=bake('kai_orm',2048,True)
 mat=bpy.data.materials.new('Kai / Baked game atlas');mat.use_nodes=True;nt=mat.node_tree;p=nt.nodes.get('Principled BSDF');im=nt.nodes.new('ShaderNodeTexImage');im.image=color;nt.links.new(im.outputs['Color'],p.inputs['Base Color']);im2=nt.nodes.new('ShaderNodeTexImage');im2.image=orm;sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(im2.outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs[1],p.inputs['Roughness']);nt.links.new(sep.outputs[2],p.inputs['Metallic'])
 skin.data.materials.clear();skin.data.materials.append(mat)
 for poly in skin.data.polygons:poly.material_index=0
 for uv in list(skin.data.uv_layers):
  if uv.name!='GameUV':skin.data.uv_layers.remove(uv)
 skin.data.uv_layers.active=skin.data.uv_layers['GameUV'];skin.data.uv_layers.active.active_render=True
 mod=skin.modifiers.new('Kai game skin weights','ARMATURE');mod.object=rig;rig.data.pose_position='POSE';assign(rig,bpy.data.actions['Idle']);s.frame_set(0)
 bpy.ops.object.select_all(action='DESELECT');skin.hide_set(False);skin.select_set(True);rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'kai_game_export.blend'))
 log('Exporting skinned animations');bpy.ops.export_scene.gltf(filepath=str(GAME/'kai.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=False,export_materials='EXPORT',export_vertex_color='NONE',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_anim_single_armature=True,export_def_bones=False,export_rest_position_armature=True,export_skins=True,export_all_influences=False)
 skin.data.calc_loop_triangles();report={'triangles':len(skin.data.loop_triangles),'vertices':len(skin.data.vertices),'bones':len(rig.data.bones),'clips':[a.name for a in bpy.data.actions if a.get('kai_clip')],'albedo':4096,'orm':2048,'export':str(GAME/'kai.glb')};(OUT/'runtime_validation.json').write_text(json.dumps(report,indent=2));log('Completed Kai GLB and baked textures')
if __name__=='__main__':
 try:
  mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'all'
  if mode in ['rig','all']:rig_source()
  if mode in ['geometry','all']:runtime_geometry()
  if mode in ['bake','all']:bake_export()
 except Exception:
  (WORK/'error.txt').write_text(traceback.format_exc());raise
