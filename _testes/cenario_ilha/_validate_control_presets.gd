extends SceneTree
## godot --windowed --fixed-fps 60 --path . --script _testes/cenario_ilha/_validate_control_presets.gd
## Mouse capture requires a window: the headless display always reports a visible cursor.

var _failures := 0
var _world: Node3D
var _player: CharacterBody3D


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)


func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Run this input test without --headless; it checks captured mouse input.")
		quit(1)
		return
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	_check(island.get_node("Player").control_preset == 0, "Island must start with keyboard/gamepad controls")
	island.free()
	_world = Node3D.new()
	root.add_child(_world)
	var floor_body := StaticBody3D.new()
	var collision := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(100, 1, 100)
	collision.shape = box
	floor_body.add_child(collision)
	floor_body.position.y = -0.5
	_world.add_child(floor_body)
	_player = load("res://_testes/parkour/Player.tscn").instantiate()
	_world.add_child(_player)
	_player.set_physics_process(false)
	_player.position = Vector3(0, 0.03, 0)
	for frame in 12:
		await _step()
	_check(_player.is_on_floor(), "Controller test has no floor")
	await _test_camera_relative_movement()
	await _test_free_camera()
	await _test_switching_and_saving()
	_world.free()
	print("CONTROL_PRESETS ", "PASS" if _failures == 0 else "FAIL", " failures=", _failures)
	quit(0 if _failures == 0 else 1)


func _test_camera_relative_movement() -> void:
	_player.camera_pivo.global_rotation = Vector3(deg_to_rad(-18), PI / 2, 0)
	var yaw: float = _player.camera_pivo.global_rotation.y
	_key(KEY_W, true)
	for frame in 12:
		await _step()
	_check(_player.velocity.x < -6.9 and absf(_player.velocity.z) < 0.01, "W must move forward relative to the camera")
	_check(is_equal_approx(_player.camera_pivo.global_rotation.y, yaw), "Walking turned the free camera")
	_key(KEY_W, false)
	_joy(JOY_AXIS_LEFT_X, 1.0)
	for frame in 12:
		await _step()
	_check(_player.velocity.z < -6.9 and absf(_player.velocity.x) < 0.01, "Left stick must move relative to the camera")
	_check(is_equal_approx(_player.camera_pivo.global_rotation.y, yaw), "Left stick turned the free camera")
	_joy(JOY_AXIS_LEFT_X, 0.0)
	await _step()
	_key(KEY_SPACE, true)
	await _step()
	_check(_player.velocity.y > 6.0, "Space did not jump")
	_key(KEY_SPACE, false)
	for frame in 100:
		await _step()
	_check(_player.is_on_floor(), "Player did not land after keyboard jump")
	_joy_button(JOY_BUTTON_A, true)
	await _step()
	_check(_player.velocity.y > 6.0, "Gamepad A did not jump")
	_joy_button(JOY_BUTTON_A, false)
	for frame in 100:
		await _step()
	if _failures == 0:
		print("MOVEMENT_OK keyboard, left stick, Space and gamepad A")


func _test_free_camera() -> void:
	var rotations: Array[Vector3] = []
	for fps in [30.0, 60.0, 120.0]:
		_player.camera_pivo.rotation = Vector3.ZERO
		_mouse(Vector2(100, 40))
		await _step(1.0 / fps)
		rotations.append(_player.camera_pivo.rotation)
		_check(is_equal_approx(_player.camera_pivo.rotation.y, deg_to_rad(-15)), "Mouse yaw depends on FPS or sensitivity is incorrect")
		_check(is_equal_approx(_player.camera_pivo.rotation.x, deg_to_rad(-6)), "Mouse vertical direction is incorrect")
	_check(rotations[0].is_equal_approx(rotations[2]), "Mouse orbit differs between 30 and 120 FPS")
	_player.camera_pivo.rotation = Vector3.ZERO
	_joy(JOY_AXIS_RIGHT_X, 0.1)
	for frame in 60:
		await _step()
	_check(_player.camera_pivo.rotation.is_zero_approx(), "Gamepad drift inside the deadzone moved the camera")
	_joy(JOY_AXIS_RIGHT_X, 1.0)
	for frame in 60:
		await _step()
	_check(absf(_player.camera_pivo.rotation.y + 2.5) < 0.001, "Right stick yaw is incorrect")
	_joy(JOY_AXIS_RIGHT_X, 0.0)
	_joy(JOY_AXIS_RIGHT_Y, 1.0)
	for frame in 60:
		await _step()
	_check(is_equal_approx(_player.camera_pivo.rotation.x, deg_to_rad(-75)), "Camera pitch escaped its lower limit")
	_joy(JOY_AXIS_RIGHT_Y, 0.0)
	_player.invert_camera_y = true
	_player.camera_pivo.rotation.x = 0.0
	_mouse(Vector2(0, 40))
	await _step()
	_check(is_equal_approx(_player.camera_pivo.rotation.x, deg_to_rad(6)), "Invert camera Y did not invert mouse motion")
	_player.invert_camera_y = false
	if _failures == 0:
		print("FREE_CAMERA_OK mouse FPS independence, right stick, deadzone, pitch and inversion")


func _test_switching_and_saving() -> void:
	_mouse(Vector2(100, 100))
	_player.control_preset = 1
	_check(_player.follow_behind, "Arcade preset did not enable automatic camera")
	_check(_player.camera_rotation.is_zero_approx(), "Preset change left queued mouse motion")
	_check(is_equal_approx(_player.camera_pivo.rotation.x, deg_to_rad(-18)), "Arcade preset did not restore its pitch")
	var yaw: float = _player.camera_pivo.global_rotation.y
	_mouse(Vector2(100, 100))
	_joy(JOY_AXIS_RIGHT_X, 1.0)
	for frame in 60:
		await _step()
	_check(is_equal_approx(_player.camera_pivo.global_rotation.y, yaw), "Arcade camera responded to mouse/right stick")
	_joy(JOY_AXIS_RIGHT_X, 0.0)
	for preset in [1, 0]:
		_player.control_preset = preset
		var packed := PackedScene.new()
		_check(packed.pack(_player) == OK, "Could not pack preset")
		var restored: Node = packed.instantiate()
		_check(restored.control_preset == preset, "Preset did not survive scene serialization")
		restored.free()
	_player.camera_pivo.rotation = Vector3.ZERO
	_mouse(Vector2(100, 0))
	await _step()
	_check(is_equal_approx(_player.camera_pivo.rotation.y, deg_to_rad(-15)), "Returning to standard preset did not restore mouse orbit")
	if _failures == 0:
		print("PRESET_SWITCH_OK runtime and scene serialization")


func _step(delta: float = 1.0 / 60.0) -> void:
	await physics_frame
	_player._physics_process(delta)


func _key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _joy(axis: JoyAxis, value: float) -> void:
	var event := InputEventJoypadMotion.new()
	event.axis = axis
	event.axis_value = value
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _joy_button(button: JoyButton, pressed: bool) -> void:
	var event := InputEventJoypadButton.new()
	event.button_index = button
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _mouse(movement: Vector2) -> void:
	var event := InputEventMouseMotion.new()
	event.screen_relative = movement
	_player._unhandled_input(event)
