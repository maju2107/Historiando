extends SceneTree
## Offscreen Vulkan capture of the actual island and its existing player HUD.

var _viewport: SubViewport

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	root.hide()
	call_deferred("_capture")

func _capture() -> void:
	_viewport = SubViewport.new()
	_viewport.size = Vector2i(1440, 900)
	_viewport.own_world_3d = true
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(_viewport)
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	_viewport.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	var course: Node3D = island.get_node("ParkourFlutuante")
	course.cycle_enabled = false
	course.set_physics_process(false)
	var camera := Camera3D.new()
	island.add_child(camera)
	camera.current = true
	camera.fov = 58
	camera.look_at_from_position(Vector3(-4.5,7.2,11.5),Vector3(-8,4.7,15))
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	DirAccess.make_dir_recursive_absolute("res://art/topazio_imperial/gameplay")
	await _save("01_topazio_na_ilha")
	var pickup: Area3D = island.get_node("Topazios/Trilha01")
	player.global_position = pickup.global_position - Vector3.UP * .65
	for frame in 8:
		await physics_frame
	await _save("02_fragmento_coletado")
	print("TOPAZIO_CAPTURE_OK fragments=",player.gears)
	island.queue_free()
	await process_frame
	_viewport.queue_free()
	await process_frame
	quit()

func _save(name: String) -> void:
	for frame in 15:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := _viewport.get_texture().get_image()
	assert(not image.is_empty(),"Capture image is empty")
	image.save_png("res://art/topazio_imperial/gameplay/" + name + ".png")
