extends SceneTree
const DEST := "C:/Users/obran/Historiando_Backups/ui_controls_2026-10-16/quiz_motion"

func _initialize() -> void:
	root.hide()
	set_meta("skip_island_intro",true)
	set_meta("skip_island_ending",true)
	call_deferred("_run")

func _run() -> void:
	for dimensions in [Vector2i(1440,900),Vector2i(844,390)]:
		var viewport := SubViewport.new()
		viewport.size = dimensions
		viewport.own_world_3d = true
		viewport.msaa_3d = Viewport.MSAA_4X
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
		viewport.add_child(island)
		var player: CharacterBody3D = island.get_node("Player")
		player.set_physics_process(false)
		player.control_preset = 2 if dimensions.y < 550 else 0
		var course: Node3D = island.get_node("ParkourFlutuante")
		course.cycle_enabled = false
		var quiz: Node3D = course.quiz
		var platform: Node3D = course.get_platforms()[4]
		player.global_position = platform.surface_position()+Vector3.UP*.08
		player.camera_pivo.rotation = Vector3(deg_to_rad(-18),platform.rotation.y,0)
		player.gobot.rotation.y = platform.rotation.y+PI
		for frame in 12: await process_frame
		var folder := DEST+"/%dx%d" % [dimensions.x,dimensions.y]
		DirAccess.make_dir_recursive_absolute(folder)
		var start := Time.get_ticks_msec()
		var next := start
		var entered := false
		var chosen := false
		var times: Array = []
		while Time.get_ticks_msec()-start < 3200:
			await process_frame
			var elapsed := Time.get_ticks_msec()-start
			if elapsed >= 300 and not entered:
				entered = true
				quiz.on_landing(4)
				player.gear_container.comic_hud.notify_checkpoint("PONTO DE RETORNO ATIVADO")
			if elapsed >= 1900 and not chosen:
				chosen = true
				quiz.on_landing(5)
			if Time.get_ticks_msec() < next: continue
			await RenderingServer.frame_post_draw
			var image := viewport.get_texture().get_image()
			if dimensions.x > 1000: image.resize(720,450,Image.INTERPOLATE_LANCZOS)
			image.save_png(folder+"/frame_%03d.png" % times.size())
			times.append(Time.get_ticks_msec()-start)
			next = start+times.size()*65
		FileAccess.open(folder+"/timing.json",FileAccess.WRITE).store_string(JSON.stringify(times))
		print("QUIZ_MOTION_CAPTURE ",dimensions," frames=",times.size())
		island.queue_free()
		await process_frame
		viewport.queue_free()
		await process_frame
	quit()
