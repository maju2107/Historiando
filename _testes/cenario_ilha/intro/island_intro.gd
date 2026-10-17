extends Node3D
## Wake-up, island reveal, Kai's comic introduction and the return-home mission.
signal stage_changed(stage: String)
signal finished
const Kit = preload("res://scenes/ui/ui_kit.gd")
const Pose = preload("res://_testes/cenario_ilha/intro/waking_pose.gd")
const KaiScene = preload("res://assets/characters/kai/KaiActor.tscn")
static var seen_this_session := false
@export var enabled := true
@export_range(.05,2,.05) var duration_scale := 1.0
@export_category("Diálogos / Dialogic")
## Edit the Text events in Dialogic; keep Signal events for camera/animation cues.
# Load on instantiation, after Dialogic registers its .dtl resource loader.
@export var waking_dialogue: DialogicTimeline = load("res://dialogo/linha_do_tempo/ilha_despertar.dtl")
@export var kai_dialogue: DialogicTimeline = load("res://dialogo/linha_do_tempo/kai_encontro.dtl")
var active := false
var stage := "waiting"
var player: CharacterBody3D
var camera: Camera3D
var pose: Node
var _course: Node3D
var _overlay: CanvasLayer
var _lids: ShaderMaterial
var _tween: Tween
var _spawn := Vector3.ZERO
var _dialogic: Node
var _layout: Node
var _dialogue_started := false
var kai: Node3D
var _fragment_total := 0
var _kai_destination := Vector3.ZERO
var _original_player_rotation := Vector3.ZERO
var _cue_tween: Tween
var _effects: Array[Node] = []
var _reduced_motion := false
var mission_assigned := false
var yara_face: Node

func _ready() -> void:
	player = get_parent().get_node("Player")
	_course = get_parent().get_node("ParkourFlutuante")
	_spawn = player.global_position
	_original_player_rotation = player.gobot.rotation
	_fragment_total = get_parent().get_node("Topazios").get_child_count()
	var preferences := ConfigFile.new()
	preferences.load("user://interface.cfg")
	_reduced_motion = bool(preferences.get_value("accessibility","reduce_motion",false))
	_prepare_kai.call_deferred()
	# Start beside the trunk so the regular follow camera has a clear view.
	player.camera_pivo.rotation.y = deg_to_rad(60)
	if not enabled or seen_this_session or get_tree().get_meta("skip_island_intro",false):
		stage = "finished"
		call_deferred("_set_first_objective")
		return
	duration_scale = float(get_tree().get_meta("intro_duration_scale",duration_scale))
	active = true
	player.can_move = false
	player.set_physics_process(false)
	player.mobile_controls.hide()
	_course.set_physics_process(false)
	player.get_node("HUD").hide()
	_build_overlay()
	call_deferred("_run")

func _set_first_objective(revealed := true) -> void:
	var hud: Control = player.gear_container.comic_hud
	if is_instance_valid(hud):
		if revealed:
			mission_assigned = true
			hud.set_fragment_goal(_fragment_total)
			hud.set_collectibles(player.gears)
			hud.set_objective("Siga os cristais pela ilha.\nReúna os fragmentos para voltar para casa.")
			hud.set_location("PLEISTOCENO")
		else:
			hud.set_objective("Descubra onde você está.\nSiga os cristais pela ilha.")
			hud.set_location("LOCAL DESCONHECIDO")

func _stage(name: String) -> void:
	stage = name
	stage_changed.emit(name)

func _run() -> void:
	await get_tree().process_frame
	if not active: return
	_set_first_objective(false)
	player.get_node("HUD").hide()
	pose = Pose.new()
	add_child(pose)
	pose.configure(player.gobot)
	yara_face = preload("res://assets/characters/FacialAnimator.gd").new()
	add_child(yara_face)
	yara_face.configure(player.gobot,preload("res://assets/characters/yara/yara_expressions.res"))
	yara_face.automatic_blink = false
	pose.authored_face_blink = true
	yara_face.blink_override = func(): return pose.blink
	yara_face.set_mood("curious")
	camera = Camera3D.new()
	camera.name = "OpeningCamera"
	camera.fov = 58
	camera.near = .06
	add_child(camera)
	camera.make_current()
	player.gobot.hide()
	camera.look_at_from_position(_spawn+Vector3(0,.70,-.05),_spawn+Vector3(0,2.2,-5))
	_stage("first_person_blink")
	await _open_eyes(.7,.25)
	if not active: return
	await _open_eyes(.8,.35)
	if not active: return
	_lids.set_shader_parameter("openness",0.0)
	player.gobot.show()
	camera.fov = 48
	camera.look_at_from_position(_spawn+Vector3(-1.55,.85,-2.6),_spawn+Vector3(0,.38,-.12))
	_stage("seated")
	await _animate(_lids,"shader_parameter/openness",1.0,.65)
	if not active: return
	await _animate(pose,"blink",1.0,.075)
	if not active: return
	await _animate(pose,"blink",0.0,.13)
	if not active: return
	_stage("head_shake")
	await _animate(pose,"nod",.20,.22)
	if not active: return
	await _animate(pose,"nod",-.12,.24)
	if not active: return
	await _animate(pose,"nod",.09,.22)
	if not active: return
	await _animate(pose,"nod",0.0,.30)
	if not active: return
	_dialogic = get_node("/root/Dialogic")
	_dialogic.Text.text_started.connect(_on_speech)
	_layout = _dialogic.Styles.load_style("res://dialogo/estilos/island_banner_style.tres",self)
	_dialogue_started = true
	_dialogic.start(waking_dialogue)
	_stage("dialogue")
	await _dialogic.timeline_ended
	_dialogue_started = false
	if not active: return
	_stage("island_pan")
	await _travel(Vector3(-24,17,34),Vector3(-3,5,14),3.0,65)
	if not active: return
	await _travel(Vector3(-31,25,-2),Vector3(0,9,-3),3.5,68)
	if not active: return
	await _travel(Vector3(27,32,-28),Vector3(0,14,0),3.8,68)
	if not active: return
	_stage("island_overview")
	# Stand while the camera surveys the far side, then return to the face.
	await _animate(pose,"seated",0.0,1.5)
	if not active: return
	await _travel(_spawn+Vector3(.7,1.4,-2.4),_spawn+Vector3(0,1.05,0),2.6,48)
	if not active: return
	_stage("return_closeup")
	await _animate(pose,"blink",1.0,.075)
	if not active: return
	await _animate(pose,"blink",0.0,.13)
	if not active: return
	await _wait(.8)
	if not active: return
	_stage("kai_arrival")
	# Wake-up and dialogue share the authored, fitted lid/lash shapes.
	pose.blink = 0.0
	yara_face.automatic_blink = true
	kai.show()
	kai.call("play_gesture","Walk",1.1)
	kai.call("face_position",_kai_destination)
	_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(kai,"global_position",_kai_destination,1.8*duration_scale)
	await _tween.finished
	if not active: return
	kai.call("face_position",player.global_position)
	player.gobot.look_at(Vector3(kai.global_position.x,player.gobot.global_position.y,kai.global_position.z),Vector3.UP,true)
	kai.call("play_gesture","Idle")
	await _travel(_spawn+Vector3(-.1,1.2,-2.8),_spawn+Vector3(.60,.82,.30),.9,53)
	if not active: return
	_dialogic.signal_event.connect(_on_kai_cue)
	# Dialogic frees the previous layout at the end of the waking timeline.
	_layout = _dialogic.Styles.load_style("res://dialogo/estilos/island_banner_style.tres",self)
	_dialogue_started = true
	_dialogic.start(kai_dialogue)
	_stage("kai_dialogue")
	await _dialogic.timeline_ended
	_dialogue_started = false
	if not active: return
	if _dialogic.signal_event.is_connected(_on_kai_cue): _dialogic.signal_event.disconnect(_on_kai_cue)
	if _cue_tween and _cue_tween.is_valid(): _cue_tween.kill()
	pose.confused = 0
	player.gobot.rotation = _original_player_rotation
	kai.call("play_gesture","Idle")
	_stage("mission_handoff")
	await _wait(.4)
	if not active: return
	_stage("handing_control_back")
	var gameplay_camera: Camera3D = player.camera
	await _travel(gameplay_camera.global_position,_spawn+Vector3(0,1.0,0),.9,gameplay_camera.fov)
	if active: skip()

func _prepare_kai() -> void:
	kai = KaiScene.instantiate()
	kai.name = "Kai"
	get_parent().add_child(kai)
	_kai_destination = _spawn + Vector3(1.15,0,.65)
	var ray := PhysicsRayQueryParameters3D.create(_kai_destination+Vector3.UP*3,_kai_destination-Vector3.UP*6,1,[player.get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(ray)
	if not hit.is_empty(): _kai_destination.y = hit.position.y+.012
	kai.global_position = _spawn+Vector3(3.0,_kai_destination.y-_spawn.y,.90) if active else _kai_destination
	kai.visible = not active
	kai.call("face_position",player.global_position)

func _on_kai_cue(value: Variant) -> void:
	if not active or not str(value).begins_with("kai_") and not str(value).begins_with("yara_"): return
	var cue := str(value)
	_stage(cue)
	var kai_mood := "reassuring"
	var yara_mood := "curious"
	match cue:
		"kai_when","kai_epoch": kai_mood = "amused"
		"yara_console":
			kai_mood = "amused"
			yara_mood = "surprised"
		"kai_correct":
			kai_mood = "amused"
			yara_mood = "confused"
		"kai_explain","yara_back": yara_mood = "confused"
		"kai_mission","yara_ready","kai_goodbye": yara_mood = "determined"
	kai.face.set_mood(kai_mood)
	yara_face.set_mood(yara_mood)
	yara_face.automatic_blink = cue!="yara_console"
	var gesture := "Talk"
	match cue:
		"kai_when": gesture = "Explain"
		"kai_epoch":
			gesture = "Explain"
			_comic_pop("PLEISTOCENO",kai.global_position+Vector3(0,1.65,0),Kit.GOLD)
		"yara_console":
			gesture = "React"
			pose.confused = 1.0
			_comic_pop("?!",_spawn+Vector3(0,1.60,0),Kit.GOLD)
		"kai_correct": gesture = "Correct"
		"kai_explain": gesture = "Explain"
		"yara_back": gesture = "Shrug"
		"kai_pieces": gesture = "Point"
		"kai_mission":
			gesture = "Point"
			_set_first_objective(true)
			player.get_node("HUD").show()
			player.gear_container.comic_hud.set_cinematic_mission_only(true)
		"yara_ready": gesture = "Shrug"
		"kai_goodbye": gesture = "Talk"
	kai.call("play_gesture",gesture,1.0)
	if cue != "yara_console": pose.confused = .25 if cue == "yara_back" else 0.0
	var actor: Node3D = player.gobot if cue.begins_with("yara_") else kai
	var face := actor.global_position+Vector3(0,1.03,0)
	var front := actor.global_basis.z.normalized()
	var side := front.cross(Vector3.UP)
	var to := face+front*1.55+side*(-.65 if cue.begins_with("yara_") else .75)+Vector3.UP*.08
	var target := face
	var fov := 48.0
	if cue in ["kai_mission","kai_goodbye"]:
		to = _spawn+Vector3(-.1,1.2,-2.8)
		target = _spawn+Vector3(.60,.82,.30)
		fov = 53
	if _cue_tween and _cue_tween.is_valid(): _cue_tween.kill()
	var start := camera.global_transform
	var end := Transform3D(Basis.looking_at(target-to),to)
	var initial_fov := camera.fov
	_cue_tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_cue_tween.tween_method(func(w: float):
		camera.global_transform = start.interpolate_with(end,w)
		camera.fov = lerpf(initial_fov,fov,w),0.0,1.0,maxf(.04,(.15 if _reduced_motion else .55)*duration_scale))

func _on_speech(info: Dictionary) -> void:
	if not active: return
	var character: Variant = info.get("character")
	var is_kai: bool = character!=null and character.display_name=="Kai"
	if is_instance_valid(kai) and is_instance_valid(kai.face):
		if is_kai: kai.face.speak(str(info.get("text","")))
		else: kai.face.stop_speaking()
	if is_instance_valid(yara_face):
		if not is_kai: yara_face.speak(str(info.get("text","")))
		else: yara_face.stop_speaking()

func _comic_pop(words: String,_at: Vector3,color: Color) -> void:
	var mark := preload("res://_testes/cenario_ilha/intro/comic_reaction.gd").new()
	mark.words = words
	mark.accent = color
	var screen := get_viewport().get_visible_rect().size
	var factor := screen.x/1600.0
	mark.size = Vector2(185,170) if words=="?!" else Vector2(400,170)
	mark.position = Vector2(screen.x*.79,screen.y*.35)-mark.size/2
	mark.pivot_offset = mark.size/2
	mark.rotation = -.07
	_overlay.get_child(0).add_child(mark)
	_effects.append(mark)
	mark.scale = Vector2.ONE*factor*(1.0 if _reduced_motion else .25)
	var tween := mark.create_tween()
	if not _reduced_motion:
		tween.tween_property(mark,"scale",Vector2.ONE*factor*1.08,.18*duration_scale).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tween.tween_property(mark,"scale",Vector2.ONE*factor,.12*duration_scale).set_trans(Tween.TRANS_SINE)
	tween.tween_interval(1.35*duration_scale)
	tween.tween_property(mark,"modulate:a",0.0,.3*duration_scale)
	tween.tween_callback(mark.queue_free)

func _build_overlay() -> void:
	_overlay = CanvasLayer.new()
	_overlay.layer = 50
	add_child(_overlay)
	var full := Control.new()
	full.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	full.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.add_child(full)
	var eyelids := ColorRect.new()
	eyelids.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	eyelids.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_lids = ShaderMaterial.new()
	_lids.shader = preload("res://_testes/cenario_ilha/intro/eyelid_overlay.gdshader")
	_lids.set_shader_parameter("openness",0.0)
	eyelids.material = _lids
	full.add_child(eyelids)
	var bottom := ColorRect.new()
	bottom.color = Color("100019")
	bottom.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.offset_top = -58
	full.add_child(bottom)
	var skip_button := Kit.button(bottom,"PULAR ABERTURA  ›",Rect2(0,0,250,46),skip,Kit.PAPER,true)
	skip_button.set_anchors_and_offsets_preset(Control.PRESET_RIGHT_WIDE)
	skip_button.offset_left = -260
	skip_button.offset_right = -16
	skip_button.offset_top = 6
	skip_button.offset_bottom = -6
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func _open_eyes(open_time: float,hold_time: float) -> void:
	await _animate(_lids,"shader_parameter/openness",1.0,open_time)
	if not active: return
	await _wait(hold_time)
	if not active: return
	await _animate(_lids,"shader_parameter/openness",0.0,.18)

func _animate(object: Object,property: String,value: Variant,seconds: float) -> void:
	_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	if object is ShaderMaterial:
		var parameter := property.trim_prefix("shader_parameter/")
		var initial: float = object.get_shader_parameter(parameter)
		_tween.tween_method(func(weight: float): object.set_shader_parameter(parameter,weight),initial,float(value),maxf(.015,seconds*duration_scale))
	else:
		_tween.tween_property(object,property,value,maxf(.015,seconds*duration_scale))
	await _tween.finished

func _wait(seconds: float) -> void:
	_tween = create_tween()
	_tween.tween_interval(maxf(.015,seconds*duration_scale))
	await _tween.finished

func _travel(to: Vector3,target: Vector3,seconds: float,fov: float) -> void:
	var start := camera.global_transform
	var end := Transform3D(Basis.looking_at(target-to),to)
	var initial_fov := camera.fov
	_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_method(func(weight: float):
		camera.global_transform = start.interpolate_with(end,weight)
		camera.fov = lerpf(initial_fov,fov,weight),0.0,1.0,maxf(.015,seconds*duration_scale))
	await _tween.finished

func skip() -> void:
	if not active: return
	active = false
	seen_this_session = true
	if _tween and _tween.is_valid(): _tween.kill()
	if _cue_tween and _cue_tween.is_valid(): _cue_tween.kill()
	if is_instance_valid(_dialogic) and _dialogic.signal_event.is_connected(_on_kai_cue): _dialogic.signal_event.disconnect(_on_kai_cue)
	if _dialogue_started and is_instance_valid(_dialogic):
		_dialogic.end_timeline(true)
	_dialogue_started = false
	if is_instance_valid(_dialogic) and _dialogic.Text.text_started.is_connected(_on_speech): _dialogic.Text.text_started.disconnect(_on_speech)
	if is_instance_valid(yara_face): yara_face.release()
	if is_instance_valid(pose): pose.release()
	if is_instance_valid(_layout): _layout.queue_free()
	if is_instance_valid(_overlay): _overlay.queue_free()
	if is_instance_valid(camera): camera.queue_free()
	for effect in _effects:
		if is_instance_valid(effect): effect.queue_free()
	if is_instance_valid(kai):
		kai.global_position = _kai_destination
		kai.show()
		kai.call("play_gesture","Idle")
		kai.face.stop_speaking()
		kai.face.set_mood("reassuring")
		kai.call("face_position",player.global_position)
	player.gobot.rotation = _original_player_rotation
	player.gear_container.comic_hud.set_cinematic_mission_only(false)
	player.gobot.show()
	player.get_node("HUD").show()
	player.mobile_controls.show()
	player.velocity = Vector3.ZERO
	player.can_move = true
	player.set_physics_process(true)
	player.camera.make_current()
	player.reset_physics_interpolation()
	_course.set_physics_process(true)
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE if player.control_preset == 2 else Input.MOUSE_MODE_CAPTURED)
	_set_first_objective()
	_stage("finished")
	finished.emit()

func _exit_tree() -> void:
	if _dialogue_started and is_instance_valid(_dialogic):
		_dialogic.end_timeline(true)
