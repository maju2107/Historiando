import bpy,json,shutil
from pathlib import Path
R=Path('C:/Users/obran/OneDrive/Documentos/GitHub/Historiando');W=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16');W.mkdir(exist_ok=True)
if not (W/'kai_before_rig.blend').exists():shutil.copy2(R/'art/kai/kai.blend',W/'kai_before_rig.blend')
bpy.ops.wm.open_mainfile(filepath=str(R/'art/kai/kai.blend'));rig=bpy.data.objects['KAI_Rig']
report={'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform,'pose':list(rig.pose.bones[b.name].rotation_euler)} for b in rig.data.bones], 'actions':[a.name for a in bpy.data.actions], 'materials':{m.name:[(n.name,n.type) for n in m.node_tree.nodes] for m in bpy.data.materials if m.use_nodes},'meshes':[{'name':o.name,'verts':len(o.data.vertices),'modifiers':[(m.type,m.name) for m in o.modifiers],'groups':[g.name for g in o.vertex_groups if any(vg.group==g.index for v in o.data.vertices for vg in v.groups)]} for o in bpy.data.objects if o.type=='MESH']}
(W/'probe.json').write_text(json.dumps(report,indent=2))
