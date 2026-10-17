"""Replace floating lash cords with broad surface-fitted cartoon lash bands."""
import bpy,bmesh,json,math,traceback,importlib.util
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import pi
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_lashes_2026-10-16')
spec=importlib.util.spec_from_file_location('volume',ROOT/'tools/kai/refine_hair_volume.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V);B=V.B
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def resample(ps,n):
 d=[0.]
 for a,b in zip(ps,ps[1:]):d.append(d[-1]+(b-a).length)
 out=[];k=1
 for i in range(n):
  x=d[-1]*i/(n-1)
  while k<len(ps)-1 and d[k]<x:k+=1
  t=(x-d[k-1])/max(1e-8,d[k]-d[k-1]);out.append(ps[k-1].lerp(ps[k],t))
 return out
def centers(o,N):
 return [sum((o.matrix_world@v.co for v in list(o.data.vertices)[i*N:(i+1)*N]),Vector())/N for i in range(len(o.data.vertices)//N)]
def main():
 bpy.ops.wm.open_mainfile(filepath=str(WORK/'kai_before_lash_fit.blend'));body=bpy.data.objects['KAI_Base_Body'];B.rig=bpy.data.objects['KAI_Rig'];B.COL=bpy.data.objects['KAI_Relaxed upper eye contour L'].users_collection[0]
 names={p+s for p in ['KAI_Relaxed upper eye contour ','KAI_Base_LowerLashline.'] for s in ['L','R']}
 protected={o.name:V.fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in names}
 bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
 guides={'upper':centers(bpy.data.objects['KAI_Relaxed upper eye contour L'],10),'lower':centers(bpy.data.objects['KAI_Base_LowerLashline.L'],4)}
 guides['upper'].sort(key=lambda p:p.x)
 # The final point lies on the temple skin, joining the outer lash corner.
 end=guides['upper'][-1];guides['upper'] += [Vector((end.x+.004,end.y+.001,end.z+.002)),Vector((end.x+.009,end.y+.003,end.z+.004))]
 material=bpy.data.materials['Kai / Warm dark contours'].copy();material.name='Kai / Matte cartoon eyelashes'
 nt=material.node_tree;nt.nodes.clear();ink=nt.nodes.new('ShaderNodeEmission');ink.inputs['Color'].default_value=B.rgb('17100F');ink.inputs['Strength'].default_value=1
 output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(ink.outputs[0],output.inputs['Surface']);material.diffuse_color=B.rgb('17100F')
 def fit(point):
  near,normal,idx,d=bvh.find_nearest(point)
  hit=bvh.ray_cast(Vector((point.x,-.4,point.z)),Vector((0,1,0)))[0]
  # Front projection is used only when it reaches this eyelid, not the back
  # of the head through an eye opening. Otherwise follow the nearest rim.
  if hit is not None and hit.y<-.06 and (hit-point).length<.009:
   near=hit
  return near
 records=[]
 for side,sg in [('L',1),('R',-1)]:
  for kind in ['upper','lower']:
   name=('KAI_Relaxed upper eye contour ' if kind=='upper' else 'KAI_Base_LowerLashline.')+side
   bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
   raw=[Vector((sg*p.x,p.y,p.z)) for p in guides[kind]];path=resample(raw,113);path=[fit(p) for p in path]
   vv=[];ff=[];rows=7
   for i,center in enumerate(path):
    t=i/(len(path)-1);tangent=path[min(i+1,len(path)-1)]-path[max(0,i-1)]
    direction=Vector((-tangent.z,0,tangent.x)).normalized()
    if kind=='upper' and direction.z<0:direction=-direction
    if kind=='lower':
     # Spread outwards from the socket onto cheek skin.
     desired=Vector((sg*.6,0,-.7))
     if direction.dot(desired)<0:direction=-direction
    taper=math.sin(pi*t)**.42
    width=(.0065 if kind=='upper' else .0032)*taper+.00015
    if kind=='upper':width+=.0025*math.exp(-((t-.86)/.075)**2)
    for j in range(rows):
     u=j/(rows-1);point=center+direction*(width*(u-.08));vv.append(fit(point))
   for i in range(len(path)-1):
    for j in range(rows-1):a=i*rows+j;ff.append((a,a+1,a+1+rows,a+rows))
   o=B.mesh(name.removeprefix('KAI_'),vv,ff,material,1,'Head')
   # Final shrinkwrap is after smoothing and skinning, preventing the smoothed
   # edge from lifting away in either viewport or render.
   sh=o.modifiers.new('Attached to eyelid surface','SHRINKWRAP');sh.target=body;sh.wrap_method='NEAREST_SURFACEPOINT';sh.wrap_mode='ON_SURFACE';sh.offset=.00012
   solid=o.modifiers.new('Thin embedded lash thickness','SOLIDIFY');solid.thickness=.0006;solid.offset=0
   o['lash_fit']='Broad tapered surface ribbon; final shrinkwrap follows skinned eyelid. Back of ribbon embeds into skin.'
   records.append({'object':name,'width_m':.0065 if kind=='upper' else .0032,'shrinkwrap_offset_m':.00012,'thickness_m':.0006})
 bpy.context.view_layer.update();assert protected=={n:V.fingerprint(bpy.data.objects[n]) for n in protected},'An unrelated mesh changed'
 report={'source_checkpoint':str(WORK/'kai_before_lash_fit.blend'),'preserved_other_meshes':len(protected),'ribbons':records,'attachment_check':'pending visual and evaluated-surface checks'}
 (OUT/'lash_fit_validation.json').write_text(json.dumps(report,indent=2))
 scene=bpy.context.scene;scene.frame_set(1);scene['kai_lashes_revision']='Attached cartoon upper and lower outer-half lash ribbons'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'))
 (WORK/'progress.txt').write_text('Saved attached lash ribbons; inspect front and both sides')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'error.txt').write_text(traceback.format_exc());raise
