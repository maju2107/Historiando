extends SceneTree

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	var course: Node3D = island.get_node("ParkourFlutuante")
	course.cycle_enabled = false
	course.set_physics_process(false)
	await physics_frame
	await physics_frame
	var space := island.get_world_3d().direct_space_state
	var capsule := CapsuleShape3D.new()
	capsule.radius = .32
	capsule.height = 1.30
	for pickup: Area3D in island.get_node("Topazios").get_children():
		var original := pickup.global_position
		var supported := false
		for ring in 6:
			var samples := 1 if ring == 0 else 16
			for index in samples:
				var candidate := original + Vector3(cos(TAU * index / samples),0,sin(TAU * index / samples)) * ring * .45
				if candidate.distance_to(player.global_position + Vector3.UP * .65) < 1.3:
					continue
				var ray := PhysicsRayQueryParameters3D.create(candidate + Vector3.UP * .4,candidate - Vector3.UP * 1.3,1)
				ray.exclude = [player.get_rid()]
				var hit := space.intersect_ray(ray)
				if hit.is_empty():
					continue
				if not (hit.collider is TerrainChunk or hit.collider.is_in_group("floating_parkour_platform")):
					continue
				if absf(hit.position.y - (original.y - .85)) > .22:
					continue
				candidate.y = hit.position.y + .85
				var query := PhysicsShapeQueryParameters3D.new()
				query.shape = capsule
				query.transform = Transform3D(Basis.IDENTITY,candidate - Vector3.UP * .10)
				query.collision_mask = 1
				query.exclude = [player.get_rid()]
				if not space.intersect_shape(query).is_empty():
					continue
				print("CLEAR_PLACEMENT ",pickup.name," ",candidate," moved=",candidate.distance_to(original))
				supported = true
				break
			if supported:
				break
		if not supported:
			print("NO_CLEAR_PLACEMENT ",pickup.name)
	island.queue_free()
	await process_frame
	quit()
