extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var player = load("res://_testes/parkour/Player.tscn").instantiate()
	root.add_child(player)
	player.set_physics_process(false)
	player.control_preset = 2
	var controls = player.mobile_controls
	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.pressed = true
	touch.position = controls._stick_center + Vector2(controls._radius, 0)
	controls._unhandled_input(touch)
	assert(player._get_movement_input().x > 0.99)
	touch.index = 1
	touch.position = controls._jump_center
	controls._unhandled_input(touch)
	assert(controls.consume_jump())
	assert(not controls.consume_jump())
	touch.index = 2
	touch.position = Vector2(root.size) * Vector2(0.5, 0.4)
	controls._unhandled_input(touch)
	var drag := InputEventScreenDrag.new()
	drag.index = 2
	drag.relative = Vector2(100, 40)
	controls._unhandled_input(drag)
	assert(player.camera_rotation.x > 0.0)
	assert(player._get_movement_input().x > 0.99)
	touch.index = 0
	touch.pressed = false
	controls._input(touch)
	assert(player._get_movement_input().is_zero_approx())
	player.control_preset = 1
	assert(not controls._mobile and controls._camera_finger == -1)
	player.control_preset = 2
	controls._unhandled_input(drag)
	assert(player.camera_rotation.is_zero_approx())
	controls._notification(Node.NOTIFICATION_PAUSED)
	assert(controls.movement.is_zero_approx())
	player.free()
	print("MOBILE_CONTROLS PASS")
	quit()
