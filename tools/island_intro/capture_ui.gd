extends SceneTree
const Interface = preload("res://scenes/ui/interface.gd")
var viewport: SubViewport

func _initialize() -> void:
	root.hide()
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func _run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(1600,900)
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	viewport.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	var course: Node3D = island.get_node("ParkourFlutuante")
	course.cycle_enabled = false
	course.set_physics_process(false)
	for frame in 8: await process_frame
	var platform: Node3D = course.get_platforms()[7]
	player.global_position = platform.surface_position()
	var camera := Camera3D.new()
	island.add_child(camera)
	camera.current = true
	camera.look_at_from_position(platform.global_position+Vector3(-6,5,6),platform.global_position+Vector3(0,1,0))
	var hud: Control = player.gear_container.comic_hud
	hud.set_location("PLEISTOCENO","TRILHA DOS CÉUS")
	hud.set_objective("Trilha dos céus · 08 / 21\nVerde: retorno seguro.\nSiga as setas. Vermelho: vai sumir!")
	DirAccess.make_dir_recursive_absolute("res://art/island_intro/previews")
	await save_image("mission_panel")
	hud.show_epoch_intro()
	for frame in 40: await process_frame
	await save_image("pleistoceno_presentation")
	hud.epoch_presentation.hide()
	var menu := Interface.new()
	menu.initial_screen = "pause"
	var menu_layer := CanvasLayer.new()
	menu_layer.layer = 90
	viewport.add_child(menu_layer)
	menu_layer.add_child(menu)
	menu._open_settings("pause")
	await save_image("settings_controls")
	print("INTRO_UI_CAPTURE_OK")
	island.queue_free(); menu.queue_free()
	await process_frame
	viewport.queue_free()
	await process_frame
	quit()

func save_image(name: String) -> void:
	for frame in 12: await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://art/island_intro/previews/"+name+".png")
