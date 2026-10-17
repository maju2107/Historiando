"""Soften the exposed knees and form each eye's lash outline as one ribbon."""
import bpy,json,math,traceback,importlib.util
import bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');OUT=ROOT/'art/kai';WORK=Path('C:/Users/obran/Historiando_Backups/kai_leg_lash_2026-10-16')
sp=importlib.util.spec_from_file_location('volume',ROOT/'tools/kai/refine_hair_volume.py');V=importlib.util.module_from_spec(sp);sp.loader.exec_module(V);B=V.B
sp=importlib.util.spec_from_file_location('lash',ROOT/'tools/kai/fit_cartoon_lashes.py');L=importlib.util.module_from_spec(sp);sp.loader.exec_module(L)
def main():
 bpy.ops.wm.open_mainfile(filepath=str(WORK/'kai_before_leg_lash.blend'));body=bpy.data.objects['KAI_Base_Body'];B.rig=bpy.data.objects['KAI_Rig'];B.COL=body.users_collection[0]
 old_names={p+s for p in ['KAI_Relaxed upper eye contour ','KAI_Base_LowerLashline.'] for s in ['L','R']}
 protected={o.name:V.fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in old_names|{body.name}}
 original=[v.co.copy() for v in body.data.vertices];changed=[]
 # Smooth only the knee's cross-section profiles. Keep its animation loops,
 # heights and weights; mirrored geometry applies the same correction to both legs.
 for base in [596,1193,608,1205,620]:
  for j in range(12):
   v=body.data.vertices[base+j];up=original[584+j];low=original[632+j]
   t=max(0,min(1,(up.z-v.co.z)/(up.z-low.z)));w=.93*math.sin(math.pi*t)**2;target=up.lerp(low,t)
   v.co.x+=(target.x-v.co.x)*w;v.co.y+=(target.y-v.co.y)*w;changed.append(v.index)
 body.data.update();assert all(v.co==original[v.index] for v in body.data.vertices if v.index not in changed)
 bpy.context.view_layer.update();bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
 # Existing surface-ribbon inner edges provide the accepted eye opening shape.
 upper=bpy.data.objects['KAI_Relaxed upper eye contour L'];lower=bpy.data.objects['KAI_Base_LowerLashline.L']
 up=[upper.data.vertices[i*7].co.copy() for i in range(113)];up=[p for p in up if p.x<=.1215]
 down=[lower.data.vertices[i*7].co.copy() for i in range(113)]
 a=up[-1];d=down[0];b=a+Vector((.0035,.0005,-.0005));c=d+Vector((.002,.0005,.002))
 bridge=B.bez([a,b,c,d],15)
 path=L.resample(up+bridge[1:-1]+down,181)
 # Average the guide before widening it: microscopic kinks otherwise become
 # visible scallops at the edge of a broad cartoon band.
 for _ in range(14):path=[path[0]]+[path[i-1]*.25+path[i]*.5+path[i+1]*.25 for i in range(1,len(path)-1)]+[path[-1]]
 path=L.resample(path,181)
 upper_length=sum((q-p).length for p,q in zip(up,up[1:]));bridge_length=sum((q-p).length for p,q in zip(bridge,bridge[1:]));total=sum((q-p).length for p,q in zip(path,path[1:]));join=(upper_length+.5*bridge_length)/total
 material=bpy.data.materials['Kai / Matte cartoon eyelashes']
 evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());skin=evaluated.to_mesh();skin.calc_loop_triangles();skin_triangles=[]
 for tri in skin.loop_triangles:
  ps=[skin.vertices[k].co.copy() for k in tri.vertices];center=sum(ps,Vector())/3
  if not(.025<center.x<.16 and .745<center.z<.835 and center.y<-.085):continue
  if (ps[1]-ps[0]).cross(ps[2]-ps[0]).normalized().y>-.03:continue
  hit=bvh.ray_cast(Vector((center.x,-.4,center.z)),Vector((0,1,0)))[0]
  if hit is None or abs(hit.y-center.y)>.0004:continue
  skin_triangles.append(ps)
 evaluated.to_mesh_clear()
 def clipped_patch(outline):
  # Clip actual front skin triangles against the smooth 2D lash strip.
  # The result follows the eyelid's surface exactly, without folded ribbon
  # rows or projection switches along the broad outer corner.
  vv=[];ff=[]
  for i in range(len(outline)-1):
   quad=[outline[i][0],outline[i+1][0],outline[i+1][1],outline[i][1]]
   area=sum(a.x*b.z-b.x*a.z for a,b in zip(quad,quad[1:]+quad[:1]))
   if area<0:quad.reverse()
   xlo=min(p.x for p in quad);xhi=max(p.x for p in quad);zlo=min(p.z for p in quad);zhi=max(p.z for p in quad)
   for tri in skin_triangles:
    if max(p.x for p in tri)<xlo or min(p.x for p in tri)>xhi or max(p.z for p in tri)<zlo or min(p.z for p in tri)>zhi:continue
    polygon=tri[:]
    for a,b in zip(quad,quad[1:]+quad[:1]):
     result=[]
     def distance(p):return (b.x-a.x)*(p.z-a.z)-(b.z-a.z)*(p.x-a.x)
     if not polygon:break
     prev=polygon[-1];dp=distance(prev)
     for point in polygon:
      dc=distance(point)
      if (dp>=-1e-12)!=(dc>=-1e-12):result.append(prev.lerp(point,dp/(dp-dc)))
      if dc>=-1e-12:result.append(point)
      prev=point;dp=dc
     polygon=result
    if len(polygon)>=3:
     start=len(vv);vv.extend(polygon);ff.append(tuple(range(start,start+len(polygon))))
  return vv,ff
 for name in old_names:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 records=[]
 for side,sg in [('L',1),('R',-1)]:
  pp=path;outline=[]
  for i,center in enumerate(pp):
   t=i/(len(pp)-1);tangent=pp[min(i+4,len(pp)-1)]-pp[max(0,i-4)];direction=Vector((-tangent.z,0,tangent.x)).normalized()
   blend=L.smooth((t-join+.045)/.09);width=.009*(1-blend)+.0050*blend
   width+=.0023*math.exp(-((t-(join-.045))/.035)**2)
   width*=min(1,(t/.08)**.55,((1-t)/.10)**.55);width=max(.00018,width)
   outline.append((center-direction*width*.06,center+direction*width*.94))
  vv,ff=clipped_patch(outline)
  vv=[Vector((sg*p.x,p.y,p.z)) for p in vv]
  o=B.mesh('Connected cartoon lashes '+side,vv,ff,material,0,'Head')
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
  sh=o.modifiers.new('Attached to eyelid surface','SHRINKWRAP');sh.target=body;sh.wrap_method='NEAREST_SURFACEPOINT';sh.wrap_mode='ON_SURFACE';sh.offset=.00012
  so=o.modifiers.new('Thin embedded lash thickness','SOLIDIFY');so.thickness=.0006;so.offset=0
  # A single connected skin-surface patch spans the upper lid, outer corner
  # and lower half; its outline is clipped directly against facial triangles.
  o['construction']='One continuous lash ribbon: upper lid to outer corner to lower outer half; no separate floating connector.'
  adjacency=[set() for _ in o.data.vertices]
  for e in o.data.edges:a,b=e.vertices;adjacency[a].add(b);adjacency[b].add(a)
  seen={0};todo=[0]
  while todo:
   for n in adjacency[todo.pop()]-seen:seen.add(n);todo.append(n)
  isolated=len(o.data.vertices)-len(seen)
  if isolated:
   bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in seen],context='VERTS');bm.to_mesh(o.data);bm.free()
  assert len(seen)==len(o.data.vertices),('Disconnected skin patch',side,len(seen),len(o.data.vertices))
  records.append({'object':o.name,'upper_width_m':.009,'lower_width_m':.005,'connected_vertices':len(seen),'discarded_isolated_clipping_fragments':isolated,'corner_path_fraction':join})
 bpy.context.view_layer.update();assert protected=={n:V.fingerprint(bpy.data.objects[n]) for n in protected}
 r={'source_checkpoint':str(WORK/'kai_before_leg_lash.blend'),'preserved_other_meshes':len(protected),'body_changed_vertices':changed,'body_other_vertices_unchanged':True,'body_topology_and_weights_unchanged':True,'knee_max_displacement_m':max((body.data.vertices[i].co-original[i]).length for i in changed),'ribbons':records,'attachment_check':'pending'}
 (OUT/'leg_lash_validation.json').write_text(json.dumps(r,indent=2));s=bpy.context.scene;s.frame_set(1);s['kai_leg_lash_revision']='Softened exposed knees; thicker continuous upper-to-lower cartoon lashes'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'kai.blend'));(WORK/'progress.txt').write_text('Saved local knee correction and continuous lash ribbons')
if __name__=='__main__':
 try:main()
 except Exception:
  (WORK/'error.txt').write_text(traceback.format_exc());raise
