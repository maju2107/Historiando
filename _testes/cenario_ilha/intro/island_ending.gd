extends Node3D
## All-fragment finale. Dialogic owns speech; this node owns staging and cleanup.
signal stage_changed(stage: String)
signal finished
const Kit = preload("res://scenes/ui/ui_kit.gd")
const Face = preload("res://assets/characters/FacialAnimator.gd")
const KaiScene = preload("res://assets/characters/kai/KaiActor.tscn")
@export var enabled := true
@export_range(.05,2,.05) var duration_scale := 1.0
## Authored open clearing, separate from the current checkpoint or last pickup.
@export var clearing_position := Vector3(-7,4.08,22)
@export_category("Diálogos / Dialogic")
@export var ending_dialogue: DialogicTimeline = load("res://dialogo/linha_do_tempo/ilha_final.dtl")
var active := false
var started := false
var completed := false
var stage := "waiting"
var start_count := 0
var player: CharacterBody3D
var kai: Node3D
var yara_face: Node
var camera: Camera3D
var portal: Node3D
var _hud: Control
var _spawn := Vector3.ZERO
var _queued := false
var _dialogic: Node
var _dialogue_started := false
var _overlay: CanvasLayer
var _overlay_root: Control
var _fade_layer: CanvasLayer
var _fade: ColorRect
var _pause_button: Button
var _skip_button: Button
var _tween: Tween
var _camera_tween: Tween
var _portal_material: ShaderMaterial
var _shards: Array[Node3D] = []
var _clock := 0.0
var _reduced_motion := false
var _hud_color := Color.WHITE
var _bottom: ColorRect

func _ready() -> void:
	player = get_parent().get_node("Player")
	_spawn = clearing_position
	_connect_mission.call_deferred()

func _connect_mission() -> void:
	await get_tree().process_frame
	if not enabled or get_tree().get_meta("skip_island_ending",false): return
	_hud = player.gear_container.comic_hud
	_hud.fragments_completed.connect(_queue_start)
	if _hud.fragments_complete: _queue_start()

func _queue_start() -> void:
	if started or _queued: return
	_queued = true
	_start.call_deferred()

func _stage(value: String) -> void:
	stage = value
	stage_changed.emit(value)

func _start() -> void:
	var opening: Node = get_parent().get_node("Opening")
	if opening.active: await opening.finished
	var quiz: Node = get_parent().get_node("ParkourFlutuante").quiz
	if quiz and quiz.hint_active: await quiz.hint_finished
	if not is_inside_tree() or started or not _hud.fragments_complete: return
	started = true
	active = true
	start_count += 1
	duration_scale = float(get_tree().get_meta("ending_duration_scale",duration_scale))
	var settings := preload("res://scenes/ui/interface.gd").load_settings()
	_reduced_motion = bool(get_tree().get_meta("ending_reduce_motion",settings.get_value("accessibility","reduce_motion",false)))
	if not get_tree().get_meta("ending_preview",false):
		get_node("/root/FaseCore").concluir_fase(1)
	player.can_move = false
	player.set_physics_process(false)
	player.velocity = Vector3.ZERO
	player.mobile_controls.reset_touches()
	_hud_color = _hud.modulate
	player.mobile_controls.hide()
	get_parent().get_node("ParkourFlutuante").set_physics_process(false)
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	kai = opening.kai
	if not is_instance_valid(kai):
		kai = KaiScene.instantiate()
		get_parent().add_child(kai)
	yara_face = Face.new()
	add_child(yara_face)
	yara_face.configure(player.gobot,preload("res://assets/characters/yara/yara_expressions.res"))
	yara_face.set_mood("surprised")
	camera = Camera3D.new()
	camera.near = .06
	add_child(camera)
	camera.global_transform = player.camera.global_transform
	camera.fov = player.camera.fov
	camera.make_current()
	_build_overlay()
	_stage("pickup_settle")
	await _settle_pickup()
	if not active: return
	_stage("pickup_hold")
	await _wait(1.6)
	if not active: return
	_tween = create_tween()
	_tween.tween_property(_hud,"modulate:a",0.0,.45*duration_scale)
	await _tween.finished
	if not active: return
	player.get_node("HUD").hide()
	_bottom.modulate.a = 0
	_bottom.show()
	var bars := create_tween()
	bars.tween_property(_bottom,"modulate:a",1.0,.45*duration_scale)
	_stage("fragments_gather")
	_pop("TODOS OS FRAGMENTOS!",Kit.GOLD)
	await _wait(1.35)
	if not active: return
	_stage("transition_out")
	await _fade_to(1,1.15)
	if not active: return
	# A short dissolve returns to the open clearing, even if the last
	# pickup was on a disappearing platform. No visible teleport or falling.
	player.global_position = _spawn+Vector3(-.25,0,0)
	player.reset_physics_interpolation()
	kai.global_position = _spawn+Vector3(1.15,.012,.65)
	var ground := get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(kai.global_position+Vector3.UP*2,kai.global_position-Vector3.UP*2,1,[player.get_rid()]))
	if not ground.is_empty(): kai.global_position.y = ground.position.y+.012
	kai.show()
	kai.face_position(player.global_position)
	player.gobot.look_at(Vector3(kai.global_position.x,player.gobot.global_position.y,kai.global_position.z),Vector3.UP,true)
	kai.play_gesture("React")
	_build_portal()
	_two_shot(true)
	_stage("return_to_clearing")
	await _wait(.2)
	if not active: return
	await _fade_to(0,1.35)
	if not active: return
	await _wait(.6)
	if not active: return
	_dialogic = get_node("/root/Dialogic")
	_dialogic.signal_event.connect(_on_cue)
	_dialogic.Text.text_started.connect(_on_speech)
	_dialogic.Styles.load_style("res://dialogo/estilos/island_banner_style.tres",self)
	_dialogue_started = true
	_stage("ending_dialogue")
	_dialogic.start(ending_dialogue)
	await _dialogic.timeline_ended
	_dialogue_started = false
	if not active: return
	_stage("walk_home")
	if _camera_tween and _camera_tween.is_valid(): _camera_tween.kill()
	_two_shot(false)
	var destination := _spawn+Vector3(0,0,1.8)
	player.gobot.look_at(Vector3(destination.x,player.gobot.global_position.y,destination.z),Vector3.UP,true)
	player.anim_player.play("Walk",.18)
	kai.play_gesture("Explain")
	_tween = create_tween()
	_tween.tween_property(player,"global_position",destination,1.8*duration_scale).set_trans(Tween.TRANS_SINE)
	await _tween.finished
	if not active: return
	player.anim_player.play("Idle",.15)
	await _fade_to(1,.75)
	if active: finish()

func _settle_pickup() -> void:
	var from := player.global_position
	var hit := get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from+Vector3.UP*.2,from-Vector3.UP*3.0,1,[player.get_rid()]))
	var landing := from
	if not hit.is_empty() and hit.normal.y > .8:
		var height: float = hit.position.y+.08
		if from.y-height > .04: landing.y = height
	var focus := landing+Vector3.UP*.95
	var offset := camera.global_position-focus
	_camera_to(focus+offset*.96,focus,maxf(48,camera.fov-4),1.6)
	if not landing.is_equal_approx(from):
		_tween = create_tween()
		_tween.tween_property(player,"global_position",landing,.55*duration_scale).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		await _tween.finished
	else:
		await _wait(.35)
	if active: player.anim_player.play("Idle",.35)

func _on_cue(value: Variant) -> void:
	var cue := str(value)
	if not active or not cue.begins_with("end_"): return
	_stage(cue)
	var yara_speaks := cue in ["end_found","end_luggage","end_thanks","end_goodbye"]
	yara_face.set_mood("amused" if cue in ["end_luggage","end_thanks"] else "reassuring")
	kai.face.set_mood("amused" if cue in ["end_luggage","end_joke","end_thanks"] else "reassuring")
	var gesture := "Talk"
	match cue:
		"end_found": gesture = "React"
		"end_portal":
			gesture = "Point"
			portal.show()
			var grow := create_tween()
			grow.tween_property(portal,"scale",Vector3.ONE,(.25 if _reduced_motion else .8)*duration_scale).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
			_pop("DE VOLTA PRA CASA!",Kit.GOLD)
		"end_luggage":
			yara_face.set_mood("surprised")
			gesture = "Shrug"
			_pop("?!",Kit.PAPER)
		"end_joke": gesture = "Correct"
		"end_remember": gesture = "Explain"
		"end_home": gesture = "Explain"
	kai.play_gesture(gesture)
	if cue in ["end_portal","end_home"]:
		_two_shot(false)
	else:
		var actor: Node3D = player.gobot if yara_speaks else kai
		var face := actor.global_position+Vector3(0,1.03,0)
		var front := actor.global_basis.z.normalized()
		_camera_to(face+front*1.7+front.cross(Vector3.UP)*.6+Vector3.UP*.12,face,48,.5)

func _on_speech(info: Dictionary) -> void:
	if not active: return
	var speaker: Variant = info.get("character")
	var kai_speaks: bool = speaker != null and speaker.display_name == "Kai"
	if kai_speaks:
		kai.face.speak(str(info.get("text","")))
		yara_face.stop_speaking()
	else:
		yara_face.speak(str(info.get("text","")))
		kai.face.stop_speaking()

func _two_shot(immediate: bool) -> void:
	_camera_to(_spawn+Vector3(-.45,1.5,-3.8),_spawn+Vector3(.35,.95,.75),54,0 if immediate else .6)

func _camera_to(position_to: Vector3,target: Vector3,fov: float,seconds: float) -> void:
	if _camera_tween and _camera_tween.is_valid(): _camera_tween.kill()
	var destination := Transform3D(Basis.looking_at(target-position_to),position_to)
	if seconds == 0:
		camera.global_transform = destination
		camera.fov = fov
		return
	var initial := camera.global_transform
	var initial_fov := camera.fov
	_camera_tween = create_tween()
	_camera_tween.tween_method(func(weight: float):
		camera.global_transform = initial.interpolate_with(destination,weight)
		camera.fov = lerpf(initial_fov,fov,weight),0.0,1.0,maxf(.02,(.15 if _reduced_motion else seconds)*duration_scale)).set_trans(Tween.TRANS_SINE)

func _build_overlay() -> void:
	_overlay = CanvasLayer.new()
	_overlay.layer = 50
	add_child(_overlay)
	_overlay_root = Control.new()
	_overlay_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_overlay_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.add_child(_overlay_root)
	var bottom := Kit.rect(_overlay_root,Rect2(),Kit.INK)
	_bottom = bottom
	bottom.hide()
	bottom.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.offset_top = -58
	_pause_button = Kit.button(bottom,"II   PAUSA",Rect2(16,6,170,46),func(): get_node("/root/BotaoGlobal").toggle_pause(),Kit.PAPER,true)
	_skip_button = Kit.button(bottom,"PULAR DESFECHO  ›",Rect2(),finish,Kit.PAPER,true)
	_skip_button.set_anchors_and_offsets_preset(Control.PRESET_RIGHT_WIDE)
	_skip_button.offset_right = -16
	_skip_button.offset_top = 6
	_skip_button.offset_bottom = -6
	get_viewport().size_changed.connect(_layout_controls)
	_layout_controls()
	_fade_layer = CanvasLayer.new()
	_fade_layer.layer = 80
	add_child(_fade_layer)
	_fade = Kit.rect(_fade_layer,Rect2(),Color(Kit.PAPER,0))
	_fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func _layout_controls() -> void:
	var width := get_viewport().get_visible_rect().size.x
	_pause_button.size.x = minf(170,width*.30)
	_skip_button.offset_left = -minf(256,width-_pause_button.size.x-48)-16

func _build_portal() -> void:
	portal = Node3D.new()
	portal.name = "ReturnHomePortal"
	add_child(portal)
	portal.global_position = _spawn+Vector3(0,1.1,1.8)
	portal.scale = Vector3.ONE*.05
	portal.hide()
	var gold := StandardMaterial3D.new()
	gold.albedo_color = Kit.GOLD
	gold.emission_enabled = true
	gold.emission = Kit.GOLD*.3
	gold.roughness = .65
	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = .95
	torus.outer_radius = 1.06
	torus.rings = 48
	torus.ring_segments = 12
	ring.mesh = torus
	ring.rotation.x = PI/2
	ring.material_override = gold
	portal.add_child(ring)
	var disc := MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(1.94,1.94)
	disc.mesh = quad
	disc.rotation.y = PI # Face the camera without mirroring the brand emblem.
	_portal_material = ShaderMaterial.new()
	_portal_material.shader = preload("res://_testes/cenario_ilha/intro/time_portal.gdshader")
	_portal_material.set_shader_parameter("emblem",preload("res://assets/ui/historiando/brand_symbol.svg"))
	disc.material_override = _portal_material
	portal.add_child(disc)
	for index in 12:
		var shard := MeshInstance3D.new()
		var gem := SphereMesh.new()
		gem.radial_segments = 4
		gem.rings = 1
		gem.radius = .07
		gem.height = .22
		shard.mesh = gem
		shard.material_override = gold
		portal.add_child(shard)
		_shards.append(shard)
	_update_portal()

func _process(delta: float) -> void:
	if not active or not is_instance_valid(portal): return
	_clock += delta
	_update_portal()

func _update_portal() -> void:
	var phase := 0.0 if _reduced_motion else _clock*.6
	_portal_material.set_shader_parameter("phase",phase)
	for index in _shards.size():
		var angle := index*TAU/_shards.size()+phase*.18
		_shards[index].position = Vector3(cos(angle)*1.18,sin(angle)*1.18,0)
		_shards[index].rotation.z = angle-PI/2

func _pop(words: String,color: Color) -> void:
	var mark := preload("res://_testes/cenario_ilha/intro/comic_reaction.gd").new()
	mark.words = words
	mark.accent = color
	var screen := get_viewport().get_visible_rect().size
	var factor := clampf(minf(screen.x/1600,screen.y/900),.65,1.25)
	mark.size = Vector2(480,220) if words != "?!" else Vector2(180,160)
	factor = minf(factor,minf((screen.x-36)/(mark.size.x+140),(screen.y-80)/(mark.size.y+90)))
	mark.scale = Vector2.ONE*factor
	var margin := Vector2(70,45)*factor
	var preferred := Vector2(screen.x*.76,screen.y*.52)-mark.size*factor/2
	mark.position = preferred.clamp(margin,screen-mark.size*factor-margin)
	_overlay_root.add_child(mark)
	var fade := mark.create_tween()
	fade.tween_interval(2.2*duration_scale)
	fade.tween_property(mark,"modulate:a",0.0,.35*duration_scale)
	fade.tween_callback(mark.queue_free)

func _wait(seconds: float) -> void:
	await get_tree().create_timer(maxf(.02,seconds*duration_scale),false).timeout

func _fade_to(alpha: float,seconds: float) -> void:
	_tween = create_tween()
	_tween.tween_property(_fade,"color:a",alpha,maxf(.02,seconds*duration_scale)).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	await _tween.finished

func _disconnect_dialogue() -> void:
	if not is_instance_valid(_dialogic): return
	if _dialogic.signal_event.is_connected(_on_cue): _dialogic.signal_event.disconnect(_on_cue)
	if _dialogic.Text.text_started.is_connected(_on_speech): _dialogic.Text.text_started.disconnect(_on_speech)
	if _dialogue_started:
		_dialogue_started = false
		_dialogic.end_timeline(true)

func finish() -> void:
	if not active: return
	active = false
	completed = true
	if _tween and _tween.is_valid(): _tween.kill()
	if _camera_tween and _camera_tween.is_valid(): _camera_tween.kill()
	_disconnect_dialogue()
	if is_instance_valid(yara_face): yara_face.release()
	if is_instance_valid(kai):
		kai.face.stop_speaking()
		kai.play_gesture("Idle")
	if is_instance_valid(_fade): _fade.color.a = 1
	if is_instance_valid(_hud): _hud.modulate = _hud_color
	_stage("complete")
	get_node("/root/BotaoGlobal").show_level_complete(_hud.fragment_goal)
	finished.emit()

func _exit_tree() -> void:
	active = false
	_disconnect_dialogue()
	if is_instance_valid(yara_face): yara_face.release()
