extends SceneTree
func _initialize() -> void:
	root.hide()
	call_deferred("_run")

func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(64,64)
	viewport.own_world_3d = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var actor := load("res://assets/characters/kai/KaiActor.tscn").instantiate() as Node3D
	viewport.add_child(actor)
	actor.position.y = .012
	actor.face.set_process(false)
	var camera := Camera3D.new()
	viewport.add_child(camera)
	camera.position = Vector3(0,1,3)
	camera.look_at(Vector3(0,.7,0))
	camera.current = true
	var skin := actor.find_child("Kai_Skin",true,false) as MeshInstance3D
	var rest: PackedVector3Array = skin.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var sole := PackedInt32Array()
	for i in rest.size():
		if rest[i].y<.035: sole.append(i)
	var report := {}
	for clip in ["Idle","Walk","Run","Talk","Explain","Correct","Shrug","Point","React"]:
		var animation: Animation = actor.animator.get_animation(clip)
		var samples := []
		for frame in int(round(animation.length*30))+1:
			var time := minf(frame/30.0,animation.length)
			actor.animator.play(clip,0)
			actor.animator.seek(time,true)
			actor.animator.pause()
			await process_frame
			await RenderingServer.frame_post_draw
			var posed := skin.bake_mesh_from_current_skeleton_pose()
			var points: PackedVector3Array = posed.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
			var lowest := INF
			for i in sole: lowest = minf(lowest,(skin.global_transform*points[i]).y)
			samples.append({"time":time,"lowest_world_y":lowest,"delta_native":(.0145-lowest)/1.25})
		report[clip] = samples
		print("FLOOR_PROBE ",clip," frames=",samples.size())
	var verify := "--verify" in OS.get_cmdline_user_args()
	FileAccess.open("C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16/"+("floor_verified.json" if verify else "floor_probe.json"),FileAccess.WRITE).store_string(JSON.stringify(report))
	if verify:
		var maximum_error := 0.0
		var results := {}
		for clip in report:
			var low := INF
			var high := -INF
			for row in report[clip]:
				low = minf(low,row.lowest_world_y)
				high = maxf(high,row.lowest_world_y)
				maximum_error = maxf(maximum_error,absf(row.lowest_world_y-.0145))
			results[clip] = {"frames":report[clip].size(),"lowest_y_range_m":[low,high]}
		FileAccess.open("res://art/kai/ground_engine_validation.json",FileAccess.WRITE).store_string(JSON.stringify({"samples":results,"maximum_contact_error_m":maximum_error,"issues":[] if maximum_error<.003 else ["Foot support deviates from its target"]},"\t"))
		print("KAI_FOOT_SUPPORT ","PASS" if maximum_error<.003 else "FAIL"," maximum_error=",maximum_error)
		quit(0 if maximum_error<.003 else 1)
	else: quit()
