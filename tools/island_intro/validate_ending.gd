extends SceneTree
var failures := 0
var island: Node3D
var ending: Node3D
var player: CharacterBody3D
var stages: Array[String] = []
var progress_bytes := PackedByteArray()
var progress_existed := false
var original_flags: Array = []
var save_path := "user://progresso.cfg"
var stage_times := {}
var pickup_hud_visible := false

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	set_meta("ending_duration_scale",.08)
	call_deferred("_run")

func check(value: bool,message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func frames(count := 5) -> void:
	for frame in count: await process_frame

func load_island() -> void:
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	current_scene = island
	player = island.get_node("Player")
	player.set_physics_process(false)
	island.get_node("ParkourFlutuante").set_physics_process(false)
	ending = island.get_node("Ending")
	ending.stage_changed.connect(func(value: String):
		stages.append(value)
		stage_times[value] = Time.get_ticks_msec()
		if value == "pickup_settle": pickup_hud_visible = player.get_node("HUD").visible)
	await frames()

func collect_all() -> void:
	for pickup in island.get_node("Topazios").get_children(): pickup._on_body_entered(player)
	await frames()

func _run() -> void:
	var progress: Node = root.get_node("FaseCore")
	progress_existed = FileAccess.file_exists(save_path)
	if progress_existed: progress_bytes = FileAccess.get_file_as_bytes(save_path)
	original_flags = [progress.fase1_concluida,progress.fase2_concluida,progress.fase3_concluida]
	await load_island()
	check(not ending.started,"Ending must not run before the goal")
	var pickups := island.get_node("Topazios").get_children()
	for pickup in pickups.slice(0,30): pickup._on_body_entered(player)
	await frames()
	check(player.gears == 30 and not ending.started,"Thirty fragments must not trigger the finale")
	pickups[30]._on_body_entered(player)
	await frames()
	check(ending.active and ending.start_count == 1,"The final real pickup must trigger one finale")
	check(not player.can_move and not player.is_physics_processing(),"Ending must lock player movement")
	check(pickup_hud_visible,"The completed HUD must remain visible while the last pickup registers")
	check(not player.mobile_controls.visible and player.mobile_controls.movement.is_zero_approx(),"Ending must hide movement controls and clear touches")
	check(progress.fase1_concluida,"Finishing all fragments must mark phase one complete")
	var saved := ConfigFile.new()
	check(saved.load(save_path) == OK and saved.get_value("fases","fase_1_concluida",false),"Phase completion must be saved")
	var checked_pause := false
	var checked_pickup_pause := false
	var deadline := Time.get_ticks_msec()+45000
	var next_input := 0
	while Time.get_ticks_msec()<deadline and not ending.completed:
		await process_frame
		if ending.stage == "pickup_hold" and not checked_pickup_pause:
			checked_pickup_pause = true
			var clock: float = ending._clock
			var transform: Transform3D = ending.camera.global_transform
			var manager: Node = root.get_node("BotaoGlobal")
			manager.toggle_pause()
			await frames(12)
			check(ending.stage == "pickup_hold" and ending._clock == clock and ending.camera.global_transform.is_equal_approx(transform),"Pause must freeze the pickup hold before the dissolve")
			check(player.get_node("HUD").visible,"The completed HUD must stay visible during the paused pickup hold")
			manager.toggle_pause()
		if ending.stage == "end_portal" and not checked_pause:
			checked_pause = true
			await frames()
			var space := island.get_world_3d().direct_space_state
			for actor in [player,ending.kai]:
				var ground := space.intersect_ray(PhysicsRayQueryParameters3D.create(actor.global_position+Vector3.UP,actor.global_position-Vector3.UP*2,1,[player.get_rid()]))
				check(not ground.is_empty(),"Both ending actors need solid ground")
				if not ground.is_empty(): check(actor.global_position.y-ground.position.y >= 0 and actor.global_position.y-ground.position.y < .15,"Ending actors must stand on the clearing")
			var obstruction := space.intersect_ray(PhysicsRayQueryParameters3D.create(ending.camera.global_position,ending.portal.global_position,1,[player.get_rid()]))
			check(obstruction.is_empty(),"Vegetation must not block the portal shot")
			var clock: float = ending._clock
			var transform: Transform3D = ending.camera.global_transform
			var manager: Node = root.get_node("BotaoGlobal")
			manager.toggle_pause()
			await frames(12)
			check(ending._clock == clock and ending.camera.global_transform.is_equal_approx(transform),"Pause must freeze portal and camera")
			manager.toggle_pause()
		if Time.get_ticks_msec()>next_input and root.get_node("Dialogic").current_timeline != null:
			root.get_node("Dialogic").Inputs.handle_input()
			next_input = Time.get_ticks_msec()+300
	check(ending.completed,"Finale did not reach completion")
	check(checked_pause,"Portal pause check did not run")
	check(checked_pickup_pause,"Pickup handoff pause check did not run")
	for expected in ["pickup_settle","pickup_hold","fragments_gather","transition_out","return_to_clearing","end_found","end_portal","end_luggage","end_joke","end_thanks","end_remember","end_goodbye","end_home","walk_home","complete"]:
		check(expected in stages,"Missing ending stage: "+expected)
	check(stage_times.get("transition_out",0)-stage_times.get("pickup_hold",0) >= 3.0*.08*1000,"The last pickup needs a readable hold before the dissolve")
	check(stage_times.get("end_found",0)-stage_times.get("return_to_clearing",0) >= 2.0*.08*1000,"The clearing needs a gradual reveal and a beat before speech")
	check(is_instance_valid(ending.portal) and ending.portal.visible,"Ending must build and reveal the portal")
	check(ending.yara_face.mouth_peak > .15 and ending.kai.face.mouth_peak > .15,"Both characters must articulate ending dialogue")
	check(ending.yara_face.expression_changes >= 8,"Ending must include facial reactions")
	check(root.get_node("Dialogic").current_timeline == null,"Completion must close Dialogic")
	var manager: Node = root.get_node("BotaoGlobal")
	check(paused and manager.level_complete and manager.pause_screen.screen == "complete","Ending must show the completion menu")
	check(manager.pause_screen.completion_fragments == 31,"Completion card must show the real goal")
	var escape := InputEventJoypadButton.new()
	escape.button_index = JOY_BUTTON_Y
	escape.pressed = true
	manager._input(escape)
	check(paused and manager.level_complete,"Y must not resume the completed level behind the card")
	ending._queue_start()
	check(ending.start_count == 1,"Repeated completion must not replay the ending")
	print("FULL_ENDING_DIALOGIC_PORTAL_PAUSE_SAVE_AND_CARD_OK")
	# The actual Replay button must reload the level with no stuck input/pause.
	manager.pause_screen.find_child("ReplayPhase",true,false).pressed.emit()
	await frames(12)
	island = current_scene
	check(island != null and island.get_node("Player").gears == 0,"Replay must reset fragment progress")
	check(not paused and manager.pause_screen == null,"Replay must close the completion menu and resume")
	if island != null:
		island.queue_free()
		await frames()
	# Skip early and during speech both lead to the same safe completion card.
	for skip_stage in ["pickup_settle","end_luggage"]:
		stages.clear()
		set_meta("ending_reduce_motion",skip_stage == "end_luggage")
		await load_island()
		if skip_stage == "pickup_settle":
			ending.stage_changed.connect(func(_value: String): ending.finish.call_deferred(),CONNECT_ONE_SHOT)
		await collect_all()
		deadline = Time.get_ticks_msec()+20000
		next_input = 0
		while Time.get_ticks_msec()<deadline and ending.stage != skip_stage and not ending.completed:
			await process_frame
			if Time.get_ticks_msec()>next_input and root.get_node("Dialogic").current_timeline != null:
				root.get_node("Dialogic").Inputs.handle_input()
				next_input = Time.get_ticks_msec()+300
		check(skip_stage in stages,"Could not reach ending skip stage: "+skip_stage)
		if skip_stage == "end_luggage": check(ending._portal_material.get_shader_parameter("phase") == 0,"Reduced motion must disable portal swirl/orbit")
		ending.finish()
		await frames()
		check(ending.completed and paused and manager.level_complete,"Skip must finish the phase")
		check(root.get_node("Dialogic").current_timeline == null,"Skipping ending speech must close the timeline")
		if skip_stage == "end_luggage":
			manager.pause_screen.find_child("ReturnHome",true,false).pressed.emit()
			deadline = Time.get_ticks_msec()+6000
			while Time.get_ticks_msec()<deadline:
				await process_frame
				if current_scene != null and current_scene.scene_file_path == "res://scenes/telaInicial/TelaInicial.tscn": break
			check(current_scene != null and current_scene.scene_file_path == "res://scenes/telaInicial/TelaInicial.tscn" and not paused,"Return Home must reach the main menu without stuck pause")
			if current_scene != null: current_scene.queue_free()
		else:
			manager.toggle_pause()
			island.queue_free()
		await frames()
	print("ENDING_EARLY_AND_SPEECH_SKIP_OK")
	var viewport := SubViewport.new()
	root.add_child(viewport)
	for dimensions in [Vector2i(844,390),Vector2i(640,360)]:
		viewport.size = dimensions
		var menu := preload("res://scenes/ui/interface.gd").new()
		menu.initial_screen = "complete"
		menu.completion_fragments = 31
		viewport.add_child(menu)
		await frames()
		var replay_rect: Rect2 = menu.first_button.get_global_rect()
		var home_rect: Rect2 = menu.find_child("ReturnHome",true,false).get_global_rect()
		check(replay_rect.size.y >= 47.9 and home_rect.size.y >= 47.9,"Mobile ending menu needs large touch targets")
		check(not replay_rect.intersects(home_rect) and Rect2(Vector2.ZERO,Vector2(dimensions)).encloses(home_rect),"Mobile ending buttons must fit and remain separate")
		menu.queue_free()
		await frames()
	viewport.queue_free()
	await frames()
	print("ENDING_MOBILE_COMPLETION_LAYOUT_OK")
	# Restore the user's real save after exercising the actual persistence path.
	if progress_existed:
		FileAccess.open(save_path,FileAccess.WRITE).store_buffer(progress_bytes)
	else:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(save_path))
	progress.fase1_concluida = original_flags[0]
	progress.fase2_concluida = original_flags[1]
	progress.fase3_concluida = original_flags[2]
	check(FileAccess.get_file_as_bytes(save_path) == progress_bytes if progress_existed else not FileAccess.file_exists(save_path),"User progress file must be restored exactly")
	var report := {"failures":failures,"fragment_goal":31,"user_save_restored":true,"timeline":"res://dialogo/linha_do_tempo/ilha_final.dtl","checks":["final real pickup only","once-only trigger","full dialogue and faces","grounded actors and clear portal","camera and portal pause","actual progress save","replay","return home","early and speech skip","reduced motion","mobile completion targets"]}
	FileAccess.open("res://art/island_intro/ending_validation.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	print("ISLAND_ENDING ","PASS" if failures == 0 else "FAIL"," failures=",failures," user_save_restored=true")
	quit(0 if failures == 0 else 1)
