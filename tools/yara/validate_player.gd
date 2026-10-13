extends SceneTree

var failures: Array[String] = []
var report: Dictionary = {"states": [], "checks": []}

func _initialize() -> void:
	call_deferred("_run")


func check(condition: bool, message: String) -> bool:
	report["checks"].append({"check": message, "passed": condition})
	if not condition:
		failures.append(message)
		printerr("YARA_CHECK_FAILED: ", message)
	return condition


func wait_ticks(count: int) -> void:
	for tick in count:
		await physics_frame


func _run() -> void:
	var packed := load("res://_testes/cenario_ilha/YaraPlayer.tscn") as PackedScene
	if not check(packed != null, "Yara player loads"):
		quit(1)
		return
	var test_space := Node3D.new()
	root.add_child(test_space)
	var ground := StaticBody3D.new()
	var collision := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(30, 0.2, 30)
	collision.shape = box
	ground.position.y = -0.1
	ground.add_child(collision)
	test_space.add_child(ground)
	var player: CharacterBody3D = packed.instantiate()
	player.position = Vector3(0, 2, 0)
	test_space.add_child(player)
	player.set("control_preset", 0)
	var animator := player.get_node_or_null("gobot/AnimationPlayer") as AnimationPlayer
	if not check(animator != null, "Existing AnimationPlayer path works"):
		quit(1)
		return
	for clip in ["Idle", "Walk", "Run", "Jump", "Fall", "Flip", "VictorySign", "EdgeGrab", "WallSlide"]:
		check(animator.has_animation(clip), "Clip " + clip)
	for clip in ["Idle", "Walk", "Run"]:
		check(animator.get_animation(clip).loop_mode == Animation.LOOP_LINEAR, "Loop " + clip)
	var skeleton := player.get_node("gobot").find_child("Skeleton3D", true, false) as Skeleton3D
	check(skeleton != null and skeleton.get_bone_count() >= 57, "Deform skeleton and volume helpers imported")
	await wait_ticks(90)
	check(player.is_on_floor(), "Player lands on existing collider")
	check(animator.current_animation == "Idle", "Standing selects Idle")
	var start := player.position
	# Exercise the controller's existing optional sprint branch without editing InputMap.
	if not InputMap.has_action("sprint"):
		InputMap.add_action("sprint")
		report["test_only_sprint_binding"] = true
	Input.action_press("ui_up")
	await wait_ticks(20)
	check(animator.current_animation == "Walk", "Movement selects Walk")
	check(player.position.distance_to(start) > 0.3, "Existing movement controls move Yara")
	Input.action_press("sprint")
	await wait_ticks(15)
	check(animator.current_animation == "Run", "Sprint selects Run")
	Input.action_release("sprint")
	Input.action_release("ui_up")
	await wait_ticks(25)
	check(animator.current_animation == "Idle", "Stopping returns to Idle")
	await process_frame
	var jump_event := InputEventAction.new()
	jump_event.action = "ui_accept"
	jump_event.pressed = true
	Input.parse_input_event(jump_event)
	await wait_ticks(3)
	jump_event.pressed = false
	Input.parse_input_event(jump_event)
	report["jump_velocity_sample"] = player.velocity.y
	check(player.velocity.y > 0 and animator.current_animation == "Jump", "Jump input selects airborne Jump")
	var falling := false
	for tick in 110:
		await physics_frame
		falling = falling or animator.current_animation == "Fall"
	check(falling, "Descent selects Fall")
	check(player.is_on_floor() and animator.current_animation == "Idle", "Landing returns to Idle")
	var island := load("res://_testes/cenario_ilha/CenarioIlha.tscn") as PackedScene
	check(island != null, "Island loads with Yara")
	var scene := island.instantiate()
	var island_player := scene.get_node("Player")
	check(island_player.scene_file_path == "res://_testes/cenario_ilha/YaraPlayer.tscn", "Island replaces only player visual prefab")
	check(island_player.get("walk_speed") == 6.5 and island_player.get("run_speed") == 2.0 and island_player.get("jump_velocity") == 5.0, "Island movement tuning preserved")
	scene.free()
	report["issues"] = failures
	var file := FileAccess.open("res://art/yara/validation/godot_validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	print("YARA_PLAYER_VALIDATION ", JSON.stringify(report))
	test_space.queue_free()
	quit(0 if failures.is_empty() else 1)
