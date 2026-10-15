extends SceneTree
var failures := 0
var stages: Array[String] = []
var saw_dialogue := false
var saw_pose := false
var checked_ground_sit := false
var island: Node3D
const Intro = preload("res://_testes/cenario_ilha/intro/island_intro.gd")

func _initialize() -> void:
	set_meta("intro_duration_scale",.08)
	call_deferred("_run")

func check(value: bool,message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func load_island() -> void:
	Intro.seen_this_session = false
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	island.get_node("Opening").stage_changed.connect(func(name: String): stages.append(name))
	root.add_child(island)
	current_scene = island
	await process_frame

func _run() -> void:
	await load_island()
	var intro: Node3D = island.get_node("Opening")
	var player: CharacterBody3D = island.get_node("Player")
	check(island.get_node_or_null("TigreTemporario") == null,"The tiger must be removed from this scene")
	check(player.global_position.y < 4.2,"Player must spawn on the lowest broad island platform")
	check(not player.can_move and not player.is_physics_processing(),"Opening must lock gameplay movement")
	for frame in 1100:
		await process_frame
		if intro.stage == "seated" and is_instance_valid(intro.pose):
			saw_pose = intro.pose.seated > .9 and intro.pose._eyes.size() == 2 and intro.pose._lashes.size() == 2
			if not checked_ground_sit:
				checked_ground_sit = true
				var skeleton: Skeleton3D = intro.pose.skeleton
				var hips := bone_position(skeleton,"Hips")
				var left_foot := bone_position(skeleton,"Foot.L")
				var right_foot := bone_position(skeleton,"Foot.R")
				var left_knee := bone_position(skeleton,"LowerLeg.L")
				var right_knee := bone_position(skeleton,"LowerLeg.R")
				var ray := PhysicsRayQueryParameters3D.create(hips+Vector3.UP,hips+Vector3.DOWN,1,[player.get_rid()])
				var floor_hit := island.get_world_3d().direct_space_state.intersect_ray(ray)
				check(not floor_hit.is_empty(),"Seated pose must be supported by terrain")
				if not floor_hit.is_empty():
					check(hips.y-floor_hit.position.y > .04 and hips.y-floor_hit.position.y < .14,"Hips must rest just above the floor, rather than hover in a squat")
				check(absf(left_knee.y-hips.y)<.04 and absf(right_knee.y-hips.y)<.04,"Thighs must lie along the ground")
				check(left_foot.x<left_knee.x and right_foot.x>right_knee.x and right_foot.x-left_foot.x>.45,"Straight legs must open outward into a V")
				for side in ["L","R"]:
					var hip := bone_position(skeleton,"UpperLeg."+side)
					var knee := bone_position(skeleton,"LowerLeg."+side)
					var foot := bone_position(skeleton,"Foot."+side)
					check((knee-hip).normalized().dot((foot-knee).normalized())>.98,"Knee must remain extended in the sitting pose")
				print("GROUND_SIT_EXTENDED_V_OK")
		if intro.stage == "dialogue":
			var dialogic := root.get_node("Dialogic")
			var nodes := get_nodes_in_group("dialogic_dialog_text")
			if not nodes.is_empty() and not nodes[0].text.is_empty() and not saw_dialogue:
				saw_dialogue = "onde eu estou...?" in nodes[0].get_parsed_text()
				var viewport_size: Vector2 = nodes[0].get_viewport_rect().size
				check(nodes[0].textbox_root.size.x >= viewport_size.x*.94,"Dialogic balloon must cover the screen width")
				check(nodes[0].textbox_root.position.y < viewport_size.y*.1,"Dialogic balloon must stay at the top")
				var before_characters: int = nodes[0].visible_characters
				paused = true
				for sample in 10: await process_frame
				check(intro.stage == "dialogue" and nodes[0].visible_characters == before_characters,"Dialogue and cutscene must pause together")
				paused = false
		if not intro.active: break
	check(not intro.active and intro.stage == "finished","Opening did not finish")
	check(saw_pose,"Opening did not pose the legs and prepare both eyes for blinking")
	check(saw_dialogue,"Actual Dialogic timeline did not display the opening line")
	for stage in ["first_person_blink","seated","head_shake","dialogue","island_pan","return_closeup","handing_control_back","finished"]:
		check(stage in stages,"Missing cutscene stage: "+stage)
	check(player.can_move and player.is_physics_processing(),"Opening failed to restore movement")
	check(player.camera.current,"Opening failed to restore gameplay camera")
	check(player.get_node("HUD").visible,"Opening failed to restore HUD")
	check(player.gobot.position.is_equal_approx(intro.pose._original_position),"Standing must restore the original model height")
	for original in intro.pose._original_meshes:
		check(original.mesh.mesh==original.original,"Opening must restore the shared source mesh after blinking")
	for surface in intro.pose._eyes+intro.pose._lashes:
		check(surface.mesh.get_surface_override_material(surface.surface)==surface.original,"Opening must restore eye and eyelash materials")
	check(player.gear_container.comic_hud.objective.text.begins_with("Descubra onde"),"First mission should be discovering the island")
	check(player.gear_container.comic_hud.location_label.text == "LOCAL DESCONHECIDO","Location must remain unknown until discovering the route")
	check(not player.mobile_controls.find_children("*","OptionButton",true,false).size(),"Development controls button must not remain under logo")
	print("FULL_OPENING_AND_DIALOGIC_OK stages=",stages)
	island.queue_free()
	await process_frame
	stages.clear()
	await load_island()
	intro = island.get_node("Opening")
	for frame in 4: await process_frame
	intro.skip()
	await process_frame
	player = island.get_node("Player")
	check(player.can_move and player.camera.current,"Skip must restore movement and gameplay camera")
	check(not intro.active,"Skip did not stop opening")
	print("OPENING_SKIP_OK")
	island.queue_free()
	await process_frame
	await load_island()
	intro = island.get_node("Opening")
	for frame in 400:
		await process_frame
		if intro.stage == "dialogue": break
	check(intro.stage == "dialogue","Could not reach dialogue for skip check")
	intro.skip()
	for frame in 6: await process_frame
	check(root.get_node("Dialogic").current_timeline == null,"Skipping during speech must stop the Dialogic timeline")
	check(island.get_node("Player").can_move,"Skipping speech did not restore controls")
	print("SKIP_DURING_DIALOGUE_OK")
	island.queue_free()
	await process_frame
	# Retry uses the static session flag, avoiding an opening loop after death.
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	for frame in 6: await process_frame
	check(not island.get_node("Opening").active and island.get_node("Player").can_move,"Retry replayed or locked the opening")
	island.queue_free()
	await process_frame
	print("ISLAND_INTRO ","PASS" if failures==0 else "FAIL"," failures=",failures)
	quit(0 if failures==0 else 1)

func bone_position(skeleton: Skeleton3D,bone: String) -> Vector3:
	return skeleton.global_transform*skeleton.get_bone_global_pose(skeleton.find_bone(bone)).origin
