@tool
extends StaticBody3D
## A visible, solid platform during its active window; a faint, non-solid
## hologram during the ghost window. The course provides one shared clock.

@export var platform_size := Vector3(4.8, 0.36, 4.8):
	set(value):
		platform_size = Vector3(maxf(value.x, 0.5), maxf(value.y, 0.1), maxf(value.z, 0.5))
		_refresh_geometry()
@export var permanent := false:
	set(value):
		permanent = value
		_refresh_geometry()
@export var platform_number := 1:
	set(value):
		platform_number = value
		_refresh_geometry()

var is_solid := true
var _material: ShaderMaterial
var _label: Label3D
var _collision: CollisionShape3D


func _ready() -> void:
	_material = $Visual.material_override.duplicate() as ShaderMaterial
	$Visual.material_override = _material
	_label = $Number
	_collision = $CollisionShape3D
	_refresh_geometry()


func _refresh_geometry() -> void:
	if not is_node_ready() or _material == null:
		return
	var box := BoxMesh.new()
	box.size = platform_size
	$Visual.mesh = box
	var shape := BoxShape3D.new()
	shape.size = platform_size
	_collision.shape = shape
	_material.set_shader_parameter("platform_size", platform_size)
	_material.set_shader_parameter("permanent", 1.0 if permanent else 0.0)
	_label.position.y = platform_size.y * 0.5 + 0.018
	_label.text = "CHEGADA" if permanent else "%02d" % platform_number
	_label.font_size = 58 if permanent else 72
	if permanent:
		set_active_state(true, 0.0)


func set_palette(color: Color, energy: float) -> void:
	if _material == null:
		return
	_material.set_shader_parameter("edge_color", color)
	_material.set_shader_parameter("glow_strength", energy)
	_label.modulate = Color(color, 0.85 if is_solid else 0.12)


func apply_cycle(time: float, active_seconds: float, ghost_seconds: float, warning_seconds: float, offset: float) -> void:
	if permanent:
		set_active_state(true, 0.0)
		return
	var phase := fposmod(time - offset, active_seconds + ghost_seconds)
	var active := phase < active_seconds
	var warning := 0.0
	if active and warning_seconds > 0.0:
		warning = smoothstep(active_seconds - warning_seconds, active_seconds, phase)
	set_active_state(active, warning)


func set_active_state(active: bool, warning: float = 0.0) -> void:
	active = active or permanent
	if _material == null:
		return
	_material.set_shader_parameter("solid_amount", 1.0 if active else 0.0)
	_material.set_shader_parameter("warning_amount", 0.0 if permanent else warning)
	_label.modulate.a = 0.85 if active else 0.12
	if active != is_solid:
		is_solid = active
		# Disable the body layer immediately and defer the shape change safely.
		collision_layer = 1 if active else 0
		_collision.set_deferred("disabled", not active)


func surface_position() -> Vector3:
	return to_global(Vector3(0, platform_size.y * 0.5, 0))
