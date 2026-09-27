extends SceneTree
## Integration check: native HUD adapter, pause/cursor, death UI, scene routes.
var failures := 0
var capture := false

func _initialize() -> void:
	capture = "--capture" in OS.get_cmdline_user_args()
	call_deferred("_run")

func check(condition: bool, message: String) -> void:
	if not condition:
		failures += 1
		push_error(message)

func _run() -> void:
	change_scene_to_file("res://scenes/telaInicial/TelaInicial.tscn")
	await scene_changed
	current_scene.first_button.pressed.emit()
	await process_frame
	current_scene.first_button.pressed.emit()
	await scene_changed
	check(current_scene.scene_file_path == "res://_testes/cenario_ilha/CenarioIlha.tscn","Home → chapter 01 opens the island prototype.")
	await create_timer(1.5).timeout
	var player := current_scene.get_node("Player")
	player.set_physics_process(false)
	var adapter := player.get_node("HUD/gear_container")
	check(is_instance_valid(adapter.comic_hud),"Player gets the new HUD through the existing adapter.")
	player.collect_gear()
	check(adapter.comic_hud.collectibles == player.gears,"HUD counter follows player collection.")
	adapter.update_life(2)
	check(adapter.comic_hud.health == 2,"HUD health follows adapter updates.")
	if capture:
		await create_timer(0.4).timeout
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://docs/ui/07_hud_no_jogo.png")
	var pause := root.get_node("BotaoGlobal")
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	var previous_cursor := Input.get_mouse_mode()
	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.physical_keycode = KEY_ESCAPE
	escape.pressed = true
	root.push_input(escape)
	check(paused,"Pause works inside the 3D island.")
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_VISIBLE,"Pause frees cursor.")
	root.push_input(escape)
	check(Input.get_mouse_mode() == previous_cursor,"Escape resume restores gameplay cursor.")
	await process_frame
	adapter.update_life(0)
	await process_frame
	check(paused and pause.game_over,"Zero lives opens a paused retry screen.")
	check(pause.pause_screen.screen == "retry","Death screen provides retry instead of continue.")
	if capture:
		await create_timer(0.4).timeout
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://docs/ui/08_tentar_novamente.png")
	pause._restart()
	await scene_changed
	await process_frame
	check(not paused,"Retry resumes the game.")
	check(current_scene.get_node("Player").health == 3,"Retry restores player health.")
	# Exercise real existing chapter paths without touching saved progress.
	for index in [1,2,3]:
		var path := "res://scenes/menuDeFases/fase%d/fase_%d.tscn" % [index,index]
		check(change_scene_to_file(path) == OK,"Chapter %d loads." % index)
		await scene_changed
		await process_frame
	change_scene_to_file("res://scenes/telaInicial/TelaInicial.tscn")
	await scene_changed
	await process_frame
	check(current_scene.screen == "home","Returning home restores the new menu.")
	print("HISTORIANDO GAMEPLAY UI: %d failure(s)" % failures)
	quit(1 if failures else 0)
