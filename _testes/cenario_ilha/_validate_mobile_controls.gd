extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1280,720)
	root.add_child(viewport)
	var player = load("res://_testes/parkour/Player.tscn").instantiate()
	viewport.add_child(player)
	player.set_physics_process(false)
	player.control_preset = 2
	var controls = player.mobile_controls
	for frame in 3: await process_frame
	var hud: Control = player.gear_container.comic_hud
	hud.set_fragment_goal(31)
	hud.set_objective("Trilha dos céus · 08 / 21\nVerde: retorno seguro.\nSiga as setas. Vermelho: vai sumir!")
	for dimensions in [Vector2i(1280,720),Vector2i(844,390),Vector2i(640,360),Vector2i(390,844)]:
		viewport.size = dimensions
		for frame in 3: await process_frame
		assert(controls.size.is_equal_approx(Vector2(dimensions)))
		assert(controls._radius*1.8 >= 115.0) # Generous jump diameter even on small phones.
		assert(controls._stick_center.y+controls._radius < dimensions.y-30)
		assert(controls._jump_center.y+controls._radius*.9 < dimensions.y-30)
		assert(controls._stick_center.distance_to(controls._jump_center) > controls._radius*1.9)
		assert(Rect2(Vector2.ZERO,Vector2(dimensions)).encloses(Rect2(controls._stick_center-Vector2.ONE*controls._radius,Vector2.ONE*controls._radius*2)))
		var pause_rect: Rect2 = hud.pause_button.get_global_rect()
		assert(not hud.pause_prompt.visible) # Touch uses the pause button itself.
		assert(pause_rect.size.y >= 47.9)
		assert(Rect2(Vector2.ZERO,Vector2(dimensions)).encloses(pause_rect))
		var mission_rect: Rect2 = hud.objective_panel.get_global_rect()
		var stick_rect := Rect2(controls._stick_center-Vector2.ONE*controls._radius,Vector2.ONE*controls._radius*2)
		if mission_rect.intersects(stick_rect):
			push_error("Mission overlaps joystick at %s: %s / %s" % [dimensions,mission_rect,stick_rect])
			quit(1)
			return
	print("MOBILE_LAYOUT_4_VIEWPORTS_OK")
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
	assert(not controls.consume_jump() and controls._camera_finger == -1)
	controls._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	assert(controls.movement.is_zero_approx())
	player.free()
	viewport.free()
	print("MOBILE_CONTROLS PASS")
	quit()
