extends SceneTree
var viewport: SubViewport
var island: Node3D
var player: CharacterBody3D
var course: Node3D
var quiz: Node3D
var failures := 0
var layouts: Array = []
const DEST := "res://art/island_intro/previews/quiz/"

func _initialize() -> void:
	root.hide()
	set_meta("skip_island_intro",true)
	set_meta("skip_island_ending",true)
	call_deferred("_run")

func frames(count := 10) -> void:
	for frame in count: await process_frame

func capture(name: String) -> void:
	if name.begins_with("question"):
		if quiz.bubble.position.y > viewport.size.y*.2:
			failures += 1
			push_error("Question must stay at the top on mobile: "+name)
		player.gear_container.comic_hud.notify_checkpoint("PONTO DE RETORNO ATIVADO")
	await frames()
	if name.begins_with("question"): await create_timer(.7).timeout
	if name == "answer_chosen_clear_route": await create_timer(.7).timeout
	if name.begins_with("question"):
		var rectangles: Array[Rect2] = []
		var camera: Camera3D = player.camera
		for sign in quiz.signs[quiz.current_question].get_children():
			var center: Vector3 = sign.global_position
			var a := camera.unproject_position(center-camera.global_basis.x*2.175+camera.global_basis.y*.76)
			var b := camera.unproject_position(center+camera.global_basis.x*2.175-camera.global_basis.y*.76)
			var bounds := Rect2(a,b-a).abs()
			rectangles.append(bounds)
			if not Rect2(Vector2.ZERO,Vector2(viewport.size)).encloses(bounds) or bounds.intersects(quiz.bubble.get_global_rect()):
				failures += 1
				push_error("Question/answer plate overlap or clipping: "+name)
		var hud: Control = player.gear_container.comic_hud
		if quiz.bubble.get_global_rect().intersects(hud.pause_button.get_global_rect()):
			failures += 1
			push_error("Question covers pause: "+name)
		if quiz.bubble.get_global_rect().intersects(hud.checkpoint_notification.get_global_rect()):
			failures += 1
			push_error("Checkpoint notice covers question: "+name)
		layouts.append({"capture":name,"plates_visible":rectangles.size(),"viewport":[viewport.size.x,viewport.size.y]})
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(DEST+name+".png")
	print("QUIZ_CAPTURE ",name)

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(DEST)
	viewport = SubViewport.new()
	viewport.size = Vector2i(1440,900)
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	viewport.add_child(island)
	player = island.get_node("Player")
	player.set_physics_process(false)
	player.control_preset = 0
	course = island.get_node("ParkourFlutuante")
	course.cycle_enabled = false
	quiz = course.quiz
	await frames(20)
	# Review every actual placed heart against surrounding scenery.
	player.get_node("HUD").hide()
	var review_camera := Camera3D.new()
	island.add_child(review_camera)
	review_camera.fov = 52
	print("HEART_REVIEW_OBSTACLE_BOUNDS ",island.get_node("GoldenHearts")._obstacle_bounds.size())
	for heart in get_nodes_in_group("golden_hearts"):
		for sector in 12:
			var angle := TAU*(sector+3)/12
			var candidate: Vector3 = heart.global_position+Vector3(cos(angle)*3.5,1.7,sin(angle)*3.5)
			var clear := true
			for bounds in island.get_node("GoldenHearts")._obstacle_bounds:
				if bounds.grow(.15).has_point(candidate): clear = false
			if not clear: continue
			for offset in [Vector3.ZERO,Vector3(.65,0,0),Vector3(-.65,0,0),Vector3(0,.65,0),Vector3(0,-.65,0),Vector3(0,0,.65),Vector3(0,0,-.65)]:
				var query := PhysicsRayQueryParameters3D.create(candidate,heart.global_position+offset,1,[player.get_rid()])
				query.hit_back_faces = true
				var hit := island.get_world_3d().direct_space_state.intersect_ray(query)
				if not hit.is_empty(): clear = false
			if not clear: continue
			review_camera.global_position = candidate
			review_camera.look_at(heart.global_position)
			print("HEART_REVIEW_CAMERA ",heart.name," sector=",sector+3)
			break
		review_camera.make_current()
		await capture("heart_"+str(heart.name)+"_clearance")
	review_camera.queue_free()
	player.camera.make_current()
	player.get_node("HUD").show()
	for index in 4:
		var data: Dictionary = quiz.questions[index]
		var question: Node3D = course.get_platforms()[int(data.question_platform)]
		player.global_position = question.surface_position()+Vector3.UP*.08
		player.reset_physics_interpolation()
		player.camera_pivo.rotation = Vector3(deg_to_rad(-18),question.rotation.y,0)
		player.gobot.rotation.y = question.rotation.y+PI
		quiz.on_landing(int(data.question_platform))
		await capture("question_%d" % (index+1))
		if index == 0:
			for dimensions in [Vector2i(844,390),Vector2i(640,360),Vector2i(390,844)]:
				player.control_preset = 2
				viewport.size = dimensions
				await capture("question_mobile_%dx%d" % [dimensions.x,dimensions.y])
			viewport.size = Vector2i(1440,900)
			player.control_preset = 0
		quiz.on_landing(int(data.answer_platform))
		if index == 0:
			player.global_position = course.get_platforms()[int(data.answer_platform)].surface_position()+Vector3.UP*.08
			await capture("answer_chosen_clear_route")
		course.apply_cycle_time(0)
	# Show the native Dialogic hint with the same camera/actor code as play.
	quiz.solved[0] = false
	quiz.current_question = 0
	var checkpoint: Node3D = course.get_platforms()[3]
	player.global_position = checkpoint.surface_position()+Vector3.UP*.08
	player.camera_pivo.rotation = Vector3(deg_to_rad(-18),checkpoint.rotation.y,0)
	player.health = 2
	player._update_life_hud()
	quiz._begin_hint.call_deferred(0)
	await create_timer(1.5).timeout
	for text in get_nodes_in_group("dialogic_dialog_text"): text.finish_text()
	await capture("kai_hint")
	root.get_node("Dialogic").end_timeline(true)
	await frames()
	island.queue_free()
	await frames()
	# Isolated native mesh review: original geometry, no external generator.
	var heart := preload("res://assets/props/golden_heart/GoldenHeart.tscn").instantiate()
	viewport.add_child(heart)
	heart.set_process(false)
	heart.visual.rotation.y = -.25
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-35,-35,0)
	light.light_energy = 1.7
	viewport.add_child(light)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color("1a002c")
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color("ffe2b8")
	environment.environment.ambient_light_energy = .5
	viewport.add_child(environment)
	var camera := Camera3D.new()
	viewport.add_child(camera)
	camera.position = Vector3(0,.1,2.3)
	camera.look_at(Vector3(0,-.07,0))
	camera.fov = 36
	camera.make_current()
	viewport.size = Vector2i(640,640)
	await capture("golden_heart")
	viewport.queue_free()
	await frames(2)
	FileAccess.open("res://art/island_intro/quiz_layout_validation.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"layouts":layouts},"\t"))
	print("QUIZ_CAPTURE_COMPLETE")
	quit(0 if failures == 0 else 1)
