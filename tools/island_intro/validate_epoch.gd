extends SceneTree
var failures := 0

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func check(value: bool,message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	var course: Node3D = island.get_node("ParkourFlutuante")
	course.set_physics_process(false)
	for frame in 8: await process_frame
	var hud: Control = player.gear_container.comic_hud
	var card: PanelContainer = hud.epoch_presentation
	check(not card.visible,"The era must remain hidden while exploring the island")
	course._register_landing(0)
	for frame in 45: await process_frame
	check(card.visible and card.modulate.a>.99,"First parkour landing should introduce the era")
	check(card.description.get_line_count()==3,"The description should occupy exactly three lines")
	check(card.get_global_rect().encloses(card.description.get_global_rect()),"Description must fit its panel")
	check(not card.get_global_rect().intersects(hud.objective_panel.get_global_rect()),"Era panel must leave the mission readable")
	check(player.can_move,"The introduction must not lock movement")
	check(card.mouse_filter==Control.MOUSE_FILTER_IGNORE,"The era panel must not intercept game input")
	paused = true
	var alpha := card.modulate.a
	var elapsed: float = card.animation.get_total_elapsed_time()
	for frame in 60: await process_frame
	check(card.modulate.a==alpha and is_equal_approx(card.animation.get_total_elapsed_time(),elapsed),"Reading time must freeze when paused")
	paused = false
	card.animation.custom_step(20.0)
	check(not card.visible,"Era panel must fade and dismiss itself")
	course._last_landed = -1
	course._register_landing(0)
	course._register_landing(1)
	check(card.presentations==1 and not card.visible,"Retrying and progressing must not repeat the presentation")
	check(hud.location_label.text=="PLEISTOCENO","Parkour should reveal Pleistocene in the HUD")
	print("PLEISTOCENE_PRESENTATION ","PASS" if failures==0 else "FAIL"," failures=",failures)
	island.queue_free()
	await process_frame
	quit(0 if failures==0 else 1)
