extends SceneTree

func _initialize() -> void:
	root.hide()
	call_deferred("_capture")


func _capture() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(900, 900)
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var studio := Node3D.new()
	viewport.add_child(studio)
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.09, 0.10, 0.11)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color.WHITE
	environment.ambient_light_energy = 0.65
	world.environment = environment
	studio.add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-40, -30, 0)
	key.light_energy = 1.15
	studio.add_child(key)
	var fill := OmniLight3D.new()
	fill.position = Vector3(-2, 1.5, 2)
	fill.omni_range = 8
	fill.light_energy = 1.0
	studio.add_child(fill)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 1.85
	camera.position = Vector3(1.5, 1.3, 3.8)
	studio.add_child(camera)
	camera.look_at(Vector3(0, 0.72, 0.08), Vector3.UP)
	camera.current = true
	var packed := load("res://assets/characters/yara/YaraSkin.tscn") as PackedScene
	var model := packed.instantiate() as Node3D
	model.scale = Vector3.ONE * 1.25
	studio.add_child(model)
	var animator := model.get_node("AnimationPlayer") as AnimationPlayer
	var skin := model.find_child("Yara_PaintedSkin", true, false) as MeshInstance3D
	if skin != null:
		for surface in skin.mesh.get_surface_count():
			var material := skin.get_active_material(surface) as StandardMaterial3D
			print("YARA_MATERIAL ", surface, " ", material.resource_name, " vcolor=", material.vertex_color_use_as_albedo, " albedo_texture=", material.albedo_texture != null, " normal_texture=", material.normal_texture != null)
	var folder := "res://art/yara/previews"
	DirAccess.make_dir_recursive_absolute(folder)
	for sample in [{"clip": "Idle", "time": 0.0}, {"clip": "Walk", "time": 0.2}, {"clip": "Run", "time": 0.15}, {"clip": "Jump", "time": 0.07}, {"clip": "Flip", "time": 0.27}, {"clip": "VictorySign", "time": 0.27}]:
		animator.play(sample["clip"], 0)
		animator.seek(sample["time"], true)
		animator.pause()
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		var image := viewport.get_texture().get_image()
		if image.is_empty():
			printerr("YARA_CAPTURE_EMPTY")
			quit(1)
			return
		image.save_png(folder + "/" + sample["clip"] + ".png")
		print("YARA_GPU_CAPTURE ", sample["clip"])
	camera.size = 0.68
	camera.position = Vector3(0.5, 1.13, 3.4)
	camera.look_at(Vector3(0, 1.02, 0.09), Vector3.UP)
	animator.play("Idle", 0)
	animator.seek(0, true)
	animator.pause()
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(folder + "/Face.png")
	camera.size = 1.85
	camera.position = Vector3(-2, 1.25, -3.3)
	camera.look_at(Vector3(0, 0.72, 0.08), Vector3.UP)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(folder + "/Back.png")
	camera.size = 0.48
	camera.position = Vector3(0.5, 0.38, 3.4)
	camera.look_at(Vector3(0, 0.16, 0.06), Vector3.UP)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(folder + "/Shoes.png")
	camera.size = 0.33
	camera.position = Vector3(0.3, 0.74, 3.4)
	camera.look_at(Vector3(0, 0.66, 0.04), Vector3.UP)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(folder + "/Chest.png")
	quit()

