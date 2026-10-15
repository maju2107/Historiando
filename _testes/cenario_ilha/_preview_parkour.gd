extends SceneTree
## Real-render review: godot --path . --script res://_testes/cenario_ilha/_preview_parkour.gd

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_capture")


func _capture() -> void:
	root.size = Vector2i(1440, 900)
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	var course: Node3D = island.get_node("ParkourFlutuante")
	course.set_physics_process(false)
	course.cycle_enabled = false
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	DirAccess.make_dir_recursive_absolute("res://tmp/parkour")
	var camera := Camera3D.new()
	island.add_child(camera)
	camera.current = true
	camera.fov = 65
	camera.look_at_from_position(Vector3(-2, 17.8, -12), Vector3(9, 14.8, -3.5))
	await _save("01_entrance")
	player.get_node("HUD").hide()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 64
	camera.look_at_from_position(Vector3(44, 49, 52), Vector3(0, 14, 0))
	await _save("02_course")
	camera.projection = Camera3D.PROJECTION_PERSPECTIVE
	var deck: Node3D = course.get_platforms()[7]
	camera.look_at_from_position(deck.global_position + Vector3(-7, 6, 7), deck.global_position + Vector3(0, 0.2, 0))
	await _save("03_checkpoint")
	course.cycle_enabled = true
	course.apply_cycle_time(course.stagger_seconds * 8 + course.active_seconds - 0.05)
	deck = course.get_platforms()[8]
	camera.look_at_from_position(deck.global_position + Vector3(-6, 5, 6), deck.global_position)
	await _save("04_warning")
	course.apply_cycle_time(course.stagger_seconds * 8 + course.active_seconds + 0.2)
	await _save("05_ghost")
	course.cycle_enabled = false
	deck = course.get_platforms()[7]
	player.global_position = deck.surface_position()
	course._register_landing(7)
	player.get_node("HUD").show()
	camera.look_at_from_position(deck.global_position + Vector3(0, 5, 7), deck.global_position + Vector3(0, 0, -2))
	await _save("06_progress")
	root.remove_child(island)
	island.free()
	quit()


func _save(filename: String) -> void:
	for frame in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://tmp/parkour/%s.png" % filename)
