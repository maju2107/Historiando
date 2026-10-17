extends SceneTree
var viewport: SubViewport
var island: Node3D
var ending: Node3D
var next_advance := 0
var complete := false
var pending := 0

func _initialize() -> void:
	root.hide()
	set_meta("skip_island_intro",true)
	set_meta("ending_preview",true) # Review renders never alter the user's save.
	set_meta("ending_duration_scale",1.0)
	call_deferred("_run")

func _run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(1440,900)
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	viewport.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.control_preset = 0
	player.set_physics_process(false)
	island.get_node("ParkourFlutuante").set_physics_process(false)
	ending = island.get_node("Ending")
	ending.stage_changed.connect(_stage)
	for frame in 8: await process_frame
	var pickups := island.get_node("Topazios").get_children()
	for pickup in pickups.slice(0,30): pickup._on_body_entered(player)
	var last: Area3D = pickups[30]
	player.global_position = last.global_position-Vector3.UP*.15
	player.camera_pivo.rotation = Vector3(deg_to_rad(-22),deg_to_rad(60),0)
	player.reset_physics_interpolation()
	last._on_body_entered(player)
	var deadline := Time.get_ticks_msec()+120000
	while Time.get_ticks_msec()<deadline:
		await process_frame
		if root.get_node("Dialogic").current_timeline != null and Time.get_ticks_msec()>next_advance:
			root.get_node("Dialogic").Inputs.handle_input()
			next_advance = Time.get_ticks_msec()+4000
		if complete and pending == 0: break
	var manager: Node = root.get_node("BotaoGlobal")
	if is_instance_valid(manager.pause_screen): manager.toggle_pause()
	island.queue_free()
	await process_frame
	viewport.queue_free()
	await process_frame
	print("ENDING_CAPTURE_COMPLETE")
	quit()

func _stage(value: String) -> void:
	next_advance = Time.get_ticks_msec()+4200
	if value == "complete": complete = true
	if value == "pickup_settle":
		pending += 1
		_capture_handoff.call_deferred()
	if value in ["pickup_hold","fragments_gather","return_to_clearing","end_portal","end_luggage","end_remember","walk_home","complete"]:
		pending += 1
		_capture.call_deferred(value)

func _capture(value: String) -> void:
	await create_timer(.4 if value == "fragments_gather" else .85,true).timeout
	if value == "complete":
		var manager: Node = root.get_node("BotaoGlobal")
		var layer := CanvasLayer.new()
		layer.layer = 90
		layer.process_mode = Node.PROCESS_MODE_ALWAYS
		viewport.add_child(layer)
		manager.pause_screen.reparent(layer)
		manager.pause_screen._resize()
	else:
		for text in get_nodes_in_group("dialogic_dialog_text"): text.finish_text()
	for frame in 8: await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute("res://art/island_intro/previews/ending")
	viewport.get_texture().get_image().save_png("res://art/island_intro/previews/ending/"+value+".png")
	if value in ["end_luggage","complete"]:
		var original_size := viewport.size
		var player: CharacterBody3D = island.get_node("Player")
		player.control_preset = 2
		for dimensions in [Vector2i(844,390),Vector2i(640,360)]:
			viewport.size = dimensions
			if value == "complete": root.get_node("BotaoGlobal").pause_screen._resize()
			for frame in 8: await process_frame
			await RenderingServer.frame_post_draw
			viewport.get_texture().get_image().save_png("res://art/island_intro/previews/ending/%s_mobile_%dx%d.png" % [value,dimensions.x,dimensions.y])
		viewport.size = original_size
		player.control_preset = 0
		if value == "complete": root.get_node("BotaoGlobal").pause_screen._resize()
	print("ENDING_CAPTURE ",value)
	pending -= 1

func _capture_handoff() -> void:
	var folder := "C:/Users/obran/Historiando_Backups/ui_controls_2026-10-16/ending_handoff"
	DirAccess.make_dir_recursive_absolute(folder)
	var start := Time.get_ticks_msec()
	var next := start
	var times: Array = []
	while Time.get_ticks_msec()-start < 8500:
		await process_frame
		if Time.get_ticks_msec() < next: continue
		await RenderingServer.frame_post_draw
		var frame := viewport.get_texture().get_image()
		frame.resize(720,450,Image.INTERPOLATE_LANCZOS)
		frame.save_png(folder+"/frame_%03d.png" % times.size())
		times.append(Time.get_ticks_msec()-start)
		next = start+times.size()*200
	FileAccess.open(folder+"/timing.json",FileAccess.WRITE).store_string(JSON.stringify(times))
	pending -= 1
