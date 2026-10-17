@tool
extends Node3D

@export_group("Perguntas do Pleistoceno")
@export var question_bank: Resource = preload("res://_testes/cenario_ilha/parkour/pleistocene_questions.tres")

@export_group("Ciclo das plataformas")
## Tempo sólido, em segundos. O ciclo não depende de o jogador pisar na plataforma.
@export_range(1.5, 20.0, 0.1) var active_seconds := 6.0:
	set(value):
		active_seconds = maxf(value, 1.5)
		_refresh()
@export_range(0.5, 10.0, 0.1) var ghost_seconds := 2.0:
	set(value):
		ghost_seconds = maxf(value, 0.5)
		_refresh()
## Defasagem entre plataformas vizinhas; próxima do tempo de um salto.
@export_range(0.0, 3.0, 0.05) var stagger_seconds := 1.25:
	set(value):
		stagger_seconds = maxf(value, 0.0)
		_refresh()
@export_range(0.0, 2.0, 0.05) var warning_seconds := 0.75
@export var cycle_enabled := true:
	set(value):
		cycle_enabled = value
		_refresh()
@export_group("Aparencia")
@export var edge_color := Color("ff7a18"):
	set(value):
		edge_color = value
		_refresh()
@export_range(0.0, 8.0, 0.1) var glow_strength := 3.0:
	set(value):
		glow_strength = value
		_refresh()

var _elapsed := 0.0
var _platforms: Array[Node3D] = []
var _player: CharacterBody3D
var _last_landed := -1
var _checkpoint_index := -1
var _route_active := false
var _completed := false
var _epoch_presented := false
var quiz: Node3D


func _ready() -> void:
	process_physics_priority = -10
	for child: Node in get_children():
		if child is Node3D and child.has_method("apply_cycle"):
			_platforms.append(child)
	_refresh()
	if not Engine.is_editor_hint():
		_player = get_node_or_null("../Player") as CharacterBody3D
		if _player:
			_player.respawned.connect(_on_player_respawned)
			if not get_tree().get_meta("skip_parkour_quiz",false):
				quiz = preload("res://_testes/cenario_ilha/parkour/pleistocene_quiz.gd").new()
				quiz.name = "PleistoceneQuiz"
				quiz.question_bank = question_bank
				add_child(quiz)
	set_physics_process(not Engine.is_editor_hint())


func _physics_process(delta: float) -> void:
	if cycle_enabled:
		_elapsed = fposmod(_elapsed + delta, active_seconds + ghost_seconds)
		apply_cycle_time(_elapsed)
	_update_progress()


func _update_progress() -> void:
	if not is_instance_valid(_player) or _player.is_dead:
		return
	if _player.is_on_floor():
		var support := _supporting_platform_index()
		if support >= 0:
			_register_landing(support)


func _supporting_platform_index() -> int:
	for i in _player.get_slide_collision_count():
		var collision := _player.get_slide_collision(i)
		# Touching a platform's side while standing on terrain is not a landing.
		if collision.get_normal().dot(_player.up_direction) >= cos(_player.floor_max_angle):
			var index := _platforms.find(collision.get_collider())
			if index >= 0:
				return index
	return -1


func _register_landing(index: int) -> void:
	if _completed or index <= _last_landed:
		return
	if is_instance_valid(quiz) and not quiz.allows_platform(index): return
	_last_landed = index
	_route_active = true
	var platform := _platforms[index]
	var hud := _get_hud()
	if hud:
		hud.set_location("PLEISTOCENO","TRILHA DOS CÉUS")
		if not _epoch_presented:
			_epoch_presented = true
			# Kai introduces the epoch during the opening; do not repeat a popup.
	if platform.checkpoint:
		_checkpoint_index = index
		_player.player_start_position = platform.surface_position() + Vector3(0, 0.08, 0)
		if hud and index != 0:
			hud.notify_checkpoint("PONTO DE RETORNO ATIVADO")
	if index == _platforms.size() - 1:
		_completed = true
		_route_active = false
		if hud:
			hud.set_location("PLEISTOCENO","MIRANTE")
			hud.set_objective("Trilha concluída! Aproveite o mirante.")
			hud.notify("TRILHA DOS CÉUS CONCLUÍDA!")
	elif hud:
		hud.set_objective("Trilha dos céus · %02d / %02d\n%s" % [index + 1, _platforms.size(), "Verde: retorno seguro." if platform.checkpoint else "Siga as setas. Vermelho: vai sumir!"])
	if is_instance_valid(quiz): quiz.on_landing(index)


func _on_player_respawned() -> void:
	_last_landed = _checkpoint_index
	# Give the next jumps a fresh solid window after recovering.
	_elapsed = maxf(_checkpoint_index, 0) * stagger_seconds + 3.0
	apply_cycle_time(_elapsed)
	var hud := _get_hud()
	if hud and _player.health > 0 and not _completed and _checkpoint_index >= 0:
		hud.set_objective("Trilha dos céus · %02d / %02d\nContinue do ponto de retorno." % [_checkpoint_index + 1, _platforms.size()])
		hud.notify_checkpoint("DE VOLTA AO PONTO DE RETORNO")


func _get_hud() -> Control:
	if is_instance_valid(_player) and _player.gear_container:
		var hud: Control = _player.gear_container.comic_hud
		if is_instance_valid(hud) and hud.is_node_ready():
			return hud
	return null


func _refresh() -> void:
	if not is_node_ready():
		return
	for platform in _platforms:
		platform.set_palette(edge_color, glow_strength)
	apply_cycle_time(_elapsed)


func apply_cycle_time(time: float) -> void:
	for i in _platforms.size():
		var platform := _platforms[i]
		platform.quiz_blocked = is_instance_valid(quiz) and not quiz.allows_platform(i)
		if not cycle_enabled or Engine.is_editor_hint():
			platform.set_active_state(true)
		else:
			platform.apply_cycle(time, active_seconds, ghost_seconds, minf(warning_seconds, active_seconds), i * stagger_seconds)


func get_platforms() -> Array[Node3D]:
	return _platforms.duplicate()
