extends SceneTree
func _initialize() -> void:
	root.hide()
	call_deferred("_run")

func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(800,800)
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
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-35,-20,0)
	light.light_energy = 1.0
	studio.add_child(light)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = .60
	studio.add_child(camera)
	camera.position = Vector3(.20,1.12,3)
	camera.look_at(Vector3(0,1.04,.05))
	camera.current = true
	DirAccess.make_dir_recursive_absolute("res://art/island_intro/previews/expressions")
	for character in ["Kai","Yara"]:
		var actor := load("res://assets/characters/kai/KaiActor.tscn" if character=="Kai" else "res://assets/characters/yara/YaraSkin.tscn").instantiate() as Node3D
		if character=="Yara": actor.scale = Vector3.ONE*1.25
		studio.add_child(actor)
		var animator: AnimationPlayer = actor.find_child("AnimationPlayer",true,false)
		animator.play("Idle",0)
		animator.seek(0,true)
		animator.pause()
		var face: Node
		if character=="Kai": face = actor.face
		else:
			face = preload("res://assets/characters/FacialAnimator.gd").new()
			actor.add_child(face)
			face.configure(actor,load("res://assets/characters/yara/yara_expressions.res"))
		face.set_process(false)
		for sample in [{"name":"Neutral","shapes":{}},{"name":"TalkA","shapes":{"MouthOpen":1.0}},{"name":"TalkO","shapes":{"MouthRound":1.0}},{"name":"Amused","shapes":{"Grin":.95,"CheekRaise":.25,"BrowAsym":.8}},{"name":"Surprised","shapes":{"EyesWide":1.0,"BrowUp":1.0,"MouthOpen":.9}},{"name":"Confused","shapes":{"Concern":.7,"BrowAsym":1.0,"Squint":.4}},{"name":"TalkE","shapes":{"VisemeWide":1.0}},{"name":"TalkU","shapes":{"VisemeU":1.0}},{"name":"Closed","shapes":{"LipPress":1.0}},{"name":"Bite","shapes":{"LipBite":1.0}},{"name":"Sad","shapes":{"Sad":1.0,"Concern":.4}},{"name":"Smile","shapes":{"Smile":1.0,"CheekRaise":.6}}]:
			for i in face.skin.mesh.get_blend_shape_count(): face.skin.set_blend_shape_value(i,0)
			for shape in sample.shapes:
				face.skin.set_blend_shape_value(face.skin.find_blend_shape_by_name(shape),sample.shapes[shape])
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			viewport.get_texture().get_image().save_png("res://art/island_intro/previews/expressions/"+character+"_"+sample.name+".png")
		camera.position = Vector3(1.8,1.12,2.2)
		camera.look_at(Vector3(0,1.04,.05))
		for sample in [{"name":"Neutral_ThreeQuarter","shapes":{}},{"name":"TalkA_ThreeQuarter","shapes":{"MouthOpen":1.0}},{"name":"Amused_ThreeQuarter","shapes":{"Grin":.85,"CheekRaise":.4,"BrowAsym":.7}}]:
			for i in face.skin.mesh.get_blend_shape_count(): face.skin.set_blend_shape_value(i,0)
			for shape in sample.shapes: face.skin.set_blend_shape_value(face.skin.find_blend_shape_by_name(shape),sample.shapes[shape])
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			viewport.get_texture().get_image().save_png("res://art/island_intro/previews/expressions/"+character+"_"+sample.name+".png")
		camera.position = Vector3(.20,1.12,3)
		camera.look_at(Vector3(0,1.04,.05))
		for sample in [{"name":"Blink","shapes":{"Blink":1.0}},{"name":"Squint","shapes":{"Squint":.8}}]:
			for i in face.skin.mesh.get_blend_shape_count(): face.skin.set_blend_shape_value(i,0)
			for shape in sample.shapes: face.skin.set_blend_shape_value(face.skin.find_blend_shape_by_name(shape),sample.shapes[shape])
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			viewport.get_texture().get_image().save_png("res://art/island_intro/previews/expressions/"+character+"_"+sample.name+".png")
		actor.queue_free()
		await process_frame
	print("FACIAL_GPU_CAPTURE_COMPLETE")
	quit()
