extends SceneTree
const Pose = preload("res://_testes/cenario_ilha/intro/waking_pose.gd")
var viewport: SubViewport

func _initialize() -> void:
	root.hide()
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func _run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(1200,900)
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	viewport.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	player.get_node("HUD").hide()
	var pose := Pose.new()
	island.add_child(pose)
	pose.configure(player.gobot)
	var camera := Camera3D.new()
	island.add_child(camera)
	camera.current = true
	camera.fov = 35
	camera.look_at_from_position(player.global_position+Vector3(-.22,.78,-1.6),player.global_position+Vector3(0,.59,0))
	for sample in [["open",0.0],["half",.5],["closed",1.0]]:
		pose.blink = sample[1]
		for frame in 12: await process_frame
		await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png("res://art/island_intro/previews/blink_"+sample[0]+".png")
	print("EYELID_CAPTURE_OK")
	island.queue_free()
	await process_frame
	viewport.queue_free()
	await process_frame
	quit()
