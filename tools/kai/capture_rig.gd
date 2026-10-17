extends SceneTree
var failures := 0

func _initialize() -> void:
	root.hide()
	call_deferred("_run")

func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(900,900)
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var studio := Node3D.new()
	viewport.add_child(studio)
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(.13,.14,.15)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.WHITE
	env.ambient_light_energy = .65
	world.environment = env
	studio.add_child(world)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-40,-30,0)
	key.light_energy = 1.15
	studio.add_child(key)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 1.85
	studio.add_child(camera)
	camera.position = Vector3(1.5,1.3,3.8)
	camera.look_at(Vector3(0,.72,.08))
	camera.current = true
	var actor := load("res://assets/characters/kai/KaiActor.tscn").instantiate() as Node3D
	studio.add_child(actor)
	actor.position.y = .012 # Same ground clearance used by the island actor.
	var animator: AnimationPlayer = actor.animator
	var skeleton: Skeleton3D = actor.skeleton
	if skeleton == null or animator == null:
		quit(1)
		return
	assert(skeleton.get_bone_count()==60,"Kai must retain the compatible 60-bone rig")
	var skin := actor.find_child("Kai_Skin",true,false) as MeshInstance3D
	print("KAI_SKIN ",skin," clips=",animator.get_animation_list())
	for surface in skin.mesh.get_surface_count():
		var arrays := skin.mesh.surface_get_arrays(surface)
		var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
		for v in weights.size()/4:
			var total := weights[v*4]+weights[v*4+1]+weights[v*4+2]+weights[v*4+3]
			assert(absf(total-1)<.002,"Unnormalized runtime skin")
	var folder := "res://art/kai/previews/rig"
	DirAccess.make_dir_recursive_absolute(folder)
	var ground_samples := {}
	var rest_vertices: PackedVector3Array = skin.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var sole_vertices := PackedInt32Array()
	for i in rest_vertices.size():
		if rest_vertices[i].y<.03: sole_vertices.append(i)
	assert(skin.mesh.get_blend_shape_count()==17,"Kai needs all seventeen authored facial shapes")
	for clip in ["Idle","Walk","Run","Jump","Fall","VictorySign","Talk","Explain","Correct","Shrug","Point","React"]:
		assert(animator.has_animation(clip),"Missing Kai animation: "+clip)
		var animation := animator.get_animation(clip)
		for fraction in [0.0,.25,.5,.75,1.0]:
			animator.play(clip,0)
			animator.seek(animation.length*fraction,true)
			animator.pause()
			await process_frame
			for bone in skeleton.get_bone_count():
				var at := skeleton.get_bone_global_pose(bone).origin
				assert(at.is_finite() and at.length()<3,"Unbounded Kai deformation: "+clip)
			if clip not in ["Jump","Fall","VictorySign"]:
				await RenderingServer.frame_post_draw
				var posed := skin.bake_mesh_from_current_skeleton_pose()
				var points: PackedVector3Array = posed.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
				var lowest := INF
				for i in sole_vertices: lowest = minf(lowest,(skin.global_transform*points[i]).y)
				if not ground_samples.has(clip): ground_samples[clip] = []
				ground_samples[clip].append(lowest)
				assert(lowest>-.003,"Foot penetrates the support plane: "+clip+" "+str(fraction)+" "+str(lowest))
		animator.play(clip,0)
		animator.seek(animation.length*.45,true)
		animator.pause()
		await process_frame
		await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png(folder+"/"+clip+".png")
		print("KAI_MOTION_OK ",clip)
	animator.play("Idle",0)
	animator.seek(0,true)
	animator.pause()
	camera.size = .65
	camera.position = Vector3(.6,1.18,3.4)
	camera.look_at(Vector3(0,1.04,.08))
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(folder+"/Face.png")
	# Side views expose ankle penetration and elbow folds hidden by a front view.
	for clip in ["Walk","Run","Jump","Explain","Correct"]:
		for fraction in [.2,.45,.7,.9]:
			animator.play(clip,0)
			animator.seek(animator.get_animation(clip).length*fraction,true)
			animator.pause()
			camera.size = 1.0 if clip in ["Explain","Correct"] else .95
			camera.position = Vector3(-3.2,.75,1.4) if clip in ["Explain","Correct"] else Vector3(-3,.35,.7)
			camera.look_at(Vector3(-.08,.61,0) if clip in ["Explain","Correct"] else Vector3(0,.25,0))
			await process_frame
			await RenderingServer.frame_post_draw
			viewport.get_texture().get_image().save_png(folder+"/Joint_"+clip+"_%02d.png"%int(fraction*100))
	print("KAI_RUNTIME PASS weights normalized; 60 bones; 12 clips sampled")
	FileAccess.open("res://art/kai/runtime_motion_validation.json",FileAccess.WRITE).store_string(JSON.stringify({"engine":Engine.get_version_info().string,"renderer":"Vulkan Forward+","bones":skeleton.get_bone_count(),"facial_shapes":skin.mesh.get_blend_shape_count(),"clips":animator.get_animation_list(),"normalized_four_influence_weights":true,"five_pose_samples_per_clip":true,"lowest_sole_y_m":ground_samples,"issues":[]},"\t"))
	quit()
