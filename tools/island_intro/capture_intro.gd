extends SceneTree
var viewport: SubViewport
var island: Node3D
var pending := 0
var completed := false
var next_advance := 0
const Intro = preload("res://_testes/cenario_ilha/intro/island_intro.gd")

func _initialize() -> void:
	root.hide()
	set_meta("intro_duration_scale",.65)
	Intro.seen_this_session = false
	call_deferred("_run")

func _run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(1440,900)
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	island.get_node("Opening").stage_changed.connect(_stage)
	viewport.add_child(island)
	island.get_node("Player").control_preset = 0
	DirAccess.make_dir_recursive_absolute("res://art/island_intro/previews")
	var deadline := Time.get_ticks_msec()+150000
	while Time.get_ticks_msec()<deadline:
		await process_frame
		# Review automation only: the shipped timelines always wait for input.
		if Time.get_ticks_msec()>next_advance and root.get_node("Dialogic").current_timeline != null:
			root.get_node("Dialogic").Inputs.handle_input()
			next_advance = Time.get_ticks_msec()+4000
		if completed and pending == 0: break
	print("INTRO_CAPTURE_COMPLETE")
	island.queue_free()
	await process_frame
	viewport.queue_free()
	await process_frame
	quit()

func _stage(name: String) -> void:
	next_advance = Time.get_ticks_msec()+4200
	if name == "finished": completed = true
	if name in ["yara_console","kai_correct"]:
		pending += 1
		_capture_motion.call_deferred(name)
	if name in ["first_person_blink","seated","dialogue","island_overview","return_closeup","kai_when","kai_epoch","yara_console","kai_correct","kai_mission","finished"]:
		pending += 1
		_capture_stage.call_deferred(name)

func _capture_stage(name: String) -> void:
	var frames := 12
	if name == "dialogue": frames = 35
	if name == "seated": frames = 24
	for frame in frames: await process_frame
	if name.begins_with("kai_") or name.begins_with("yara_"):
		await create_timer(.55).timeout
		for text in get_nodes_in_group("dialogic_dialog_text"):
			text.finish_text() # Finish reveal without advancing the current line.
		for frame in 3: await process_frame
	await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	image.save_png("res://art/island_intro/previews/"+name+".png")
	if name == "dialogue":
		var player: CharacterBody3D = island.get_node("Player")
		var original_preset: int = player.control_preset
		var original_size := viewport.size
		player.control_preset = 2
		viewport.size = Vector2i(844,390)
		for frame in 8: await process_frame
		await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png("res://art/island_intro/previews/dialogue_mobile.png")
		player.control_preset = original_preset
		viewport.size = original_size
	print("INTRO_CAPTURE ",name)
	pending -= 1

func _capture_motion(name: String) -> void:
	var folder := "C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16/dialogue_motion"
	DirAccess.make_dir_recursive_absolute(folder)
	await create_timer(.22).timeout
	for sample in 20:
		await RenderingServer.frame_post_draw
		var frame := viewport.get_texture().get_image()
		frame.resize(720,450,Image.INTERPOLATE_LANCZOS)
		frame.save_png(folder+"/"+name+"_%02d.png"%sample)
		await create_timer(.075).timeout
	pending -= 1
