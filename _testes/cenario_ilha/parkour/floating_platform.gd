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
@export var checkpoint := false:
	set(value):
		checkpoint = value
		_refresh_geometry()

var is_solid := true
var quiz_blocked := false
var _material: ShaderMaterial
var _collision: CollisionShape3D
var _route_marker: MeshInstance3D
var _marker_material: StandardMaterial3D
var _palette := Color("dda63b")
var _beacons: Node3D


func _ready() -> void:
	_material = $Visual.material_override.duplicate() as ShaderMaterial
	$Visual.material_override = _material
	_collision = $CollisionShape3D
	_route_marker = MeshInstance3D.new()
	_route_marker.name = "RouteMarker"
	_route_marker.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_marker_material = StandardMaterial3D.new()
	_marker_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_marker_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	_marker_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_route_marker.material_override = _marker_material
	add_child(_route_marker)
	_beacons = Node3D.new()
	_beacons.name = "CheckpointBeacons"
	add_child(_beacons)
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
	_material.set_shader_parameter("checkpoint", 1.0 if checkpoint else 0.0)
	# A flat chevron points to the next jump without obstructing the player.
	var arrow := ImmediateMesh.new()
	arrow.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for point: Vector3 in [Vector3(-0.48, 0, 0.16), Vector3(0, 0, -0.30), Vector3(0, 0, -0.06), Vector3(-0.48, 0, 0.16), Vector3(0, 0, -0.06), Vector3(-0.48, 0, 0.40), Vector3(0, 0, -0.30), Vector3(0.48, 0, 0.16), Vector3(0.48, 0, 0.40), Vector3(0, 0, -0.30), Vector3(0.48, 0, 0.40), Vector3(0, 0, -0.06)]:
		arrow.surface_add_vertex(point)
	arrow.surface_end()
	_route_marker.mesh = arrow
	_route_marker.position = Vector3(0, platform_size.y * 0.5 + 0.025, -platform_size.z * 0.28)
	_route_marker.visible = platform_number != 21
	_refresh_beacons()
	if permanent:
		set_active_state(true, 0.0)


func _refresh_beacons() -> void:
	for child in _beacons.get_children():
		_beacons.remove_child(child)
		child.queue_free()
	if not checkpoint:
		return
	# Floating crystals on the rear corners identify safe magical platforms.
	for side in [-1.0, 1.0]:
		var base := Vector3(side * (platform_size.x * 0.5 - 0.24), platform_size.y * 0.5, platform_size.z * 0.5 - 0.24)
		for part in 2:
			var lamp := MeshInstance3D.new()
			var cylinder := CylinderMesh.new()
			cylinder.top_radius = 0.0 if part == 0 else 0.16
			cylinder.bottom_radius = 0.16 if part == 0 else 0.0
			cylinder.height = 0.24
			cylinder.radial_segments = 4
			lamp.mesh = cylinder
			lamp.position = base + Vector3(0, 0.74 if part == 0 else 0.50, 0)
			var material := StandardMaterial3D.new()
			material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			material.albedo_color = Color(0.47, 0.79, 0.68, 0.65)
			material.emission_enabled = true
			material.emission = Color("77c9ae")
			material.emission_energy_multiplier = 2.0
			lamp.material_override = material
			_beacons.add_child(lamp)


func set_palette(color: Color, energy: float) -> void:
	if _material == null:
		return
	_palette = Color("77c9ae") if checkpoint else color
	_material.set_shader_parameter("edge_color", _palette)
	_material.set_shader_parameter("glow_strength", energy)
	_marker_material.albedo_color = _palette
	_marker_material.emission_enabled = true
	_marker_material.emission = _palette
	_marker_material.emission_energy_multiplier = 0.6


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
	_material.set_shader_parameter("time_remaining", clampf((active_seconds - phase) / active_seconds, 0.0, 1.0) if active else 0.0)


func set_active_state(active: bool, warning: float = 0.0) -> void:
	active = (active or permanent) and not quiz_blocked
	if _material == null:
		return
	_material.set_shader_parameter("solid_amount", 1.0 if active else 0.0)
	_material.set_shader_parameter("warning_amount", 0.0 if permanent else warning)
	_material.set_shader_parameter("time_remaining", 1.0 if active else 0.0)
	_marker_material.albedo_color = Color(_palette, 1.0 if active else 0.12)
	_marker_material.emission_energy_multiplier = 0.6 if active else 0.0
	if active != is_solid:
		is_solid = active
		# Disable the body layer immediately and defer the shape change safely.
		collision_layer = 1 if active else 0
		_collision.set_deferred("disabled", not active)


func surface_position() -> Vector3:
	return to_global(Vector3(0, platform_size.y * 0.5, 0))
