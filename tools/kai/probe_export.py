import bpy,json
from pathlib import Path
R=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16')
bpy.ops.wm.open_mainfile(filepath=str(W/'kai_before_rig.blend'));rig=bpy.data.objects['KAI_Rig']
d={'rig':{'scale':list(rig.scale),'location':list(rig.location)},'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None,'quat':list(rig.pose.bones[b.name].rotation_quaternion),'constraints':[(c.type,c.name) for c in rig.pose.bones[b.name].constraints]} for b in rig.data.bones},'materials':{m.name:{'nodes':[{'name':n.name,'type':n.type,'uv':getattr(n,'uv_map',None),'image':getattr(getattr(n,'image',None),'name',None)} for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]} for m in bpy.data.materials if m.use_nodes}}
with bpy.data.libraries.load(str(R/'art/yara/yara.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if not n.startswith('RigCheck_')]
d['donor_actions']=[{'name':a.name,'range':list(a.frame_range),'slots':[(s.identifier,s.target_id_type) for s in a.slots]} for a in bpy.data.actions]
(W/'export_probe.json').write_text(json.dumps(d,indent=2))
