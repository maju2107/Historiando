extends SceneTree
## Real joypad events through native GUI, plus island cutscene/pause integration.
const Interface = preload("res://scenes/ui/interface.gd")
const Kit = preload("res://scenes/ui/ui_kit.gd")
var failures := 0
var checks := 0
var _had_settings := false
var _settings_bytes := PackedByteArray()

func _initialize() -> void:
	_had_settings = FileAccess.file_exists(Interface.SETTINGS_PATH)
	if _had_settings: _settings_bytes = FileAccess.get_file_as_bytes(Interface.SETTINGS_PATH)
	call_deferred("_run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)

func tap(button: JoyButton, device := 7) -> void:
	var event := InputEventJoypadButton.new()
	event.device = device
	event.button_index = button
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame
	await process_frame
	event.pressed = false
	Input.parse_input_event(event)
	await process_frame
	await process_frame

func _run() -> void:
	create_timer(75).timeout.connect(func():
		_restore_settings()
		push_error("Arcade verification timed out")
		quit(1))
	root.size = Vector2i(1600,900)
	var config := Interface.load_settings()
	config.set_value("controls","preset",1)
	config.set_value("audio","volume",.5)
	config.set_value("audio","mute",false)
	config.save(Interface.SETTINGS_PATH)
	var menu := Interface.new()
	root.add_child(menu)
	current_scene = menu
	await process_frame
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_HIDDEN,"Arcade home hides the cursor")
	await tap(JOY_BUTTON_DPAD_DOWN)
	check((root.gui_get_focus_owner() as Button).text=="AJUSTES","Down selects the row below Start")
	await tap(JOY_BUTTON_DPAD_RIGHT)
	check((root.gui_get_focus_owner() as Button).text=="SOBRE O JOGO","Right selects the button beside Settings")
	await tap(JOY_BUTTON_DPAD_DOWN)
	check((root.gui_get_focus_owner() as Button).text=="SAIR","Down stays in the right column")
	await tap(JOY_BUTTON_DPAD_LEFT)
	check((root.gui_get_focus_owner() as Button).text=="CRÉDITOS","Left selects Credits beside Exit")
	await tap(JOY_BUTTON_DPAD_UP)
	check((root.gui_get_focus_owner() as Button).text=="AJUSTES","Up stays in the left column")
	var axis := InputEventJoypadMotion.new()
	axis.device = 7
	axis.axis = JOY_AXIS_LEFT_Y
	axis.axis_value = -1.0
	Input.parse_input_event(axis)
	await process_frame
	await process_frame
	axis.axis_value = 0.0
	Input.parse_input_event(axis)
	await process_frame
	check(menu.first_button.has_focus(),"The stick axis navigates upward and neutral stops navigation")
	await tap(JOY_BUTTON_A)
	check(menu.screen == "chapters","A activates the main button on a non-primary controller")
	await tap(JOY_BUTTON_B)
	check(menu.screen == "home","B returns from chapter selection")
	await tap(JOY_BUTTON_DPAD_DOWN)
	await tap(JOY_BUTTON_A)
	check(menu.screen == "settings","Settings is accessible from Home using only the controller")
	if menu.screen != "settings": menu._open_settings("home")
	await process_frame
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture="):
			await create_timer(.3).timeout
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(argument.trim_prefix("--capture="))
	var slider: HSlider = menu.content.get_node("MasterVolume")
	var selector: OptionButton = menu.content.get_node("ControlPresetSelector")
	check(menu.content.get_node("NavigationHint").text.contains("A - Confirmar"),"Settings explains A confirmation")
	await tap(JOY_BUTTON_DPAD_DOWN)
	check(slider.has_focus(),"Down from Back wraps to volume")
	await tap(JOY_BUTTON_DPAD_RIGHT)
	check(slider.value > 50 and slider.has_focus(),"Right adjusts volume without leaving the slider")
	await tap(JOY_BUTTON_DPAD_LEFT)
	check(slider.value == 50,"Left lowers volume")
	check(is_equal_approx(float(Interface.load_settings().get_value("audio","volume")),.5),"Controller volume changes are saved")
	var switches: Array[CheckButton] = []
	for child in menu.content.get_children():
		if child is CheckButton: switches.append(child)
	await tap(JOY_BUTTON_DPAD_DOWN)
	check(switches[0].has_focus(),"Mute is reachable from volume")
	await tap(JOY_BUTTON_A)
	check(switches[0].button_pressed,"A changes a setting")
	await tap(JOY_BUTTON_A)
	for i in [1,2]:
		await tap(JOY_BUTTON_DPAD_DOWN)
		check(switches[i].has_focus(),"Every remaining switch is reachable")
	await tap(JOY_BUTTON_DPAD_DOWN)
	check(selector.has_focus(),"Control mode is reachable from the switches")
	await tap(JOY_BUTTON_A)
	check(selector.get_popup().visible,"A opens the native control-mode choices")
	await tap(JOY_BUTTON_DPAD_DOWN)
	await tap(JOY_BUTTON_A)
	check(selector.selected == 2,"Controller can select Mobile")
	check(int(Interface.load_settings().get_value("controls","preset")) == 2,"New control mode is saved")
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_VISIBLE,"Mobile mode retains its normal UI cursor")
	await tap(JOY_BUTTON_A)
	await tap(JOY_BUTTON_DPAD_UP)
	await tap(JOY_BUTTON_A)
	check(selector.selected == 1,"Controller can select Fliperama again")
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_HIDDEN,"Changing back to Arcade immediately hides the cursor")
	await tap(JOY_BUTTON_DPAD_DOWN)
	check(menu.first_button.has_focus(),"Back remains reachable after closing the dropdown")
	await tap(JOY_BUTTON_A)
	check(menu.screen == "home","A confirms Back")
	menu.show_screen("credits")
	await tap(JOY_BUTTON_B)
	check(menu.screen == "home","Credits returns with the controller")
	menu._confirm_exit()
	await tap(JOY_BUTTON_DPAD_RIGHT)
	check((root.gui_get_focus_owner() as Button).text == "CONFIRMAR","Confirmation buttons are controller accessible")
	await tap(JOY_BUTTON_B)
	check(not is_instance_valid(menu.modal),"B cancels a confirmation")
	menu.queue_free()
	await process_frame
	set_meta("intro_duration_scale",.05)
	set_meta("ending_duration_scale",.05)
	set_meta("ending_preview",true)
	change_scene_to_file(Interface.ISLAND_PATH)
	await scene_changed
	await create_timer(.4).timeout
	var player := current_scene.get_node("Player")
	var opening := current_scene.get_node("Opening")
	var pause := root.get_node("BotaoGlobal")
	check(opening.active,"The real opening is running")
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_HIDDEN,"Opening keeps the arcade cursor hidden")
	await tap(JOY_BUTTON_X)
	check(not paused,"X does not pause during a cutscene")
	await tap(JOY_BUTTON_Y)
	check(paused and is_instance_valid(pause.pause_screen),"Y pauses a cutscene")
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_HIDDEN,"Arcade pause keeps the cursor hidden")
	pause.pause_screen._open_settings("pause")
	await process_frame
	pause.pause_screen._change_controls(0)
	check(pause.previous_mouse_mode == Input.MOUSE_MODE_VISIBLE,"Switching to desktop during a cutscene restores its UI cursor on resume")
	pause.pause_screen._change_controls(1)
	check(pause.previous_mouse_mode == Input.MOUSE_MODE_HIDDEN,"Switching to arcade during a cutscene restores a hidden cursor")
	await tap(JOY_BUTTON_Y)
	check(paused and pause.pause_screen.screen == "pause","Y returns from settings to pause")
	await tap(JOY_BUTTON_Y)
	check(not paused and Input.get_mouse_mode() == Input.MOUSE_MODE_HIDDEN,"Resuming a cutscene keeps the cursor hidden")
	opening.skip()
	player.set_physics_process(false)
	await process_frame
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED,"Gameplay restores the captured cursor")
	check(player._get_movement_input().is_zero_approx(),"Connected controllers at rest do not move the player")
	for direction in [Vector2.UP,Vector2.DOWN,Vector2.LEFT,Vector2.RIGHT,Vector2(-1,-1),Vector2(1,-1),Vector2(-1,1),Vector2(1,1),Vector2.ZERO]:
		for component in [JOY_AXIS_LEFT_X,JOY_AXIS_LEFT_Y]:
			var movement_event := InputEventJoypadMotion.new()
			movement_event.device = 7
			movement_event.axis = component
			movement_event.axis_value = direction.x if component==JOY_AXIS_LEFT_X else direction.y
			Input.parse_input_event(movement_event)
		await physics_frame
		check(player._get_movement_input().is_equal_approx(direction.normalized()),"Stick direction and neutral are read correctly: "+str(direction))
		player._physics_process(1.0/60.0)
	check(Vector2(player.velocity.x,player.velocity.z).is_zero_approx(),"Releasing the stick stops actual player velocity")
	await tap(JOY_BUTTON_X)
	check(not paused,"X does not pause gameplay")
	await tap(JOY_BUTTON_Y)
	check(paused,"Y pauses gameplay")
	await tap(JOY_BUTTON_Y)
	check(not paused and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED,"Resuming gameplay restores its captured cursor")
	var quiz: Node = current_scene.get_node("ParkourFlutuante").quiz
	quiz._begin_hint(0)
	await create_timer(.8).timeout
	check(quiz.hint_active and Input.get_mouse_mode() == Input.MOUSE_MODE_HIDDEN,"Kai's wrong-answer hint keeps the cursor hidden")
	root.get_node("Dialogic").end_timeline(true)
	await create_timer(.1).timeout
	var ending: Node = current_scene.get_node("Ending")
	ending._hud.fragments_complete = true
	ending._start()
	await create_timer(.15).timeout
	check(ending.active and Input.get_mouse_mode() == Input.MOUSE_MODE_HIDDEN,"Final cutscene keeps the cursor hidden")
	current_scene.queue_free()
	await process_frame
	_restore_settings()
	Interface.apply_settings()
	print("HISTORIANDO ARCADE CONTROLS: %d checks, %d failure(s)" % [checks,failures])
	quit(1 if failures else 0)

func _restore_settings() -> void:
	if _had_settings:
		var file := FileAccess.open(Interface.SETTINGS_PATH,FileAccess.WRITE)
		file.store_buffer(_settings_bytes)
	else:
		DirAccess.remove_absolute(Interface.SETTINGS_PATH)
