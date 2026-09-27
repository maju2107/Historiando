extends SceneTree
## Run with --headless --script res://scenes/ui/verify_ui.gd for behavior checks;
## omit --headless and add -- --capture for native-rendered screen previews.
var failures := 0
var capture := false

func _initialize() -> void:
	capture = "--capture" in OS.get_cmdline_user_args()
	call_deferred("_run")

func check(condition: bool, message: String) -> void:
	if not condition:
		failures += 1
		push_error(message)

func settle() -> void:
	await create_timer(0.28).timeout

func snapshot(filename: String) -> void:
	if not capture: return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://docs/ui/"+filename+".png")

func _run() -> void:
	root.content_scale_size = Vector2i(1600,900)
	root.size = Vector2i(1600,900)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	var menu = load("res://scenes/telaInicial/TelaInicial.tscn").instantiate()
	root.add_child(menu)
	current_scene = menu
	await settle()
	check(menu.screen == "home", "Main scene opens the home screen.")
	check(menu.first_button.has_focus(), "Main action receives keyboard focus.")
	await snapshot("01_inicio")
	menu.first_button.pressed.emit()
	await settle()
	check(menu.screen == "chapters", "Start button opens chapter selection.")
	var chapter_buttons: Array[Button] = []
	for child in menu.content.get_children():
		if child is Button and child.text in ["EXPLORAR   ›", "BLOQUEADO"]: chapter_buttons.append(child)
	check(chapter_buttons.size() == 3,"Three chapter buttons exist.")
	if chapter_buttons.size() == 3:
		check(not chapter_buttons[0].disabled,"First chapter is available.")
		check(chapter_buttons[1].disabled == not root.get_node("FaseCore").fase1_concluida,"Chapter two respects saved progress.")
		check(chapter_buttons[2].disabled == not root.get_node("FaseCore").fase2_concluida,"Chapter three respects saved progress.")
	await snapshot("02_capitulos")
	check(menu.chapter_path(1) == menu.ISLAND_PATH,"First large chapter card routes to the island prototype.")
	check(menu.chapter_path(2).ends_with("fase2/fase_2.tscn"),"Other chapter routes remain intact.")
	for child in menu.content.get_children():
		if child is Button: check(not child.text.contains("PROTÓTIPO 3D"),"No separate island prototype button remains.")
	menu.show_screen("credits")
	await settle()
	var credits: RichTextLabel = menu.content.get_node("AssetCredits")
	check(menu.Credits.ENTRIES.size() == 8,"All eight workbook asset rows are included.")
	for entry in menu.Credits.ENTRIES:
		check(credits.text.contains(entry.title) and credits.text.contains(entry.url),"Credits include title and source for "+entry.title)
	await snapshot("10_creditos")
	credits.scroll_to_line(credits.get_line_count()-1)
	await settle()
	await snapshot("11_creditos_fontes")
	menu.show_screen("home")
	menu._confirm_exit()
	check(is_instance_valid(menu.modal),"Exit opens a themed modal.")
	check((menu.get_viewport().gui_get_focus_owner() as Button).text == "CANCELAR","Cancel receives initial focus.")
	await settle()
	await snapshot("12_aviso")
	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.physical_keycode = KEY_ESCAPE
	escape.pressed = true
	root.push_input(escape)
	check(not is_instance_valid(menu.modal),"Escape dismisses the modal without leaving home.")
	check(menu.first_button.has_focus(),"Modal restores the previous focus.")
	menu.set_meta("test_confirmed",false)
	menu._confirm("Teste", "Confirmação de teste.",func(): menu.set_meta("test_confirmed",true))
	menu._accept_modal()
	check(menu.get_meta("test_confirmed"),"Confirm executes the supplied action.")
	menu._open_settings("home")
	await settle()
	await snapshot("03_ajustes")
	menu.first_button.pressed.emit()
	check(menu.screen == "home","Settings returns to its calling screen.")
	menu.show_screen("demo")
	await settle()
	menu.first_button.pressed.emit()
	check(menu.demo_hud.collectibles == 1,"Collectible counter updates.")
	menu.demo_hud.set_health(2)
	check(menu.demo_hud.health == 2,"HUD accepts live health updates.")
	check(menu.demo_hud.notification.visible,"Collection notification appears.")
	await snapshot("04_hud")
	var pause = root.get_node("BotaoGlobal")
	pause.toggle_pause()
	await settle()
	check(paused,"Pause stops the game tree.")
	check(pause.pause_screen.first_button.has_focus(),"Pause focuses Continue.")
	await snapshot("05_pausa")
	pause.pause_screen._confirm_home()
	root.push_input(escape)
	check(paused and not is_instance_valid(pause.pause_screen.modal),"Escape dismisses pause confirmation without resuming gameplay.")
	pause.toggle_pause()
	await process_frame
	check(not paused,"Resume unpauses the game tree.")
	check(Input.get_mouse_mode() == Input.MOUSE_MODE_VISIBLE,"Resume restores previous cursor mode.")
	menu._open_about("home")
	await settle()
	await snapshot("06_sobre")
	menu.show_screen("type")
	await settle()
	await snapshot("09_tipografia")
	# Check layout normalization at small and wide window sizes.
	for dimensions in [Vector2i(1280,720),Vector2i(1024,768),Vector2i(2560,1080)]:
		root.size = dimensions
		await process_frame
		menu._resize()
		check(menu.canvas.position.x >= -0.1 and menu.canvas.position.y >= -0.1,"Canvas stays within viewport at %s." % dimensions)
	menu.queue_free()
	await process_frame
	print("HISTORIANDO UI: %d failure(s)" % failures)
	quit(1 if failures else 0)
