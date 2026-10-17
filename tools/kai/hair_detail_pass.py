"""Current-source hair detail pass: marked curls, fine lower strands, directional fibers."""
import bpy,math,json,shutil,traceback,importlib.util
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_work_2026-10-15')
spec=importlib.util.spec_from_file_location('hair_volume',ROOT/'tools/kai/refine_hair_volume.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);B=V.B
def detailed_material(old):
 m=old.copy();m.name='Kai / Pearl hair directional fibers';nt=m.node_tree;n=nt.nodes;l=nt.links;p=n.get('Principled BSDF')
 original=p.inputs['Base Color'].links[0].from_socket
 uv=n.new('ShaderNodeTexCoord');uv.label='Along each hair lock'
 separate=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],separate.inputs[0])
 def mathnode(op,a=None,b=None):
  q=n.new('ShaderNodeMath');q.operation=op
  if a is not None:
   if isinstance(a,(int,float)):q.inputs[0].default_value=a
   else:l.new(a,q.inputs[0])
  if b is not None:
   if isinstance(b,(int,float)):q.inputs[1].default_value=b
   else:l.new(b,q.inputs[1])
  return q.outputs[0]
 wobble=mathnode('SINE',mathnode('MULTIPLY',separate.outputs['Y'],8.0));wobble=mathnode('MULTIPLY',wobble,.50)
 scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(13,1.6,0);l.new(uv.outputs['UV'],scale.inputs[0])
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3;noise.inputs['Detail'].default_value=2;l.new(scale.outputs['Vector'],noise.inputs['Vector'])
 phase=mathnode('ADD',mathnode('MULTIPLY',separate.outputs['X'],2*pi*22),wobble)
 phase=mathnode('ADD',phase,mathnode('MULTIPLY',noise.outputs['Fac'],3.0))
 wave=mathnode('ADD',mathnode('MULTIPLY',mathnode('SINE',phase),.5),.5)
 ramp=n.new('ShaderNodeValToRGB');ramp.label='Soft pearl and lavender fiber strokes'
 ramp.color_ramp.elements[0].color=B.rgb('C2AFC0');ramp.color_ramp.elements[1].position=.15;ramp.color_ramp.elements[1].color=B.rgb('FFF7E7');l.new(wave,ramp.inputs[0])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.22;l.new(original,mix.inputs[1]);l.new(ramp.outputs['Color'],mix.inputs[2]);l.new(mix.outputs['Color'],p.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.label='Fine lengthwise hair relief';bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.00020;l.new(wave,bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=0;rough.inputs['From Max'].default_value=1;rough.inputs['To Min'].default_value=.26;rough.inputs['To Max'].default_value=.39;l.new(wave,rough.inputs['Value']);l.new(rough.outputs['Result'],p.inputs['Roughness'])
 for inp in p.inputs:
  if inp.name=='Anisotropic IOR Level':inp.default_value=.5
  elif inp.name=='Anisotropic Rotation':inp.default_value=.25
 tangent=n.new('ShaderNodeTangent');tangent.direction_type='UV_MAP'
 if p.inputs.get('Tangent'):l.new(tangent.outputs['Tangent'],p.inputs['Tangent'])
 return m
def stable_rear_lock(name,points,width,a):
 # Preserve the sideways direction through the upward curl; a radial-frame reset
 # would flip by 180 degrees at the bend and produce blunt, pinched ends.
 pts=B.bez(points,40);N=20;v=[];f=[]
 for i,p in enumerate(pts):
  t=i/(len(pts)-1);tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
  side=Vector((sin(a),-cos(a),0));side=(side-tangent*side.dot(tangent)).normalized();deep=side.cross(tangent).normalized()
  w=width*(.30+.70*min(1,t/.18))*max(.0005,1-t)**.7
  for j in range(N):
   angle=2*pi*j/N;h=sin(angle);h*=.77 if h>=0 else .50
   v.append(p+side*(w*cos(angle))+deep*(w*h))
 for i in range(len(pts)-1):
  for j in range(N):k=i*N+j;next=i*N+(j+1)%N;f.append((k,next,next+N,k+N))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(pts)-1)*N+j for j in range(N))])
 o=B.mesh(name,v,f,V.HAIR,2,'Head');o.modifiers[0].levels=1;uv=o.data.uv_layers.new(name='Lock UV')
 for polygon in o.data.polygons:
  for li in polygon.loop_indices:
   k=o.data.loops[li].vertex_index;uv.data[li].uv=((k%N)/N,(k//N)/(len(pts)-1))
 return o
def main():
 backup=WORK/'kai_before_finer_strands_and_paint.blend'
 if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));B.COL=bpy.data.collections['KAI | Editable character'];B.rig=bpy.data.objects['KAI_Rig']
 old=bpy.data.materials['Kai / Pearl hair with lavender shadows']
 hair=[o for o in bpy.data.objects if o.type=='MESH' and any(m==old for m in o.data.materials)]
 before={o.name:V.fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o not in hair}
 V.HAIR=detailed_material(old)
 for o in hair:
  for i,m in enumerate(o.data.materials):
   if m==old:o.data.materials[i]=V.HAIR
  if not o.data.uv_layers:
   uv=o.data.uv_layers.new(name='Hair flow UV')
   for loop in o.data.loops:
    co=o.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(math.atan2(co.y-.025,co.x)/(2*pi)+.5,(co.z-.6)/.5)
 # Shape the exposed lower backing into a continuous secondary layer of tapered
 # tufts. This closes the blank band without placing another row of thick ribbons.
 shell=bpy.data.objects['KAI_Clean flowing rear hair'];NA=181;NT=87
 assert len(shell.data.vertices)==NA*NT
 for vertex in shell.data.vertices:
  s=(vertex.index//NA)/(NT-1)
  if s<=.60:continue
  a=-.58+(pi+1.16)*(vertex.index%NA)/(NA-1)
  phase=(a+.58)/(pi+1.16)*13+.12*sin(a*3);frac=phase%1;tooth=1-abs(2*frac-1)
  fade=max(0,min(1,(s-.72)/.28))**2
  edge=min(1,(a+.58)/.15,(pi+.58-a)/.15);edge=max(0,edge)
  vertex.co.z-=(.010+.030*tooth)*fade*edge
  ridge=.010*max(0,sin(pi*frac))**.6*min(1,(s-.60)/.30)*edge
  vertex.co+=Vector((cos(a),sin(a),0))*ridge
 # Foreground ribbon strands follow the large locks instead of crossing them.
 shapes=[
  ('Fine fringe left',[(-.019,-.130,.999),(-.110,-.226,.966),(-.102,-.247,.838),(-.028,-.207,.875)],.016,(0,-1,0)),
  ('Fine fringe right',[(.054,-.134,.997),(.105,-.230,.964),(.120,-.242,.847),(.185,-.198,.891)],.016,(0,-1,0)),
  ('Part wisp',[(.017,-.114,1.012),(.000,-.183,.981),(-.005,-.202,.944),(-.045,-.193,.957)],.013,(0,-1,0)),
  ('Outer brow curl R',[(.130,-.180,.911),(.140,-.215,.840),(.100,-.190,.790),(.150,-.170,.820)],.009,(.25,-1,0)),
 ]
 added=[]
 for name,p,w,n in shapes:
  if name.startswith('Outer brow'):
   pts=B.bez(p,32);o=B.tube(name,pts,.0036,V.HAIR,'Head',depth=1,taper=True,normal=n,sub=2);o.modifiers[0].levels=1
   uv=o.data.uv_layers.new(name='Lock UV')
   for polygon in o.data.polygons:
    for li in polygon.loop_indices:
     k=o.data.loops[li].vertex_index;uv.data[li].uv=((k%10)/10,(k//10)/(len(pts)-1))
  else:o,_=V.lock(name,p,w,n,.76)
  added.append(o.name)
 for sg,side in [(1,'L'),(-1,'R')]:
  shapes=[
   ('Cheek side curl '+side,[(sg*.153,-.037,.747),(sg*.172,-.113,.713),(sg*.128,-.125,.650),(sg*.080,-.116,.682)],.020,(sg*.2,-1,0)),
   ('Cheek tip curl '+side,[(sg*.146,-.025,.721),(sg*.163,-.093,.688),(sg*.133,-.105,.663),(sg*.105,-.106,.682)],.012,(sg*.2,-1,0)),
  ]
  for name,p,w,n in shapes:
   o,_=V.lock(name,p,w,n,.80);added.append(o.name)
 # A shorter secondary row follows the lanes of the rear locks, with varied curled tips.
 def point(theta,a,offset):return Vector(((.198*sin(theta)+offset)*cos(a),.025+(.217*sin(theta)+offset)*sin(a),.842+.215*cos(theta)))
 for j in (0,3,5,8):
  center=-.58+(pi+1.16)*(j+.5)/9
  a=center;shift=.080*cos(a);delta=.011*sin(j*2.1)
  p=[point(1.52,a,-.004),point(1.93,a+shift*.3,.040),point(2.57,a-shift*.5,.060),point(2.40,a+shift,.080)]
  p[2].z+=delta;p[3].z=.696+delta
  o=stable_rear_lock('Fine lower rear %02d'%j,p,.010+.0015*sin(j*1.7),a);added.append(o.name)
 bpy.context.view_layer.update();assert before=={n:V.fingerprint(bpy.data.objects[n]) for n in before}
 scene=bpy.context.scene;scene['kai_hair_revision']='Fine split strands in marked fringe/jaw/lower-rear areas; directional pearl/lavender fiber color, relief and highlights'
 report={'added_strands':added,'integrated_lower_rear_tufts':13,'existing_hair_meshes_with_fiber_material':len(hair),'non_hair_meshes_preserved':len(before),'backup':str(backup),'material_detail':'UV aligned irregular fine color strokes, subtle bump and anisotropic highlights'}
 (OUT/'hair_detail_validation.json').write_text(json.dumps(report,indent=2))
 cam=scene.camera;cam.location=(0,-3,.57);cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews/front.png');bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 for name,pos in [('front',(0,-3,.57)),('three_quarter',(1.8,-3,1.0)),('side',(3,0,.57)),('back',(0,3,.57))]:
  (WORK/'hair_detail_progress.txt').write_text('Rendering '+name);cam.location=pos;cam.rotation_euler=(Vector((0,0,.55))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True)
 (WORK/'hair_detail_progress.txt').write_text('Complete fine strands and directional painting')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'hair_detail_error.txt').write_text(traceback.format_exc());raise
