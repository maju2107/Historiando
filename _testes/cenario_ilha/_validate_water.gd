extends SceneTree
## Run with: godot --headless --path . --script _testes/cenario_ilha/_validate_water.gd
const Profile = preload("res://_testes/cenario_ilha/water/watercourse_profile.gd")
var _failures := 0


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	var player := island.get_node("Player") as CharacterBody3D
	player.set_physics_process(false)
	var water := island.get_node("Water")
	await physics_frame
	await physics_frame
	var space := island.get_world_3d().direct_space_state
	var samples := 0
	for reach: Vector4 in Profile.REACHES:
		var z := reach.x + 0.25
		while z < reach.y - 0.25:
			var from := Vector3(Profile.center_x(z), reach.z + 2.0, z)
			var to := from - Vector3(0, 4, 0)
			var query := PhysicsRayQueryParameters3D.create(from, to)
			query.exclude = [player.get_rid()]
			var hit := space.intersect_ray(query)
			_check(not hit.is_empty(), "Missing riverbed at z=%.2f" % z)
			if not hit.is_empty():
				var depth: float = reach.z - hit.position.y
				_check(depth > 0.20 and depth < 0.42, "Riverbed depth %.3f at z=%.2f" % [depth, z])
			samples += 1
			z += 0.45
	print("RIVERBED samples=", samples)
	await _check_terrain_preservation(island, player)
	_check_waterfalls_clear_terrain(island, player)

	# Cross both banks with the actual Player capsule and move_and_slide.
	var crossing_z := 10.0
	var center := Profile.center_x(crossing_z)
	player.position = Vector3(center - 3.2, 4.1, crossing_z)
	player.velocity = Vector3.ZERO
	var minimum_height := 100.0
	var touched_water := false
	for frame in 210:
		await physics_frame
		player.velocity.x = 2.0
		player.velocity.z = 0.0
		player.velocity.y -= 9.8 / 60.0
		player.move_and_slide()
		minimum_height = minf(minimum_height, player.position.y)
		touched_water = touched_water or not water._contacts.is_empty()
	_check(touched_water, "Crossing did not trigger water interaction")
	_check(minimum_height > 3.45 and minimum_height < 3.70, "Player did not walk on the shallow bed: %.3f" % minimum_height)
	_check(player.position.x > center + 2.7, "Player got stuck on the bank")
	_check(player.position.y > 3.90, "Player did not climb back onto dry ground")
	_check(water._contacts.is_empty(), "Dry player still emits ripples")
	print("CROSSING final=", player.position, " min_y=", minimum_height)

	# Enter, move, jump, re-enter, and leave each elevation independently.
	water.set_physics_process(false)
	for i in Profile.REACHES.size():
		var reach: Vector4 = Profile.REACHES[i]
		var z := (reach.x + reach.y) * 0.5
		player.position = Vector3(Profile.center_x(z), reach.z - Profile.DEPTH, z)
		water._physics_process(0.016)
		_check(water._contacts.has(player.get_instance_id()), "Entry missing at reach %d" % i)
		var before: int = water._ripple_index
		player.position.z += 0.5
		water._physics_process(0.016)
		_check(water._ripple_index != before, "No wake at reach %d" % i)
		before = water._ripple_index
		player.position.y = reach.z + 1.0
		water._physics_process(0.016)
		_check(water._contacts.is_empty() and water._ripple_index == before, "Airborne player generates ripples")
		player.position.y = reach.z - Profile.DEPTH
		water._physics_process(0.016)
		_check(water._ripple_index != before, "Landing splash/ripple missing")
		before = water._ripple_index
		player.position.x += 10.0
		water._physics_process(0.016)
		_check(water._contacts.is_empty() and water._ripple_index == before, "Dry bank generates ripples")

	# Ripples must expire and remain bounded even after a long walk.
	water._physics_process(3.0)
	for ripple: Vector4 in water._ripples:
		_check(water._clock - ripple.z > water.RIPPLE_LIFETIME, "Ripple did not expire")
	for i in 100:
		water._emit_ripple(Vector3(3, 3.86, 10))
	_check(water._ripples.size() == 24, "Ripple storage grows without a bound")

	# Deleting an interactor and moving the whole island must also be safe.
	island.position = Vector3(40, 2, 30)
	player.position = Vector3(Profile.center_x(10), 3.54, 10)
	water._physics_process(0.016)
	_check(water._contacts.has(player.get_instance_id()), "Moved island lost water coordinates")
	player.free()
	water._physics_process(0.016)
	_check(water._contacts.is_empty(), "Deleted player left stale contact")
	island.free()
	print("WATER_VALIDATION ", "PASS" if _failures == 0 else "FAIL", " failures=", _failures)
	quit(0 if _failures == 0 else 1)


func _check_terrain_preservation(island: Node3D, player: CharacterBody3D) -> void:
	# Compare actual collision with an uncarved copy, including the high ledges
	# that the former unrestricted deformation collapsed into the riverbed.
	var reference: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	for child: Node in reference.get_children():
		if child.name != &"Terrain":
			child.free()
	for chunk: Node in reference.get_node("Terrain").find_children("*", "StaticBody3D", true, false):
		chunk.carve_watercourse = false
	reference.position = Vector3(200, 0, 0)
	root.add_child(reference)
	await physics_frame
	await physics_frame
	var space := island.get_world_3d().direct_space_state
	var max_depression := 0.0
	var checks := 0
	for z in range(-8, 28):
		for x in range(-1, 8):
			var from := Vector3(x, 20, z)
			var query := PhysicsRayQueryParameters3D.create(from, from - Vector3(0, 24, 0))
			query.exclude = [player.get_rid()]
			var hit := space.intersect_ray(query)
			query.from += reference.position
			query.to += reference.position
			var original := space.intersect_ray(query)
			if original.is_empty():
				continue
			_check(not hit.is_empty(), "Carving removed ground at %s" % from)
			if hit.is_empty():
				continue
			var depression: float = original.position.y - hit.position.y
			max_depression = maxf(max_depression, depression)
			_check(depression <= 0.481, "Carving crushed the terrain by %.3f at %s" % [depression, from])
			if original.collider.name in [&"Mirante", &"SacadaPicoSul"]:
				_check(absf(depression) < 0.002, "An elevated platform was deformed at %s" % from)
			checks += 1
	print("TERRAIN_PRESERVATION samples=", checks, " max_cut=", max_depression)
	reference.free()


func _check_waterfalls_clear_terrain(island: Node3D, player: CharacterBody3D) -> void:
	var space := island.get_world_3d().direct_space_state
	for label: String in ["CachoeiraSuperior", "CachoeiraInferior", "CachoeiraDaIlha"]:
		var fall := island.get_node("Water/" + label) as MeshInstance3D
		var vertices: PackedVector3Array = fall.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		var intersections := 0
		for row in range(1, 32, 2):
			for column in range(1, 16, 2):
				var point := fall.to_global(vertices[row * 17 + column])
				var query := PhysicsRayQueryParameters3D.create(Vector3(point.x, 20, point.z), Vector3(point.x, -3, point.z))
				query.exclude = [player.get_rid()]
				var hit := space.intersect_ray(query)
				if not hit.is_empty() and hit.position.y > point.y + 0.05:
					intersections += 1
		_check(intersections == 0, "%s intersects terrain at %d samples" % [label, intersections])
