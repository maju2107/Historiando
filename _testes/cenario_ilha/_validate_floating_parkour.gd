extends SceneTree
## godot --headless --fixed-fps 60 --path . --script _testes/cenario_ilha/_validate_floating_parkour.gd

var _failures := 0
var _island: Node3D
var _player: CharacterBody3D
var _course: Node3D
var _platforms: Array[Node3D]
var _spawn: Vector3
var _advance_cycle := false


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _run() -> void:
	_island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(_island)
	_player = _island.get_node("Player") as CharacterBody3D
	_spawn = _player.global_position
	_player.set_physics_process(false)
	_course = _island.get_node("ParkourFlutuante")
	_course.set_physics_process(false)
	_platforms = _course.get_platforms()
	await physics_frame
	await physics_frame
	_check(_platforms.size() == 21, "Expected 21 platforms")
	_check(_platforms.back().permanent, "The final platform is not permanent")
	var previous_y := _spawn.y
	for platform in _platforms:
		_check(platform.surface_position().y > previous_y, "The course must keep ascending")
		previous_y = platform.surface_position().y

	await _test_cycle_and_collision()
	await _test_disappearing_support()
	for preset in [0, 1]:
		_player.control_preset = preset
		await _traverse(false)
		if _failures == 0:
			await _traverse(true)
	_release_input()
	_island.free()
	print("FLOATING_PARKOUR ", "PASS" if _failures == 0 else "FAIL", " failures=", _failures)
	quit(0 if _failures == 0 else 1)


func _test_cycle_and_collision() -> void:
	var space := _island.get_world_3d().direct_space_state
	var active: float = _course.active_seconds
	var period: float = active + _course.ghost_seconds
	for i in _platforms.size():
		var platform := _platforms[i]
		for sample: Vector2 in [Vector2(0.01, 1), Vector2(active - 0.01, 1), Vector2(active + 0.01, 0), Vector2(period - 0.01, 0), Vector2(period + 0.01, 1)]:
			_course.apply_cycle_time(i * _course.stagger_seconds + sample.x)
			await physics_frame
			await physics_frame
			var expected: bool = sample.y > 0.5 or platform.permanent
			_check(platform.is_solid == expected, "Wrong cycle state on %s" % platform.name)
			_check(platform.get_node("CollisionShape3D").disabled != expected, "Wrong collision state on %s" % platform.name)
			var surface: Vector3 = platform.surface_position()
			var query := PhysicsRayQueryParameters3D.create(surface + Vector3.UP, surface - Vector3(0, 0.3, 0))
			query.exclude = [_player.get_rid()]
			var hit := space.intersect_ray(query)
			_check((not hit.is_empty() and hit.collider == platform) == expected, "Ghost/solid raycast mismatch on %s" % platform.name)
			var material: ShaderMaterial = platform.get_node("Visual").material_override
			_check(is_equal_approx(float(material.get_shader_parameter("solid_amount")), 1.0 if expected else 0.0), "Visual and collision disagree")
	# A large time jump must still preserve the period and the final platform.
	_course.apply_cycle_time(period * 1000.0 + 0.1)
	_check(_platforms[0].is_solid and _platforms.back().is_solid, "Cycle drifts over time")
	print("CYCLE_COLLISION_OK platforms=", _platforms.size())


func _test_disappearing_support() -> void:
	_course.cycle_enabled = false
	var first := _platforms[0]
	_player.global_position = first.surface_position() + Vector3(0, 0.03, 0)
	_player.velocity = Vector3.ZERO
	for frame in 12:
		await _step(Vector3.ZERO)
	_check(_player.is_on_floor(), "Player did not stand on the active platform")
	_course.cycle_enabled = true
	_course.apply_cycle_time(_course.active_seconds + 0.1)
	for frame in 24:
		await _step(Vector3.ZERO)
	_check(_player.global_position.y < first.surface_position().y - 0.3, "Ghost platform still supports the player")
	_course.apply_cycle_time(0.1)
	await physics_frame
	await physics_frame
	_check(first.is_solid and not first.get_node("CollisionShape3D").disabled, "Platform did not restore collision")
	print("DISAPPEARING_SUPPORT_OK")


func _traverse(timed: bool) -> void:
	_advance_cycle = false
	_course.cycle_enabled = false
	_course._elapsed = 0.0
	_player.global_position = _spawn
	_player.velocity = Vector3.ZERO
	for frame in 12:
		await _step(Vector3.ZERO)
	_check(_player.is_on_floor(), "Spawn has no floor")
	if timed:
		_course.cycle_enabled = true
		_course.apply_cycle_time(0.0)
		_advance_cycle = true
	var completed := 0
	for platform in _platforms:
		var target: Vector3 = platform.surface_position()
		var direction := target - _player.global_position
		direction.y = 0
		direction = direction.normalized()
		await _step(direction, true)
		var landed := false
		for frame in 100:
			await _step(direction)
			if _player.is_on_floor():
				for collision_index in _player.get_slide_collision_count():
					if _player.get_slide_collision(collision_index).get_collider() == platform:
						landed = true
				break
		_check(landed, "Missed %s (%s), position=%s, target=%s, clock=%.3f" % [platform.name, "timed" if timed else "all solid", _player.global_position, target, _course._elapsed])
		if not landed:
			break
		completed += 1
		# Walk back toward the center before the next launch, using the actual
		# controller (it intentionally keeps horizontal momentum while airborne).
		for frame in 45:
			var adjustment := target - _player.global_position
			adjustment.y = 0
			if adjustment.length() < 0.13:
				break
			await _step(adjustment.normalized())
		_check(_player.is_on_floor(), "Platform vanished during the landing/centering window")
		if not _player.is_on_floor():
			break
	_advance_cycle = false
	print("TRAVERSE ", "TIMED" if timed else "SOLID", " preset=", _player.control_preset, " completed=", completed, "/", _platforms.size())
	if timed and completed == _platforms.size():
		# Even at times when every ordinary platform has ghost windows, the
		# finish remains a floor the actual character can stand on.
		for cycle in 3:
			_course.apply_cycle_time(_course.active_seconds + cycle * (_course.active_seconds + _course.ghost_seconds))
			for frame in 12:
				await _step(Vector3.ZERO)
			_check(_player.is_on_floor(), "Permanent finish lost support")


func _step(direction: Vector3, jump: bool = false) -> void:
	await physics_frame
	if _advance_cycle:
		_course._physics_process(1.0 / 60.0)
	_set_action("ui_right", maxf(direction.x, 0.0))
	_set_action("ui_left", maxf(-direction.x, 0.0))
	_set_action("ui_down", maxf(direction.z, 0.0))
	_set_action("ui_up", maxf(-direction.z, 0.0))
	if jump:
		Input.action_press("ui_accept")
	# Express the test's direction in world space without changing movement,
	# jump strength, collision shape or the player's lack of air control.
	_player._movement_basis = Basis.IDENTITY
	_player._stick_was_active = true
	if not _player.follow_behind:
		_player.camera_pivo.global_rotation = Vector3(deg_to_rad(-18), 0, 0)
	_player._physics_process(1.0 / 60.0)
	Input.action_release("ui_accept")


func _set_action(action: StringName, strength: float) -> void:
	if strength > 0.001:
		Input.action_press(action, strength)
	else:
		Input.action_release(action)


func _release_input() -> void:
	for action: StringName in [&"ui_left", &"ui_right", &"ui_up", &"ui_down", &"ui_accept"]:
		Input.action_release(action)
