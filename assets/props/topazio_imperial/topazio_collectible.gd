extends Area3D
## One imperial topaz equals one fragment; uses the player's existing HUD API.

@export_range(0.0, 180.0, 1.0) var rotation_speed_degrees := 48.0
@export_range(0.0, 0.3, 0.01) var float_amplitude := 0.10
@export_range(0.1, 4.0, 0.1) var float_speed := 1.8
@export_range(0.0, 6.28, 0.01) var float_phase := 0.0

@onready var visual: Node3D = $Visual
var _elapsed := 0.0
var _collected := false
var _visual_origin := Vector3.ZERO


func _ready() -> void:
	_visual_origin = visual.position
	_update_float()
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	_elapsed = fposmod(_elapsed + delta * float_speed, TAU)
	_update_float()
	visual.rotate_y(deg_to_rad(rotation_speed_degrees) * delta)


func _update_float() -> void:
	visual.position = _visual_origin + Vector3.UP * sin(_elapsed + float_phase) * float_amplitude


func _on_body_entered(body: Node3D) -> void:
	if _collected or not body.is_in_group("player") or not body.has_method("collect_gear"):
		return
	if body.get("is_dead") == true:
		return
	# A capsule and head can both enter in one physics tick; count only once.
	_collected = true
	set_deferred("monitoring", false)
	hide()
	body.collect_gear()
	queue_free()
