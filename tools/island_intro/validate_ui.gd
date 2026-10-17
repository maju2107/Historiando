extends SceneTree
const Interface = preload("res://scenes/ui/interface.gd")
var failures := 0

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func check(value: bool,message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func frames() -> void:
	for frame in 6: await process_frame

func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	await frames()
	var hud: Control = player.gear_container.comic_hud
	check(hud.pause_button.position.y < 120,"Pause must occupy the former top-right counter area")
	check(hud.pause_prompt.texture != null,"Pause needs the supplied Y artwork")
	check(hud.pause_prompt.get_parent() == hud.pause_button and hud.pause_prompt.size.x == 46,"Y must be a larger passive sign at the pause corner")
	check(hud.pause_prompt.get_rect().position.y < hud.pause_button.size.y and hud.pause_prompt.get_rect().end.y > hud.pause_button.size.y,"Y should overlap the pause button's lower edge")
	check(hud.pause_prompt.texture.get_width() >= 512 and hud.pause_prompt.texture.get_image().has_mipmaps(),"Y should use a high-resolution mipmapped vector import")
	for label in hud.canvas.find_children("*","Label",true,false):
		check(not "W A S D" in label.text,"The keyboard control guide should be removed")
		check(not label.text.begins_with("FRAGMENTOS      "),"The duplicate top fragment counter remains")
	var short_height := 0.0
	for message in ["Descubra onde você está.\nSiga os cristais pela ilha.","Trilha dos céus · 01 / 21\nVerde: retorno seguro. Siga as setas. Vermelho: vai sumir!", "Este é um objetivo com bastante texto para verificar a expansão automática do painel roxo e manter toda a missão legível, incluindo a última linha."]:
		hud.set_objective(message)
		await frames()
		var panel: Rect2 = hud.objective_panel.get_global_rect()
		var text: Rect2 = hud.objective.get_global_rect()
		check(panel.encloses(text),"Mission text extends beyond the purple panel")
		if short_height==0: short_height = panel.size.y
	check(hud.objective_panel.get_global_rect().size.y > short_height,"Long missions should expand the panel")
	hud.set_objective("Descubra onde você está.")
	await frames()
	check(hud.objective_panel.get_global_rect().size.y < short_height,"Short missions should shrink the panel")
	check(player.mobile_controls.find_children("*","OptionButton",true,false).is_empty(),"Developer control selector remains on HUD")
	print("RESPONSIVE_MISSION_PANEL_OK")
	var settings_exists := FileAccess.file_exists(Interface.SETTINGS_PATH)
	var backup := FileAccess.get_file_as_bytes(Interface.SETTINGS_PATH) if settings_exists else PackedByteArray()
	var manager := root.get_node("BotaoGlobal")
	var pause_input := InputEventJoypadButton.new()
	pause_input.button_index = JOY_BUTTON_Y
	pause_input.pressed = true
	manager._input(pause_input)
	check(paused and is_instance_valid(manager.pause_screen),"Controller Y must open pause beside the matching prompt")
	manager.pause_screen._open_settings("pause")
	await frames()
	var selector: OptionButton = manager.pause_screen.find_child("ControlPresetSelector",true,false)
	check(selector != null and selector.item_count==3,"Settings must offer all three control presets")
	for preset in [1,2,0]:
		selector.item_selected.emit(preset)
		check(player.control_preset == preset,"Control mode did not change while playing")
		check(paused,"Changing controls should not unpause the game")
		check(Input.get_mouse_mode() == Input.MOUSE_MODE_VISIBLE,"Settings must retain a usable cursor")
		check(int(Interface.load_settings().get_value("controls","preset",-1))==preset,"Control preference was not saved")
	if settings_exists:
		FileAccess.open(Interface.SETTINGS_PATH,FileAccess.WRITE).store_buffer(backup)
	else:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(Interface.SETTINGS_PATH))
	manager._input(pause_input)
	check(paused and manager.pause_screen.screen == "pause","Y from settings should return to the pause menu")
	manager._input(pause_input)
	check(not paused,"Closing settings must return to the game")
	player.control_preset = 2
	await frames()
	check(not hud.pause_prompt.visible,"Mobile pause should not show a controller Y prompt")
	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.position = root.get_final_transform()*hud.pause_button.get_global_rect().get_center()
	touch.pressed = true
	Input.parse_input_event(touch)
	await process_frame
	touch.pressed = false
	Input.parse_input_event(touch)
	await frames()
	check(paused and is_instance_valid(manager.pause_screen),"A mobile tap on pause must open the pause menu")
	if is_instance_valid(manager.pause_screen): manager.toggle_pause()
	print("LIVE_SETTINGS_CONTROL_MODES_OK preferences_restored=true")
	island.queue_free()
	await frames()
	print("ISLAND_UI ","PASS" if failures==0 else "FAIL"," failures=",failures)
	quit(0 if failures==0 else 1)
