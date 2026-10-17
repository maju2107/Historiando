"""Soften Kai's tank and rebuild the elbow wraps as broad cloth bands.

Uses a dated external checkpoint; do not rerun over later manual edits.
"""
import bpy,bmesh,math,json,shutil,traceback,importlib.util
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando')
OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_cloth_2026-10-16')
WORK.mkdir(exist_ok=True)
def load_module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
B=load_module('builder',ROOT/'tools/kai/build.py')
V=load_module('volume',ROOT/'tools/kai/refine_hair_volume.py')
def log(s):
 (WORK/'progress.txt').write_text(s);print(s,flush=True)
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def fabric(original,name,color=None):
 m=original.copy();m.name=name;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 p.inputs['Roughness'].default_value=.88
 if 'Sheen Weight' in p.inputs:p.inputs['Sheen Weight'].default_value=.16
 if color:
  for link in list(p.inputs['Base Color'].links):l.remove(link)
  p.inputs['Base Color'].default_value=B.rgb(color)
 tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=240
 noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.65
 l.new(tc.outputs['Generated'],noise.inputs['Vector']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.16;b.inputs['Distance'].default_value=.00012
 l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
 return m
def main():
 backup=WORK/'kai_before_cloth.blend'
 if not backup.exists():shutil.copy2(OUT/'kai.blend',backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));s=bpy.context.scene
 B.rig=bpy.data.objects['KAI_Rig'];B.COL=bpy.data.objects['KAI_Sleeveless tank'].users_collection[0]
 targets=lambda n:n=='KAI_Sleeveless tank' or n.startswith(('KAI_Elbow strap ','KAI_Violet elbow guard ','KAI_Pad spot '))
 preserved={o.name:V.fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and not targets(o.name)}
 for o in list(bpy.data.objects):
  if targets(o.name):bpy.data.objects.remove(o,do_unlink=True)
 cotton=fabric(bpy.data.materials['Kai / Violet cotton'],'Kai / Soft violet woven jersey')
 brown=fabric(bpy.data.materials['Kai / Brown elbow straps'],'Kai / Flat brown elbow fabric','60351F')
 padmat=fabric(cotton,'Kai / Violet padded fabric','542B7A')
 # Curved panels: sloping shoulders, scooped armholes, and a tucked hem.
 # A subdivision applied before cloth creates evenly connected simulation quads.
 rows=[(.415,.087,.061),(.424,.092,.064),(.440,.100,.068),(.462,.103,.068),(.487,.101,.066),(.512,.097,.063),(.540,.091,.057),(.567,.090,.049),(.590,.090,.044)]
 nx=25;v=[];f=[];nr=len(rows)
 for back in (False,True):
  for j,(z,rx,depth) in enumerate(rows):
   for i in range(nx):
    u=-1+2*i/(nx-1);x=u*rx
    y=(1 if back else -1)*depth*math.sqrt(max(.18,1-.77*u*u))
    zz=z
    if j==nr-1:
     zz=.592-.020*max(0,1-(abs(u)/.49)**2)-.012*smooth((abs(u)-.58)/.42)
    if j==nr-2:zz-=.006*max(0,1-(abs(u)/.50)**2)
    # Small flowing folds emerge from the tucked waist, not sharp hem notches.
    amp=.0027*math.exp(-((z-.449)/.032)**2)*sin(pi*min(1,max(0,(z-.415)/.030)))
    wave=sin(5*pi*u+16*(z-.44))+.35*sin(9*pi*u-12*(z-.44))
    y+=(1 if back else -1)*amp*wave
    zz+=.0012*sin(4*pi*u)*math.exp(-((z-.445)/.023)**2)
    v.append((x,y,zz))
  off=nr*nx if back else 0
  for j in range(nr-1):
   for i in range(nx-1):a=off+j*nx+i;f.append((a,a+1,a+1+nx,a+nx))
 off=nr*nx
 # Curved sides close below the armhole; shoulder pieces are continuous fabric.
 for j in range(5):
  for i in (0,nx-1):a=j*nx+i;f.append((a,a+nx,a+nx+off,a+off))
 for i in list(range(6))+list(range(18,24)):
  a=(nr-1)*nx+i;f.append((a,a+1,a+1+off,a+off))
 top=B.mesh('Sleeveless tank',v,f,cotton,1)
 bpy.context.view_layer.objects.active=top;top.select_set(True)
 bpy.ops.object.modifier_apply(modifier=top.modifiers[0].name)
 # Parametric UVs support painting; seam is on the back/side of the shirt.
 uv=top.data.uv_layers.new(name='Cotton panels UV')
 for p in top.data.polygons:
  for li in p.loop_indices:
   c=top.data.vertices[top.data.loops[li].vertex_index].co
   uv.data[li].uv=(.25+math.atan2(c.y,c.x)/(2*pi),(c.z-.410)/.19)
 for n in ['Spine','Chest','Cloth anchors']:top.vertex_groups.new(name=n)
 for p in top.data.vertices:
  z=p.co.z;w=smooth((z-.46)/.10)
  top.vertex_groups['Chest'].add([p.index],w,'REPLACE');top.vertex_groups['Spine'].add([p.index],1-w,'REPLACE')
  # Neck and shoulder seams remain supported; the torso cloth is free to settle.
  pin=max(smooth((z-.552)/.027),1-smooth((z-.423)/.016))
  if pin>.0001:top.vertex_groups['Cloth anchors'].add([p.index],pin,'REPLACE')
 arm=top.modifiers.new('Torso skinning before cloth','ARMATURE');arm.object=B.rig
 c=top.modifiers.new('Soft cotton cloth physics','CLOTH');cs=c.settings
 cs.quality=8;cs.mass=.22;cs.air_damping=3;cs.tension_stiffness=35;cs.compression_stiffness=25;cs.shear_stiffness=8
 cs.bending_stiffness=.25;cs.bending_damping=2;cs.tension_damping=8;cs.compression_damping=8;cs.shear_damping=6
 cs.vertex_group_mass='Cloth anchors';cs.pin_stiffness=1;cs.use_dynamic_mesh=True
 cc=c.collision_settings;cc.use_collision=True;cc.distance_min=.0015;cc.collision_quality=4;cc.friction=5;cc.use_self_collision=True;cc.self_distance_min=.0015;cc.self_friction=3
 c.point_cache.frame_start=1;c.point_cache.frame_end=72
 sub=top.modifiers.new('Smooth cloth surface','SUBSURF');sub.levels=2;sub.render_levels=2
 so=top.modifiers.new('Thin cotton edge','SOLIDIFY');so.thickness=.0012;so.offset=0
 top['cloth_notes']='Live Blender cloth. Anchored shoulders, neckline and tucked waist; deforming torso collider. Play sequentially from frame 1.'
 # Use the already skinned body as the collision surface, retaining its geometry.
 body=bpy.data.objects['KAI_Base_Body'];coll=body.modifiers.new('Cotton collision surface','COLLISION')
 body.collision.thickness_outer=.0015;body.collision.thickness_inner=.001;body.collision.cloth_friction=5
 spot=bpy.data.materials['Kai / Pad spots']
 for sg,side in [(1,'L'),(-1,'R')]:
  bone='UpperArm.'+side;N=64;R=9;vv=[];ff=[]
  for j in range(R):
   t=j/(R-1);x=sg*(.161+.045*t)
   for i in range(N):
    a=2*pi*i/N;r=.0305+.0015*sin(pi*t)+.00045*cos(3*a+pi*t)
    vv.append((x,r*cos(a),.56+r*sin(a)))
  for j in range(R-1):
   for i in range(N):a=j*N+i;b=j*N+(i+1)%N;ff.append((a,b,b+N,a+N))
  band=B.mesh('Elbow strap '+side,vv,ff,brown,1,bone)
  so=band.modifiers.new('Woven wrap thickness','SOLIDIFY');so.thickness=.0014;so.offset=0
  uv=band.data.uv_layers.new(name='Fabric band UV')
  for p in band.data.polygons:
   for li in p.loop_indices:
    idx=band.data.loops[li].vertex_index;uv.data[li].uv=((idx%N)/N,(idx//N)/(R-1))
  band['construction']='Broad flat woven elbow wrap, 45 mm wide, 1.4 mm thick; no knot or rope.'
  # Flattened superellipse cushion, with its protector face behind the elbow.
  vv=[];ff=[];PN=48;PR=13
  for j in range(PR):
   phi=pi*j/(PR-1);rr=sin(phi);yy=.0355+.0075*cos(phi)
   for i in range(PN):
    a=2*pi*i/PN;xx=.039*math.copysign(abs(cos(a))**.65,cos(a))*rr;zz=.037*math.copysign(abs(sin(a))**.65,sin(a))*rr
    vv.append((sg*(.187+xx),yy,.56+zz))
  for j in range(PR-1):
   for i in range(PN):a=j*PN+i;b=j*PN+(i+1)%PN;ff.append((a,b,b+PN,a+PN))
  pad=B.mesh('Violet elbow guard '+side,vv,ff,padmat,1,bone)
  for dx,dz in [(-.017,-.015),(.017,-.015),(0,.005),(.018,.018),(-.018,.018)]:
   y=.0355+.0075*math.sqrt(max(.1,1-(dx/.04)**2-(dz/.04)**2))+.00035
   B.ball('Pad spot '+side,(sg*(.187+dx),y,.56+dz),(.004,.00055,.004),spot,bone)
  pad['construction']='Broad thin soft pad, rear facing, with flat printed spots.'
 bpy.context.view_layer.update()
 assert preserved=={n:V.fingerprint(bpy.data.objects[n]) for n in preserved},'An unrelated mesh changed'
 s.frame_start=1;s.frame_end=72;s.frame_set(1)
 s['kai_cloth_revision']='Soft draped jersey, tucked hem, live cotton cloth and flat elbow wraps'
 s['kai_cloth_test']='No gameplay action added. Live cloth follows torso animation through the existing rig.'
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 (OUT/'cloth_validation.json').write_text(json.dumps({'preserved_other_meshes':len(preserved),'shirt_control_vertices':len(top.data.vertices),'cloth_modifier':c.name,'pinned_group':cs.vertex_group_mass,'cache_frames':[1,72],'band_width_m':.045,'band_thickness_m':.0014,'pad_dimensions_m':[.078,.015,.074],'backup':str(backup),'simulation_test':'pending'},indent=2))
 log('Saved cloth construction; ready for motion simulation and visual review')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'error.txt').write_text(traceback.format_exc());raise
