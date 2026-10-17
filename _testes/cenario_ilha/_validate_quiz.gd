extends SceneTree
var failures := 0
var island: Node3D
var player: CharacterBody3D
var course: Node3D
var quiz: Node3D
var platforms: Array[Node3D]
var hints_seen := 0
var wrong_contact_checks: Array[int] = []

func _initialize() -> void:
	root.hide()
	set_meta("skip_island_intro",true)
	set_meta("skip_island_ending",true)
	call_deferred("_run")

func check(value: bool,message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func step(direction := Vector3.ZERO,jump := false) -> void:
	await physics_frame
	player.camera_pivo.global_rotation = Vector3(deg_to_rad(-18),0,0)
	for pair in [["ui_right",maxf(direction.x,0)],["ui_left",maxf(-direction.x,0)],["ui_down",maxf(direction.z,0)],["ui_up",maxf(-direction.z,0)]]:
		if pair[1] > .001: Input.action_press(pair[0],pair[1])
		else: Input.action_release(pair[0])
	if jump:
		var event := InputEventAction.new()
		event.action = "ui_accept"
		event.pressed = true
		Input.parse_input_event(event)
	if not quiz.hint_active: player._physics_process(1.0/60)
	if quiz._falling_question >= 0 and quiz._falling_question not in wrong_contact_checks:
		wrong_contact_checks.append(quiz._falling_question)
		check(not quiz.signs[quiz._falling_question].showing,"Wrong choice must start dismissing the answer plates immediately")
	Input.action_release("ui_accept")
	await process_frame

func place(at: Vector3) -> void:
	player.global_position = at
	player.velocity = Vector3.ZERO
	player._tracking_fall = false
	player._fall_peak = at.y
	player.reset_physics_interpolation()

func settle(count := 12) -> void:
	for frame in count: await step()

func jump_to(target: Node3D,expect_floor := true) -> bool:
	var at: Vector3 = target.surface_position()
	var direction := at-player.global_position
	direction.y = 0
	direction = direction.normalized()
	await step(direction,true)
	for frame in 110:
		await step(direction)
		if quiz.hint_active or player.health < 3: return not expect_floor
		if player.is_on_floor():
			for collision_index in player.get_slide_collision_count():
				if player.get_slide_collision(collision_index).get_collider() == target: return true
			return false
	return false

func finish_hint() -> void:
	var dialogic: Node = root.get_node("Dialogic")
	for frame in 240:
		await step()
		if quiz.hint_active and dialogic.current_timeline != null:
			if frame%15 == 0: dialogic.Inputs.handle_input()
		elif quiz.hints_played > hints_seen:
			hints_seen = quiz.hints_played
			break
	check(not quiz.hint_active and dialogic.current_timeline == null,"Hint must finish and close Dialogic")
	check(player.can_move,"Hint must restore movement")
	check(quiz.bubble.visible,"Question must return after Kai's hint")
	check(quiz.signs[quiz.current_question].visible,"Answer plates must return for the retry")
	player.set_physics_process(false)

func _run() -> void:
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	current_scene = island
	player = island.get_node("Player")
	player.control_preset = 0
	player.set_physics_process(false)
	course = island.get_node("ParkourFlutuante")
	course.cycle_enabled = false
	quiz = course.quiz
	platforms = course.get_platforms()
	await settle()
	check(quiz != null and quiz.questions.size() == 4,"Expected four questions")
	var checkpoints := 0
	for platform in platforms.slice(1,20):
		if platform.checkpoint: checkpoints += 1
	check(checkpoints == 4,"Expected four intermediate checkpoints, excluding start/finish")
	var space := island.get_world_3d().direct_space_state
	for index in 4:
		var data: Dictionary = quiz.questions[index]
		var correct: Node3D = platforms[int(data.answer_platform)]
		var wrong: Node3D = quiz.wrong_platforms[index]
		check(correct.permanent and not correct.checkpoint,"The correct answer must be a safe permanent deck")
		var wrong_hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(wrong.surface_position()+Vector3.UP,wrong.surface_position()-Vector3.UP*.2,1,[player.get_rid()]))
		check(wrong_hit.is_empty(),"Wrong answer %d must have no floor" % index)
	check(not platforms.back().is_solid,"Unanswered questions must gate later platforms")
	print("QUIZ_STRUCTURE_AND_COLLISION_OK")
	# Traverse every real deck with quiz gates enabled, then reset for failures.
	place(platforms[0].surface_position()+Vector3.UP*.08)
	await settle()
	for index in range(1,platforms.size()):
		check(await jump_to(platforms[index]),"Full quiz route is unreachable at platform %d" % (index+1))
		for frame in 50:
			var adjustment: Vector3 = platforms[index].surface_position()-player.global_position
			adjustment.y = 0
			if adjustment.length() < .12: break
			await step(adjustment.normalized())
		course._update_progress()
	check(course._completed and quiz.solved.count(true) == 4,"Full route must complete all four questions before the finish")
	print("QUIZ_FULL_PHYSICAL_ROUTE_OK")
	for index in 4:
		quiz.solved[index] = false
		quiz.signs[index].hide()
	quiz.current_question = -1
	quiz.bubble.hide()
	quiz._question_layout()
	course._completed = false
	course._last_landed = -1
	course._checkpoint_index = -1
	course.apply_cycle_time(0)
	# Real Area3D overlap and duplicate callbacks: +1, capped, never fragments.
	var hearts := get_nodes_in_group("golden_hearts")
	check(hearts.size() == 5,"Expected five spaced refills instead of thirteen")
	for pickup in hearts:
		var clearance := PhysicsShapeQueryParameters3D.new()
		var envelope := SphereShape3D.new()
		envelope.radius = .72
		clearance.shape = envelope
		clearance.transform.origin = pickup.global_position
		clearance.collision_mask = 1
		clearance.exclude = [player.get_rid()]
		check(space.intersect_shape(clearance,1).is_empty(),"Heart intersects scenery: "+str(pickup.name))
	FileAccess.open("res://art/island_intro/heart_placement_validation.json",FileAccess.WRITE).store_string(JSON.stringify(island.get_node("GoldenHearts").placement_report,"\t"))
	var heart: Area3D = hearts[0]
	var mesh: ArrayMesh = heart.visual.get_child(0).mesh
	var arrays := mesh.surface_get_arrays(0)
	var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	check(indices.size()/3 <= 2000,"Reusable heart must stay within its 2,000-triangle budget")
	for triangle in range(0,indices.size(),3):
		var a := vertices[indices[triangle]]
		var b := vertices[indices[triangle+1]]
		var c := vertices[indices[triangle+2]]
		check((b-a).cross(c-a).length() > .000001,"Heart mesh must not contain degenerate triangles")
	var original_fragments: int = player.gears
	place(heart.global_position-Vector3.UP*.5)
	await settle(3)
	check(player.health == 3 and heart.taken,"Full health must still consume the heart without adding lives")
	heart = hearts[1]
	player.health = 1
	place(heart.global_position-Vector3.UP*.5)
	await settle(3)
	check(player.health == 2 and heart.taken,"One physical heart must restore exactly one life")
	heart._try_collect(player)
	check(player.health == 2,"Duplicate overlap must not heal twice")
	hearts[2]._try_collect(player)
	check(player.health == 3,"Second heart must refill the third life")
	hearts[3]._try_collect(player)
	check(player.health == 3 and hearts[3].taken,"Full-health pickups must disappear without exceeding three lives")
	check(player.gears == original_fragments,"Hearts must not count as fragments")
	print("HEART_ACTUAL_OVERLAP_CAP_AND_DUPLICATE_OK count=",hearts.size())
	for index in 4:
		var data: Dictionary = quiz.questions[index]
		var checkpoint: Node3D = platforms[int(data.checkpoint)]
		var question: Node3D = platforms[int(data.question_platform)]
		var answer: Node3D = platforms[int(data.answer_platform)]
		player.health = 3
		player.is_invulnerable = false
		place(checkpoint.surface_position()+Vector3.UP*.08)
		await settle()
		check(course._checkpoint_index == int(data.checkpoint),"Question needs the preceding saved checkpoint")
		check(quiz.current_question == index and quiz.bubble.visible,"Question must appear after the checkpoint")
		var hud: Control = course._get_hud()
		check(hud.checkpoint_notification.visible and hud.checkpoint_notification.position.y > root.size.y*.7,"Checkpoint notice must use the bottom of the screen")
		check(not hud.checkpoint_notification.get_global_rect().intersects(quiz.bubble.get_global_rect()),"Checkpoint notice must not cover the question")
		check(await jump_to(question),"Question platform jump is unreachable: %d" % index)
		place(question.surface_position()+Vector3.UP*.08)
		await settle()
		await jump_to(quiz.wrong_platforms[index],false)
		for frame in 220:
			await step()
			if quiz.hint_active: break
		check(player.health == 2 and quiz.wrong_attempts == index+1,"Wrong platform must cost exactly one life")
		check(player.global_position.distance_to(player.player_start_position) < .2,"Wrong choice must return to its checkpoint")
		check(quiz.hint_active,"Kai must give a hint after a nonfatal wrong answer")
		if quiz.hint_active:
			var clock: float = course._elapsed
			root.get_node("BotaoGlobal").toggle_pause()
			for frame in 5: await process_frame
			check(quiz.hint_active and course._elapsed == clock,"Pause must freeze the hint and course")
			root.get_node("BotaoGlobal").toggle_pause()
		await finish_hint()
		player.health = 3
		player.is_invulnerable = false
		place(question.surface_position()+Vector3.UP*.08)
		await settle()
		check(await jump_to(answer),"Correct answer jump is unreachable: %d" % index)
		await settle(2)
		check(quiz.solved[index],"Landing on the correct answer must resolve the question")
		check(not quiz.signs[index].showing,"Correct landing must start dismissing the plates immediately")
		check(not quiz.bubble.showing,"Correct answer must start dismissing the question")
		await settle(24)
		check(not quiz.signs[index].visible and not quiz.bubble.visible,"Question and plates must be fully gone after the fade")
		check(platforms[int(data.answer_platform)+1].is_solid,"Correct answer must unlock continuation")
		print("QUIZ_ACTUAL_WRONG_HINT_CORRECT_OK ",index+1)
	# Last-life wrong answer: existing game-over flow, no new dialogue.
	quiz.solved[3] = false
	quiz.current_question = 3
	course._checkpoint_index = 15
	course._last_landed = 16
	player.player_start_position = platforms[15].surface_position()+Vector3.UP*.08
	var previous_hints: int = quiz.hints_played
	player.health = 1
	player.is_invulnerable = false
	place(quiz.wrong_platforms[3].surface_position()+Vector3.UP*.05)
	for frame in 150:
		await step()
		if player.is_dead: break
	for frame in 8: await process_frame
	check(player.is_dead and player.health == 0,"Wrong last-life answer must reach game over")
	check(quiz.hints_played == previous_hints and root.get_node("Dialogic").current_timeline == null,"No hint should play after the last life")
	check(paused and root.get_node("BotaoGlobal").game_over,"Existing retry menu must appear")
	root.get_node("BotaoGlobal").toggle_pause()
	print("QUIZ_LAST_LIFE_GAME_OVER_NO_HINT_OK")
	for action in ["ui_left","ui_right","ui_up","ui_down","ui_accept"]: Input.action_release(action)
	var report := {"failures":failures,"questions":4,"intermediate_checkpoints":checkpoints,"heart_count":hearts.size(),"heart_triangles":indices.size()/3,"hints_seen":hints_seen,"wrong_platforms_have_no_collision":true,"physical_jumps":true,"full_route_traversed":true,"last_life_has_no_hint":true}
	FileAccess.open("res://art/island_intro/quiz_validation.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	island.queue_free()
	await process_frame
	print("PLEISTOCENE_QUIZ ","PASS" if failures == 0 else "FAIL"," failures=",failures)
	quit(0 if failures == 0 else 1)
