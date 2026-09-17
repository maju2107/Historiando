@tool
extends Node3D

@export_group("Ciclo das plataformas")
## Tempo sólido, em segundos. O ciclo não depende de o jogador pisar na plataforma.
@export_range(1.5, 20.0, 0.1) var active_seconds := 4.5:
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


func _ready() -> void:
	process_physics_priority = -10
	for child: Node in get_children():
		if child is Node3D and child.has_method("apply_cycle"):
			_platforms.append(child)
	_refresh()
	set_physics_process(not Engine.is_editor_hint())


func _physics_process(delta: float) -> void:
	if cycle_enabled:
		_elapsed = fposmod(_elapsed + delta, active_seconds + ghost_seconds)
		apply_cycle_time(_elapsed)


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
