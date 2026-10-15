extends SceneTree
var player: CharacterBody3D
var failures := 0

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	player = island.get_node("Player")
	player.set_physics_process(false)
	player.control_preset = 0
	var course: Node3D = island.get_node("ParkourFlutuante")
	course.cycle_enabled = false
	var trail := island.get_node("Topazios").get_children()
	var goals: Array[Vector3] = []
	for crystal: Area3D in trail:
		if str(crystal.name).begins_with("Trilha") or crystal.name == "TopazioPlataforma01":
			goals.append(crystal.global_position-Vector3.UP*.85)
	for frame in 20: await step(Vector3.ZERO)
	var passed := 0
	for target: Vector3 in goals:
		var reached := false
		var peak := player.global_position.y
		var jumps := 0
		for frame in 240:
			var delta := target-player.global_position
			var horizontal := Vector3(delta.x,0,delta.z)
			if horizontal.length()<.38 and absf(delta.y)<.25 and player.is_on_floor():
				reached = true
				break
			var jump := player.is_on_floor() and delta.y>.25 and horizontal.length()<4.0
			await step(horizontal.normalized() if horizontal.length()>.06 else Vector3.ZERO,jump)
			peak = maxf(peak,player.global_position.y)
			if player.is_jumping: jumps += 1
		if not reached:
			failures += 1
			for collision_index in player.get_slide_collision_count():
				var collision := player.get_slide_collision(collision_index)
				print("TRAIL_OBSTACLE ",collision.get_collider().get_path()," normal=",collision.get_normal())
			push_error("Trail blocked at %d player=%s target=%s health=%d peak=%.3f jumps=%d" % [passed+1,player.global_position,target,player.health,peak,jumps])
			break
		passed += 1
		print("WALK_GUIDE_POINT_OK ",passed," ",player.global_position)
	for action in ["ui_left","ui_right","ui_up","ui_down","ui_accept"]: Input.action_release(action)
	if passed == goals.size():
		for frame in 4: await step(Vector3.ZERO)
		if course._checkpoint_index != 0:
			failures += 1; push_error("Trail did not reach the first parkour checkpoint")
		if not "Trilha dos céus" in player.gear_container.comic_hud.objective.text:
			failures += 1; push_error("Parkour mission did not begin on arrival")
		if player.gear_container.comic_hud.location_label.text != "PLEISTOCENO":
			failures += 1; push_error("Discovering the route should reveal the island name")
	print("GUIDED_TRAIL ","PASS" if failures==0 else "FAIL"," reached=",passed,"/",goals.size()," fragments=",player.gears)
	island.queue_free()
	await process_frame
	quit(0 if failures==0 else 1)

func step(direction: Vector3,jump: bool = false) -> void:
	await physics_frame
	player.camera_pivo.rotation = Vector3(deg_to_rad(-18),0,0)
	var input := Vector2(direction.x,direction.z)
	for pair in [["ui_right",maxf(input.x,0)],["ui_left",maxf(-input.x,0)],["ui_down",maxf(input.y,0)],["ui_up",maxf(-input.y,0)]]:
		if pair[1]>.001: Input.action_press(pair[0],pair[1])
		else: Input.action_release(pair[0])
	if jump:
		var event := InputEventAction.new()
		event.action = "ui_accept"
		event.pressed = true
		Input.parse_input_event(event)
	player._physics_process(1.0/60.0)
	Input.action_release("ui_accept")
