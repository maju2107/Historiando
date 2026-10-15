extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	island.get_node("Player").set_physics_process(false)
	var sk: Skeleton3D = island.get_node("Player/gobot").find_child("Skeleton3D",true,false)
	for i in sk.get_bone_count():
		print("BONE ",i," ",sk.get_bone_name(i)," parent=",sk.get_bone_parent(i)," rest=",sk.get_bone_rest(i))
	for mesh: MeshInstance3D in island.get_node("Player/gobot").find_children("*","MeshInstance3D",true,false):
		print("FACE_SHAPES ",mesh.name," ",mesh.mesh.get_blend_shape_count())
		for i in mesh.mesh.get_blend_shape_count(): print(mesh.mesh.get_blend_shape_name(i))
	await physics_frame
	await physics_frame
	var space := island.get_world_3d().direct_space_state
	for z in range(26,-15,-3):
		var row := "SURFACE z="+str(z)
		for x in range(-18,19,3):
			var ray := PhysicsRayQueryParameters3D.create(Vector3(x,35,z),Vector3(x,-2,z),1)
			for attempt in 20:
				var hit := space.intersect_ray(ray)
				if hit.is_empty(): break
				if hit.collider is TerrainChunk:
					row += " %s:%.2f" % [x,hit.position.y]
					break
				var ex := ray.exclude; ex.append(hit.rid); ray.exclude=ex
		print(row)
	for group in island.get_node("Vegetation").get_children():
		for tree in group.get_children():
			if tree is Node3D and str(tree.name).begins_with("Arvore") and tree.global_position.z>16:
				print("SOUTH_TREE ",tree.get_path()," ",tree.global_position)
	print("ANIMS ",island.get_node("Player/gobot/AnimationPlayer").get_animation_list())
	island.queue_free()
	await process_frame
	quit()
