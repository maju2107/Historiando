extends SceneTree

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	island.get_node("Player").set_physics_process(false)
	island.get_node("ParkourFlutuante").set_physics_process(false)
	await physics_frame
	await physics_frame
	var space := island.get_world_3d().direct_space_state
	for point: Vector2 in [Vector2(2.8,-8.8),Vector2(10.5,-5),Vector2(-6,-6),Vector2(-13,4.5),Vector2(-10.5,-4),Vector2(15,9),Vector2(22,12.5),Vector2(-23,-3),Vector2(-22,-12),Vector2(9,24)]:
		var ray := PhysicsRayQueryParameters3D.create(Vector3(point.x,40,point.y),Vector3(point.x,-3,point.y),1)
		for attempt in 24:
			var hit := space.intersect_ray(ray)
			if hit.is_empty():
				print("NO_GROUND ", point)
				break
			if hit.collider is TerrainChunk:
				print("TOPAZIO_SURFACE ", point, " y=", hit.position.y, " collider=", hit.collider.name)
				break
			var excluded := ray.exclude
			excluded.append(hit.rid)
			ray.exclude=excluded
	island.free()
	quit()
