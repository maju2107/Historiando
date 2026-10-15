extends SceneTree
var viewport: SubViewport
var island: Node3D
var pending := 0
var completed := false
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
	DirAccess.make_dir_recursive_absolute("res://art/island_intro/previews")
	for frame in 3000:
		await process_frame
		if completed and pending == 0: break
	print("INTRO_CAPTURE_COMPLETE")
	island.queue_free()
	await process_frame
	viewport.queue_free()
	await process_frame
	quit()

func _stage(name: String) -> void:
	if name == "finished": completed = true
	if name in ["first_person_blink","seated","dialogue","island_overview","return_closeup","finished"]:
		pending += 1
		_capture_stage.call_deferred(name)

func _capture_stage(name: String) -> void:
	var frames := 12
	if name == "dialogue": frames = 35
	if name == "seated": frames = 24
	for frame in frames: await process_frame
	await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	image.save_png("res://art/island_intro/previews/"+name+".png")
	print("INTRO_CAPTURE ",name)
	pending -= 1
