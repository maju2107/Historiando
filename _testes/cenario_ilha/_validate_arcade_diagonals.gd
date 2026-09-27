extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _axis(axis: JoyAxis, value: float) -> void:
	var event := InputEventJoypadMotion.new()
	event.device = 0
	event.axis = axis
	event.axis_value = value
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func _run() -> void:
	var player = load("res://_testes/parkour/Player.tscn").instantiate()
	player.control_preset = 1
	root.add_child(player)
	player.set_physics_process(false)
	player.camera_pivo.rotation.y = 0.7
	for direction in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1), Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
		var initial_yaw: float = player.camera_pivo.rotation.y
		for strength in [0.35, 1.0]:
			_axis(JOY_AXIS_LEFT_X, direction.x * strength)
			_axis(JOY_AXIS_LEFT_Y, direction.y * strength)
			if not player._get_movement_input().is_equal_approx(direction.normalized()):
				push_error("Arcade direction failed: %s at %s" % [direction, strength])
				quit(1)
				return
			player._physics_process(1.0 / 60)
			var expected: Vector3 = Basis(Vector3.UP, initial_yaw) * Vector3(direction.normalized().x, 0, direction.normalized().y)
			var actual := Vector3(player.velocity.x, 0, player.velocity.z).normalized()
			if not actual.is_equal_approx(expected):
				push_error("Arcade movement lost screen alignment during direction change")
				quit(1)
				return
			if not is_equal_approx(Vector2(player.velocity.x, player.velocity.z).length(), player.walk_speed):
				push_error("Diagonal changed movement speed")
				quit(1)
				return
	_axis(JOY_AXIS_LEFT_X, 0.1)
	_axis(JOY_AXIS_LEFT_Y, -0.1)
	assert(player._get_movement_input().is_zero_approx(), "Stick drift must be ignored")
	_axis(JOY_AXIS_LEFT_X, 0.0)
	_axis(JOY_AXIS_LEFT_Y, 0.0)
	player._physics_process(1.0 / 60)
	assert(Vector2(player.velocity.x, player.velocity.z).is_zero_approx(), "Released stick must stop movement")
	player.free()
	print("ARCADE_DIAGONALS PASS: eight directions, partial axes, uniform speed, deadzone and release")
	quit()
