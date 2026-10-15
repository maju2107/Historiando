extends SceneTree

# Run in the isolated tmp/topazio_validation project after its import pass.
func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var budget := int(args[0]) if not args.is_empty() else 1500
	var scene := load("res://prop/topazio_imperial_prop.tscn") as PackedScene
	if scene == null:
		push_error("Could not load the exported crystal scene")
		quit(1)
		return
	var instance := scene.instantiate()
	root.add_child(instance)
	if not instance is StaticBody3D:
		push_error("Root must provide static collision")
		quit(1)
		return
	var collision := instance.get_node("CollisionShape3D") as CollisionShape3D
	if not collision.shape is ConvexPolygonShape3D:
		push_error("Missing convex collision")
		quit(1)
		return
	var meshes := instance.find_children("*", "MeshInstance3D", true, false)
	if meshes.size() != 1:
		push_error("Expected one visible mesh")
		quit(1)
		return
	var mesh := (meshes[0] as MeshInstance3D).mesh
	var triangles := 0
	for surface in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		triangles += indices.size() / 3 if not indices.is_empty() else vertices.size() / 3
		for vertex in vertices:
			if not vertex.is_finite():
				push_error("Nonfinite vertex")
				quit(1)
				return
		var material := mesh.surface_get_material(surface) as StandardMaterial3D
		if material == null or material.albedo_texture == null:
			push_error("Missing embedded albedo texture")
			quit(1)
			return
		if budget > 1500 and (material.normal_texture == null or material.roughness_texture == null):
			push_error("Semi-realistic material must include normal and roughness textures")
			quit(1)
			return
	if triangles > budget:
		push_error("Triangle budget exceeded")
		quit(1)
		return
	print("TOPAZIO_GODOT_OK meshes=", meshes.size(), " triangles=", triangles,
		" bounds=", mesh.get_aabb(), " convex_points=", collision.shape.points.size())
	quit(0)
