extends Node3D

## Keeps the existing player's AnimationPlayer path and clip names.
func _enter_tree() -> void:
	var animator := find_child("AnimationPlayer", true, false) as AnimationPlayer
	if animator == null:
		push_error("Yara model is missing its AnimationPlayer.")
		return
	if animator.get_parent() != self:
		var animation_root := animator.get_node(animator.root_node)
		animator.reparent(self)
		animator.root_node = animator.get_path_to(animation_root)


func _ready() -> void:
	var animator := get_node("AnimationPlayer") as AnimationPlayer
	for clip in ["Idle", "Walk", "Run"]:
		if animator.has_animation(clip):
			animator.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	_enable_baked_colors(self)
	var skeleton := find_child("Skeleton3D", true, false) as Skeleton3D
	if skeleton != null and skeleton.find_bone("Ponytail.1") >= 0:
		var hair := preload("res://assets/characters/yara/YaraHairPhysics.gd").new()
		hair.name = "PonytailPhysics"
		skeleton.add_child(hair)


func _enable_baked_colors(node: Node) -> void:
	if node is MeshInstance3D and node.mesh != null:
		for surface in node.mesh.get_surface_count():
			var material := node.get_active_material(surface) as StandardMaterial3D
			if material != null:
				# UV-painted materials supply their own color; older skins use baked colors.
				material.vertex_color_use_as_albedo = material.albedo_texture == null
				material.vertex_color_is_srgb = false
	for child in node.get_children():
		_enable_baked_colors(child)
