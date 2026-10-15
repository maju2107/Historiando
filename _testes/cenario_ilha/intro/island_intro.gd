extends Node3D
## Opening sequence and the first exploration objective. No changes to the rig asset.
signal stage_changed(stage: String)
signal finished
const Kit = preload("res://scenes/ui/ui_kit.gd")
const Pose = preload("res://_testes/cenario_ilha/intro/waking_pose.gd")
static var seen_this_session := false
@export var enabled := true
@export_range(.05,2,.05) var duration_scale := 1.0
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

func _ready() -> void:
	player = get_parent().get_node("Player")
	_course = get_parent().get_node("ParkourFlutuante")
	_spawn = player.global_position
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

func _set_first_objective() -> void:
	var hud: Control = player.gear_container.comic_hud
	if is_instance_valid(hud):
		hud.set_objective("Descubra onde você está.\nSiga os cristais pela ilha.")
		hud.set_location("LOCAL DESCONHECIDO")

func _stage(name: String) -> void:
	stage = name
	stage_changed.emit(name)

func _run() -> void:
	await get_tree().process_frame
	if not active: return
	_set_first_objective()
	player.get_node("HUD").hide()
	pose = Pose.new()
	add_child(pose)
	pose.configure(player.gobot)
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
	_layout = _dialogic.Styles.load_style("res://dialogo/estilos/island_banner_style.tres",self)
	_dialogue_started = true
	_dialogic.start("res://dialogo/linha_do_tempo/ilha_despertar.dtl")
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
	_stage("handing_control_back")
	var gameplay_camera: Camera3D = player.camera
	await _travel(gameplay_camera.global_position,_spawn+Vector3(0,1.0,0),.9,gameplay_camera.fov)
	if active: skip()

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
	if _dialogue_started and is_instance_valid(_dialogic):
		_dialogic.end_timeline(true)
	_dialogue_started = false
	if is_instance_valid(pose): pose.release()
	if is_instance_valid(_layout): _layout.queue_free()
	if is_instance_valid(_overlay): _overlay.queue_free()
	if is_instance_valid(camera): camera.queue_free()
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
