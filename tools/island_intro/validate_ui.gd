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
	manager.toggle_pause()
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
	manager.toggle_pause()
	check(not paused,"Closing settings must return to the game")
	print("LIVE_SETTINGS_CONTROL_MODES_OK preferences_restored=true")
	island.queue_free()
	await frames()
	print("ISLAND_UI ","PASS" if failures==0 else "FAIL"," failures=",failures)
	quit(0 if failures==0 else 1)
