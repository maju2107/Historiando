extends SceneTree
## Native input dispatch: a click/tap advances once, and controller A reveals
## then advances. No world or character edits are needed for this UI check.
var failures := 0
var cue := ""
var dialogic: Node
var gui_clicks := 0

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool,message: String) -> void:
	if not condition:
		failures += 1
		push_error(message)

func settle() -> void:
	for frame in 4: await process_frame

func screen_position(fraction: Vector2) -> Vector2:
	# parse_input_event uses window coordinates, before viewport stretch.
	return root.get_final_transform()*(root.get_visible_rect().size*fraction)

func reveal() -> void:
	get_nodes_in_group("dialogic_dialog_text")[0].finish_text()
	await create_timer(.15).timeout

func _run() -> void:
	dialogic = root.get_node("Dialogic")
	var host := Node.new()
	root.add_child(host)
	# Simulate saving an edited Text event through Dialogic's own resource saver.
	# A disposable copy proves authoring works without touching the real speeches.
	var opening: Node = load("res://_testes/cenario_ilha/intro/island_intro.gd").new()
	var source: DialogicTimeline = opening.get("kai_dialogue")
	check(opening.get("waking_dialogue") is DialogicTimeline and source != null,"Opening must expose native editable Dialogic timelines")
	var original_text: String = source.as_text()
	var edited := source.duplicate(true) as DialogicTimeline
	edited.from_text("kai: Teste de edição no Dialogic.\n[end_timeline]")
	edited.set_meta("timeline_not_saved",true)
	var test_path := "user://dialogic_edit_check_%d.dtl" % Time.get_ticks_usec()
	check(ResourceSaver.save(edited,test_path) == OK,"Dialogic must save an edited timeline")
	var saved := ResourceLoader.load(test_path,"",ResourceLoader.CACHE_MODE_IGNORE) as DialogicTimeline
	check(saved != null,"The saved timeline must reload as a Dialogic resource")
	dialogic.Styles.load_style("res://dialogo/estilos/island_banner_style.tres",host)
	dialogic.start(saved)
	await settle()
	await reveal()
	var edited_text: Node = get_nodes_in_group("dialogic_dialog_text")[0]
	check(edited_text.get_parsed_text() == "Teste de edição no Dialogic.","Saved Dialogic speech edits must appear in the existing bubble")
	check(source.as_text() == original_text,"The real speeches must remain unchanged")
	dialogic.end_timeline(true)
	await settle()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(test_path))
	opening.free()
	print("DIALOGIC_EDIT_SAVE_RELOAD_AND_CUSTOM_STYLE_OK")
	dialogic.Styles.load_style("res://dialogo/estilos/island_banner_style.tres",host)
	dialogic.signal_event.connect(func(value: Variant): cue = str(value))
	dialogic.start("res://dialogo/linha_do_tempo/kai_encontro.dtl")
	await settle()
	await reveal()
	await create_timer(3.3).timeout
	check(cue == "kai_when","Dialogue must wait after the old automatic timeout")
	var banner: Node = get_nodes_in_group("dialogic_dialog_text")[0].get_parent().get_parent()
	check(banner.panel.find_children("*","Button",true,false).is_empty(),"The continue button should be replaced by a passive sign")
	check(banner.advance_prompt.size.x >= 40 and banner.advance_prompt.size.x <= 60,"A corner sign should be larger while staying a passive badge")
	var badge_rect: Rect2 = banner.advance_prompt.get_rect()
	check(badge_rect.position.y < banner.panel.size.y and badge_rect.end.y > banner.panel.size.y,"A must overlap the speech panel's lower edge")
	check(banner.advance_prompt.texture.get_width() >= 512 and banner.advance_prompt.texture.get_image().has_mipmaps(),"A should use a high-resolution mipmapped vector import")
	var pointer := InputEventMouseMotion.new()
	pointer.position = screen_position(Vector2(.4,.6))
	Input.parse_input_event(pointer)
	var click := InputEventMouseButton.new()
	click.position = pointer.position
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	Input.parse_input_event(click)
	await process_frame
	click.pressed = false
	Input.parse_input_event(click)
	await settle()
	check(cue == "kai_epoch","A click outside the speech panel must advance exactly one line")
	await reveal()
	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.position = screen_position(Vector2(.7,.6))
	touch.pressed = true
	Input.parse_input_event(touch)
	await process_frame
	touch.pressed = false
	Input.parse_input_event(touch)
	await settle()
	check(cue == "yara_console","A tap outside the speech panel must advance exactly one line")
	await reveal()
	var accept := InputEventJoypadButton.new()
	accept.button_index = JOY_BUTTON_A
	accept.pressed = true
	Input.parse_input_event(accept)
	await process_frame
	accept.pressed = false
	Input.parse_input_event(accept)
	await settle()
	check(cue == "kai_correct","Controller A must advance the dialogue")
	await reveal()
	# Like the opening's skip button, this UI sits below the speech layer.
	# Its tap must be consumed by GUI rather than also advancing the line.
	var ui_layer := CanvasLayer.new()
	ui_layer.layer = 50
	host.add_child(ui_layer)
	var skip := Button.new()
	skip.text = "Skip"
	skip.position = root.get_visible_rect().size*Vector2(.3,.8)
	skip.size = Vector2(220,48)
	skip.pressed.connect(func(): gui_clicks += 1)
	ui_layer.add_child(skip)
	await settle()
	touch.position = root.get_final_transform()*skip.get_global_rect().get_center()
	touch.pressed = true
	Input.parse_input_event(touch)
	await process_frame
	touch.pressed = false
	Input.parse_input_event(touch)
	await settle()
	check(gui_clicks == 1 and cue == "kai_correct","Tapping skip/pause UI must not also advance dialogue")
	dialogic.end_timeline(true)
	host.queue_free()
	await settle()
	print("DIALOGUE_NATIVE_MOUSE_TOUCH_GAMEPAD ","PASS" if failures == 0 else "FAIL"," failures=",failures)
	quit(0 if failures == 0 else 1)
