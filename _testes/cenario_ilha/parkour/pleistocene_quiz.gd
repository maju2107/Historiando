extends Node3D
## Physical answers; the incorrect surface is visible but has no collision.
signal hint_started(question_index: int)
signal hint_finished
const Platform = preload("res://_testes/cenario_ilha/parkour/FloatingPlatform.tscn")
const Sign = preload("res://_testes/cenario_ilha/parkour/answer_sign.gd")
const Pair = preload("res://_testes/cenario_ilha/parkour/answer_pair.gd")
const Bubble = preload("res://_testes/cenario_ilha/parkour/quiz_bubble.gd")
const Kit = preload("res://scenes/ui/ui_kit.gd")
@export var question_bank: Resource = preload("res://_testes/cenario_ilha/parkour/pleistocene_questions.tres")
var questions: Array = []
var solved: Array[bool] = []
var wrong_platforms: Array[Node3D] = []
var signs: Array[Node3D] = []
var current_question := -1
var hint_active := false
var hints_played := 0
var wrong_attempts := 0
var bubble: Control
var _course: Node3D
var _player: CharacterBody3D
var _falling_question := -1
var _failed_question := -1
var _failure_height := 0.0
var _hint_pending := false
var _dialogic: Node
var _kai: Node3D
var _kai_transform := Transform3D.IDENTITY
var _kai_visible := false
var _camera: Camera3D
var _previous_physics := true
var _controls_visible := false
var _previous_model_transform := Transform3D.IDENTITY
var _camera_aspect := Camera3D.KEEP_HEIGHT
var _camera_fov := 75.0
var _fov_transition: Tween
var _reduced_motion := false

func _ready() -> void:
	_course = get_parent()
	_player = _course.get_node("../Player")
	_camera_aspect = _player.camera.keep_aspect
	_camera_fov = _player.camera.fov
	var settings := preload("res://scenes/ui/interface.gd").load_settings()
	_reduced_motion = bool(get_tree().get_meta("quiz_reduce_motion",settings.get_value("accessibility","reduce_motion",false)))
	questions = question_bank.questions
	for index in questions.size():
		solved.append(false)
		_build_choice(index)
	var overlay := CanvasLayer.new()
	overlay.layer = 45
	add_child(overlay)
	bubble = Bubble.new()
	bubble.reduced_motion = _reduced_motion
	overlay.add_child(bubble)
	bubble.dismissed.connect(_question_layout)
	_player.respawned.connect(_on_respawned)
	get_viewport().size_changed.connect(func(): _question_layout.call_deferred())
	_course.apply_cycle_time(_course._elapsed)

func _build_choice(index: int) -> void:
	var data: Dictionary = questions[index]
	var correct: Node3D = _course.get_platforms()[int(data.answer_platform)]
	var question: Node3D = _course.get_platforms()[int(data.question_platform)]
	# Preserve the authored lane center while allowing the correct answer
	# index to be changed in the resource without breaking the two-way fork.
	var forward := -question.basis.z.normalized()
	var right := forward.cross(Vector3.UP).normalized()
	var side := -1.0 if int(data.correct) == 0 else 1.0
	var center := correct.position-right*float(data.authored_lane)*2.6
	correct.position = center+right*side*2.6
	var wrong := Platform.instantiate()
	wrong.name = "WrongAnswer%d" % (index+1)
	wrong.position = center-right*side*2.6
	wrong.rotation = correct.rotation
	wrong.platform_size = correct.platform_size
	wrong.permanent = true
	add_child(wrong)
	wrong.set_palette(Color("dda63b"),2.0)
	wrong.collision_layer = 0
	wrong.get_node("CollisionShape3D").set_deferred("disabled",true)
	wrong._route_marker.hide()
	correct._route_marker.hide()
	wrong_platforms.append(wrong)
	var pair := Pair.new()
	pair.reduced_motion = _reduced_motion
	pair.name = "AnswerPlates%d" % (index+1)
	add_child(pair)
	for choice in 2:
		var target: Node3D = correct if choice == int(data.correct) else wrong
		var sign := Sign.new()
		sign.words = str(data.answers[choice])
		sign.letter = "A" if choice == 0 else "B"
		pair.add_child(sign)
		sign.global_position = target.surface_position()+Vector3.UP*1.45
	pair.hide()
	signs.append(pair)

func allows_platform(index: int) -> bool:
	for question_index in questions.size():
		if not solved[question_index] and index > int(questions[question_index].answer_platform): return false
	return true

func on_landing(index: int) -> void:
	for question_index in questions.size():
		var data: Dictionary = questions[question_index]
		if index == int(data.checkpoint) or index == int(data.question_platform):
			if solved[question_index]: return
			current_question = question_index
			for other_index in signs.size():
				if other_index != question_index: signs[other_index].dismiss()
			signs[question_index].present()
			if not hint_active: bubble.present(question_index,str(data.question))
			_question_layout()
		elif index == int(data.answer_platform) and current_question == question_index and not solved[question_index]:
			solved[question_index] = true
			signs[question_index].dismiss()
			_falling_question = -1
			bubble.dismiss()
			_question_layout()
			_course._elapsed = index*_course.stagger_seconds+2.0
			_course.apply_cycle_time(_course._elapsed)
			_correct_notice(question_index)

func _correct_notice(index: int) -> void:
	if bubble.visible: await bubble.dismissed
	if not is_inside_tree() or current_question != index or bubble.showing: return
	var hud: Control = _course._get_hud()
	if hud: hud.notify("BOA! RESPOSTA CERTA · %d / 4" % (index+1))

func _question_layout() -> void:
	if not is_instance_valid(bubble): return
	var active_question := current_question >= 0 and not solved[current_question]
	# Keep the mobile HUD and camera framing steady until the bubble has left.
	if not active_question and bubble.visible and not bubble.showing: return
	var screen := get_viewport().get_visible_rect().size
	var portrait := screen.x < screen.y
	_player.camera.keep_aspect = Camera3D.KEEP_WIDTH if active_question and portrait else _camera_aspect
	var target_fov := minf(_camera_fov,65.0) if active_question else _camera_fov
	if _fov_transition and _fov_transition.is_valid(): _fov_transition.kill()
	if _reduced_motion: _player.camera.fov = target_fov
	else:
		_fov_transition = create_tween()
		_fov_transition.tween_property(_player.camera,"fov",target_fov,.42).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	var hud: Control = _course._get_hud()
	if hud:
		hud.objective_panel.visible = not active_question
		hud.location_label.visible = not active_question
		hud.activity_label.visible = not active_question
		hud._resize()
		if active_question and (portrait or screen.y < 550):
			# Mobile health/pause flank the answers in a row under the top bubble.
			hud.canvas.position.y = bubble._rest_position.y+bubble.size.y+30-48*hud.canvas.scale.y

func _physics_process(_delta: float) -> void:
	if not is_instance_valid(_player) or _player.is_dead or hint_active or current_question < 0: return
	if _falling_question >= 0:
		# Give the fall a visible beat before the existing one-life recovery.
		if _player.global_position.y < _failure_height-2.8 and not _player.is_invulnerable:
			_failed_question = _falling_question
			_falling_question = -1
			wrong_attempts += 1
			_player.take_damage(1)
		return
	if solved[current_question]: return
	var wrong: Node3D = wrong_platforms[current_question]
	var local := wrong.to_local(_player.global_position)
	var surface: float = wrong.platform_size.y*.5
	if absf(local.x) < wrong.platform_size.x*.5 and absf(local.z) < wrong.platform_size.z*.5 and local.y < surface+1.15 and local.y > surface-.65 and _player.velocity.y <= 0:
		signs[current_question].dismiss()
		bubble.dismiss()
		_falling_question = current_question
		_failure_height = wrong.surface_position().y

func _on_respawned() -> void:
	_falling_question = -1
	if _failed_question >= 0:
		var failed := _failed_question
		_failed_question = -1
		# take_damage updates health before emitting respawned, even at zero.
		if _player.health > 0 and not _hint_pending:
			_hint_pending = true
			_begin_hint.call_deferred(failed)
	elif current_question >= 0 and not solved[current_question] and not hint_active:
		bubble.present(current_question,str(questions[current_question].question))

func _begin_hint(index: int) -> void:
	await get_tree().create_timer(.65,false).timeout
	_hint_pending = false
	if not is_inside_tree() or _player.is_dead or _player.health <= 0: return
	var ending: Node = _course.get_node_or_null("../Ending")
	if ending and ending.started: return
	hint_active = true
	hints_played += 1
	bubble.dismiss()
	for pair in signs: pair.dismiss()
	_previous_physics = _player.is_physics_processing()
	_controls_visible = _player.mobile_controls.visible
	Input.set_mouse_mode(Kit.ui_mouse_mode(get_tree()))
	_player.can_move = false
	_player.set_physics_process(false)
	_player.velocity = Vector3.ZERO
	_player.mobile_controls.reset_touches()
	_player.mobile_controls.hide()
	_player.anim_player.play("Idle",.2)
	_previous_model_transform = _player.gobot.global_transform
	_kai = _course.get_node("../Opening").kai
	_kai_transform = _kai.global_transform
	_kai_visible = _kai.visible
	var checkpoint: Node3D = _course.get_platforms()[int(questions[index].checkpoint)]
	var right := checkpoint.global_basis.x.normalized()
	_kai.global_position = checkpoint.surface_position()+right*1.65
	_kai.show()
	_kai.face_position(_player.global_position)
	_player.gobot.look_at(Vector3(_kai.global_position.x,_player.gobot.global_position.y,_kai.global_position.z),Vector3.UP,true)
	_kai.face.set_mood("reassuring")
	_kai.play_gesture("Explain")
	_camera = Camera3D.new()
	_camera.near = .06
	add_child(_camera)
	_camera.global_transform = _player.camera.global_transform
	_camera.fov = _player.camera.fov
	_camera.make_current()
	var focus := (_kai.global_position+_player.global_position)*.5+Vector3.UP*.95
	var destination := focus+checkpoint.global_basis.z*3.8+Vector3.UP*.9
	var transform := Transform3D(Basis.looking_at(focus-destination),destination)
	var start := _camera.global_transform
	var tween := create_tween()
	tween.tween_method(func(weight: float):
		if is_instance_valid(_camera): _camera.global_transform = start.interpolate_with(transform,weight),0.0,1.0,.55).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_dialogic = get_node("/root/Dialogic")
	_dialogic.Text.text_started.connect(_hint_speech)
	_dialogic.Styles.load_style("res://dialogo/estilos/island_banner_style.tres",self)
	var hud: Control = _course._get_hud()
	if hud: (hud.get("notification") as Label).hide()
	hint_started.emit(index)
	_dialogic.start(load(str(questions[index].hint)))
	await _dialogic.timeline_ended
	_close_hint(true)

func _hint_speech(info: Dictionary) -> void:
	if hint_active and is_instance_valid(_kai): _kai.face.speak(str(info.get("text","")))

func _close_hint(restore: bool) -> void:
	if not hint_active: return
	hint_active = false
	if is_instance_valid(_dialogic) and _dialogic.Text.text_started.is_connected(_hint_speech):
		_dialogic.Text.text_started.disconnect(_hint_speech)
	if not restore: return
	if is_instance_valid(_kai):
		_kai.face.stop_speaking()
		_kai.global_transform = _kai_transform
		_kai.visible = _kai_visible
		_kai.play_gesture("Idle")
	_player.camera.make_current()
	_player.gobot.global_transform = _previous_model_transform
	if is_instance_valid(_camera): _camera.queue_free()
	_player.can_move = true
	_player.set_physics_process(_previous_physics)
	_player.mobile_controls.visible = _controls_visible
	Input.set_mouse_mode(Kit.gameplay_mouse_mode(get_tree()))
	if current_question >= 0 and not solved[current_question]:
		bubble.present(current_question,str(questions[current_question].question))
		signs[current_question].present()
	_question_layout()
	hint_finished.emit()

func _exit_tree() -> void:
	if hint_active and is_instance_valid(_dialogic):
		_close_hint(false)
		_dialogic.end_timeline(true)
