extends Node3D
## Render the same paper/ink typography as the HUD onto a floating 3D plate.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var words := ""
var letter := "A"
var text_label: Label
var _material: StandardMaterial3D
var _mesh: MeshInstance3D
var opacity := 0.0:
	set(value):
		opacity = value
		if _material: _material.albedo_color.a = value
var lift := 0.0:
	set(value):
		lift = value
		if _mesh: _mesh.position.y = value

func _ready() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(640,224)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(viewport)
	var panel := preload("res://scenes/ui/comic_panel.gd").new()
	panel.size = Vector2(628,210)
	panel.fill = Kit.PAPER
	viewport.add_child(panel)
	Kit.rect(panel,Rect2(25,40,76,120),Kit.GOLD)
	var badge := Kit.label(panel,letter,Rect2(25,40,76,120),58,Kit.INK,Kit.BOLD)
	badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	badge.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	text_label = Kit.label(panel,words,Rect2(120,26,460,160),62,Kit.INK,Kit.BOLD)
	text_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var material := StandardMaterial3D.new()
	_material = material
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	material.albedo_texture = viewport.get_texture()
	material.albedo_color.a = opacity
	var mesh := MeshInstance3D.new()
	_mesh = mesh
	mesh.name = "FloatingAnswerPlate"
	var quad := QuadMesh.new()
	quad.size = Vector2(4.35,1.52)
	mesh.mesh = quad
	mesh.position.y = lift
	mesh.material_override = material
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mesh)
