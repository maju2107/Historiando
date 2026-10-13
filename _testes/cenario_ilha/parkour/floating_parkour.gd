@tool
extends Node3D

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
var _retry_pending := false


func _ready() -> void:
	process_physics_priority = -10
	for child: Node in get_children():
		if child is Node3D and child.has_method("apply_cycle"):
			_platforms.append(child)
	_refresh()
	if not Engine.is_editor_hint():
		_player = get_node_or_null("../Player") as CharacterBody3D
	set_physics_process(not Engine.is_editor_hint())


func _physics_process(delta: float) -> void:
	if cycle_enabled:
		_elapsed = fposmod(_elapsed + delta, active_seconds + ghost_seconds)
		apply_cycle_time(_elapsed)
	_update_progress()


func _update_progress() -> void:
	if not is_instance_valid(_player) or _player.is_dead or _completed or _retry_pending:
		return
	if _player.is_on_floor():
		for i in _player.get_slide_collision_count():
			var platform_index := _platforms.find(_player.get_slide_collision(i).get_collider())
			if platform_index >= 0:
				_register_landing(platform_index)
				break
	# Recover shortly after a missed jump instead of falling through the island.
	# The entrance remains a free exit back to ordinary island exploration.
	if _route_active and _last_landed > 0 and _player.velocity.y < 0.0:
		if _player.global_position.y < _platforms[_last_landed].surface_position().y - 3.0:
			_retry_pending = true
			_retry_from_checkpoint.call_deferred()


func _register_landing(index: int) -> void:
	if index <= _last_landed:
		return
	_last_landed = index
	_route_active = true
	var platform := _platforms[index]
	var hud := _get_hud()
	if platform.checkpoint:
		_checkpoint_index = index
		_player.player_start_position = platform.surface_position() + Vector3(0, 0.08, 0)
		if hud:
			hud.notify("TRILHA DOS CÉUS" if index == 0 else "PONTO DE RETORNO ATIVADO")
	if index == _platforms.size() - 1:
		_completed = true
		_route_active = false
		if hud:
			hud.set_objective("Trilha concluída! Aproveite o mirante.")
			hud.notify("TRILHA DOS CÉUS CONCLUÍDA!")
	elif hud:
		hud.set_objective("Trilha dos céus · %02d / %02d\n%s" % [index + 1, _platforms.size(), "Verde: retorno seguro." if platform.checkpoint else "Siga as setas. Vermelho: vai sumir!"])


func _retry_from_checkpoint() -> void:
	_retry_pending = false
	if not is_instance_valid(_player) or _player.is_dead:
		return
	_player.respawn_player()
	# Damage immunity can suppress take_damage; recovery still needs a floor.
	if not _player.is_dead:
		_player.global_position = _player.player_start_position
		_player.velocity = Vector3.ZERO
	_last_landed = _checkpoint_index
	# Give the next jumps a fresh solid window after recovering.
	_elapsed = maxf(_checkpoint_index, 0) * stagger_seconds + 3.0
	apply_cycle_time(_elapsed)
	var hud := _get_hud()
	if hud and not _player.is_dead:
		hud.set_objective("Trilha dos céus · %02d / %02d\nContinue do ponto de retorno." % [_checkpoint_index + 1, _platforms.size()])
		hud.notify("DE VOLTA AO PONTO DE RETORNO")


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
		if not cycle_enabled or Engine.is_editor_hint():
			platform.set_active_state(true)
		else:
			platform.apply_cycle(time, active_seconds, ghost_seconds, minf(warning_seconds, active_seconds), i * stagger_seconds)


func get_platforms() -> Array[Node3D]:
	return _platforms.duplicate()
