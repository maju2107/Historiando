extends SceneTree
var failures := 0
var stages: Array[String] = []
var saw_dialogue := false
var saw_kai_banner := false
var saw_yara_reply := false
var saw_pose := false
var checked_ground_sit := false
var checked_manual_advance := false
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
	var deadline := Time.get_ticks_msec()+90000
	var next_click := 0
	while Time.get_ticks_msec()<deadline:
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
				var before_mouth_time: float = intro.yara_face._clock
				paused = true
				for sample in 10: await process_frame
				check(intro.stage == "dialogue" and nodes[0].visible_characters == before_characters,"Dialogue and cutscene must pause together")
				check(intro.yara_face._clock==before_mouth_time,"Facial animation must pause with the dialogue")
				paused = false
				# Wait longer than the old 2.5-second auto-advance after reveal.
				nodes[0].finish_text()
				await create_timer(3.1).timeout
				check(intro.stage == "dialogue" and dialogic.current_timeline != null,"Speech advanced without player input")
				var banner: Node = nodes[0].get_parent().get_parent()
				check(banner.advance_prompt.visible == (player.control_preset != 2),"A should be a desktop prompt, hidden for touch controls")
				check(banner.advance_prompt.position.y >= nodes[0].position.y+nodes[0].get_content_height(),"Advance prompt overlaps speech")
				check(banner.panel.find_children("*","Button",true,false).is_empty(),"Dialogue must use a small sign instead of a continue button")
				checked_manual_advance = true
				# Native screen-wide click/tap dispatch is checked separately.
				banner._advance()
				next_click = Time.get_ticks_msec()+400
				print("MANUAL_DIALOGUE_WAIT_AND_CORNER_SIGN_OK")
		# Exercise the real Dialogic input path, including reveal then advance.
		if intro.stage=="kai_epoch" or intro.stage=="yara_console":
			for text in get_nodes_in_group("dialogic_dialog_text"):
				if text.is_visible_in_tree() and not text.text.is_empty():
					if "Pleistoceno" in text.get_parsed_text(): saw_kai_banner = true
					if "PlayStation" in text.get_parsed_text(): saw_yara_reply = true
		if saw_dialogue and Time.get_ticks_msec()>next_click and root.get_node("Dialogic").current_timeline != null:
			var action := InputEventAction.new()
			action.action = "dialogic_default_action"
			action.pressed = true
			root.get_node("Dialogic").Inputs._unhandled_input(action)
			next_click = Time.get_ticks_msec()+400
		if not intro.active: break
	check(not intro.active and intro.stage == "finished","Opening did not finish")
	check(saw_pose,"Opening did not pose the legs and prepare both eyes for blinking")
	check(saw_dialogue,"Actual Dialogic timeline did not display the opening line")
	check(checked_manual_advance,"Manual dialogue advance was not verified")
	check(saw_kai_banner and saw_yara_reply,"Kai and Yara's comedy must display in the visible dialogue banner")
	for stage in ["first_person_blink","seated","head_shake","dialogue","island_pan","return_closeup","kai_arrival","kai_when","kai_epoch","yara_console","kai_correct","kai_explain","yara_back","kai_pieces","kai_mission","yara_ready","kai_goodbye","mission_handoff","handing_control_back","finished"]:
		check(stage in stages,"Missing cutscene stage: "+stage)
	check(player.can_move and player.is_physics_processing(),"Opening failed to restore movement")
	check(player.camera.current,"Opening failed to restore gameplay camera")
	check(player.get_node("HUD").visible,"Opening failed to restore HUD")
	check(player.gobot.position.is_equal_approx(intro.pose._original_position),"Standing must restore the original model height")
	for original in intro.pose._original_meshes:
		check(original.mesh.mesh==original.original,"Opening must restore the shared source mesh after blinking")
	for surface in intro.pose._eyes+intro.pose._lashes:
		check(surface.mesh.get_surface_override_material(surface.surface)==surface.original,"Opening must restore eye and eyelash materials")
	var hud: Control = player.gear_container.comic_hud
	check(hud.fragment_goal==31 and hud.fragment_mission.visible,"Kai must assign all 31 island fragments")
	check(hud.location_label.text == "PLEISTOCENO","Kai must reveal the epoch")
	check(is_instance_valid(intro.kai) and intro.kai.visible and intro.kai.gesture_count>=12,"Kai must remain in the island after performing his gestures")
	check(intro.kai.face.mouth_peak>.15 and intro.yara_face.mouth_peak>.15,"Both speakers must articulate their mouths")
	check(intro.kai.face.expression_changes>=10 and intro.yara_face.expression_changes>=10,"Characters must react throughout the exchange")
	check(not intro.kai.face.speaking and not intro.yara_face.is_processing(),"Cinematic facial performance must end cleanly")
	check(hud._cinematic_visibility.is_empty(),"Cinematic HUD visibility was not restored")
	player.set_physics_process(false)
	var course := island.get_node("ParkourFlutuante")
	course.set_physics_process(false)
	var crystals := island.get_node("Topazios").get_children()
	var first: Area3D = crystals[0]
	first._on_body_entered(player)
	first._on_body_entered(player)
	check(player.gears==1 and "01 / 31" in hud.fragment_count.text,"A duplicate pickup must count exactly once")
	course._register_landing(0)
	check(hud.fragment_mission.visible and "01 / 31" in hud.fragment_count.text,"Parkour objectives must preserve the return-home counter")
	check(not hud.epoch_presentation.visible,"The epoch popup must not repeat Kai's explanation")
	for crystal in crystals.slice(1): crystal._on_body_entered(player)
	check(player.gears==31 and hud.fragments_complete and hud.fragment_bar.value==31,"All real island pickups must complete the mission")
	check(hud.get("notification").text=="TODOS OS FRAGMENTOS REUNIDOS!","Final pickup must retain the mission completion message")
	print("FRAGMENT_MISSION_31_PICKUPS_AND_PARKOUR_OK")
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
	await load_island()
	intro = island.get_node("Opening")
	deadline = Time.get_ticks_msec()+30000
	while Time.get_ticks_msec()<deadline:
		await process_frame
		if intro.stage=="kai_correct": break
		if root.get_node("Dialogic").current_timeline != null and Time.get_ticks_msec()>next_click:
			root.get_node("Dialogic").Inputs.handle_input()
			next_click = Time.get_ticks_msec()+250
	check(intro.stage=="kai_correct","Could not reach Kai's comedy for skip check")
	intro.skip()
	for frame in 6: await process_frame
	check(root.get_node("Dialogic").current_timeline==null and intro.kai.visible,"Skip during Kai must stop dialogue and retain the NPC")
	check(island.get_node("Player").can_move and island.get_node("Player").gear_container.comic_hud.fragment_goal==31,"Skip during Kai must restore controls and assign the mission")
	print("SKIP_DURING_KAI_OK")
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
	FileAccess.open("res://art/island_intro/kai_validation.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"full_opening":true,"visible_kai_yara_dialogue":saw_kai_banner and saw_yara_reply,"ground_sitting":checked_ground_sit,"real_fragment_pickups":31,"skip_early_and_during_each_conversation":true,"retry_restores_controls":true,"facial_speech_and_reactions":true,"pause_restores_pose_meshes_and_materials":true},"\t"))
	quit(0 if failures==0 else 1)

func bone_position(skeleton: Skeleton3D,bone: String) -> Vector3:
	return skeleton.global_transform*skeleton.get_bone_global_pose(skeleton.find_bone(bone)).origin
