@tool
extends Node3D
## Procedural water previews in the editor; interaction runs only during play.
const Profile = preload("res://_testes/cenario_ilha/water/watercourse_profile.gd")
const SurfaceShader = preload("res://_testes/cenario_ilha/water/river_surface.gdshader")
const FallShader = preload("res://_testes/cenario_ilha/water/waterfall.gdshader")
const RIPPLE_COUNT := 24
const RIPPLE_LIFETIME := 2.2

@export_group("Agua")
@export var shallow_color := Color("89cff0"):
	set(value):
		shallow_color = value
		_update_materials()
@export var deep_color := Color("4f9dd9"):
	set(value):
		deep_color = value
		_update_materials()
@export var foam_color := Color("f1faff"):
	set(value):
		foam_color = value
		_update_materials()
@export_range(0.0, 3.0, 0.05) var flow_speed := 0.7:
	set(value):
		flow_speed = value
		_update_materials()
@export_range(0.0, 0.02, 0.001) var refraction_strength := 0.006:
	set(value):
		refraction_strength = value
		_update_materials()
@export_group("Interacao")
@export var interactor_group: StringName = &"player"
@export_range(0.15, 0.8, 0.05) var ripple_spacing := 0.40

var _materials: Array[ShaderMaterial] = []
var _fall_materials: Array[ShaderMaterial] = []
var _ripples := PackedVector4Array()
var _ripple_index := 0
var _clock := 0.0
var _contacts: Dictionary = {}
var _splash: CPUParticles3D


func _ready() -> void:
	_build()
	set_physics_process(not Engine.is_editor_hint())


func _build() -> void:
	for child: Node in get_children(true):
		if child.has_meta(&"water_generated"):
			child.free()
	_materials.clear()
	_fall_materials.clear()
	_contacts.clear()
	_clock = 0.0
	_ripple_index = 0
	_ripples.resize(RIPPLE_COUNT)
	_ripples.fill(Vector4(0, 0, -100, 0))
	for i in Profile.REACHES.size():
		_create_reach(i)
		_create_fall(i)
	_create_stones()
	_splash = _create_spray("RespingosDoPlayer", Vector3.ZERO, 0.18, 9, true)
	_update_materials()


func _add_generated(node: Node) -> void:
	node.set_meta(&"water_generated", true)
	add_child(node, false, Node.INTERNAL_MODE_BACK)


func _create_reach(index: int) -> void:
	var reach: Vector4 = Profile.REACHES[index]
	var steps := ceili((reach.y - reach.x) / 0.22)
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	const COLUMNS := 10
	for row in steps + 1:
		var z := lerpf(reach.x, reach.y, float(row) / steps)
		for column in COLUMNS + 1:
			var u := float(column) / COLUMNS
			surface.set_uv(Vector2(u, float(row) / steps))
			surface.set_normal(Vector3.UP)
			surface.add_vertex(Vector3(Profile.center_x(z) + (u * 2.0 - 1.0) * Profile.half_width(z, index), reach.z, z))
	for row in steps:
		for column in COLUMNS:
			var a := row * (COLUMNS + 1) + column
			for vertex in [a, a + 1, a + COLUMNS + 1, a + 1, a + COLUMNS + 2, a + COLUMNS + 1]:
				surface.add_index(vertex)
	var material := ShaderMaterial.new()
	material.shader = SurfaceShader
	material.set_shader_parameter("ripples", _ripples)
	if index > 0:
		material.set_shader_parameter("impact_position", Vector2(Profile.center_x(reach.x + 0.25), reach.x + 0.25))
		material.set_shader_parameter("impact_strength", 1.0)
	_materials.append(material)
	var water := MeshInstance3D.new()
	water.name = ["Nascente", "CorregoMedio", "CorregoBase"][index]
	water.mesh = surface.commit()
	water.material_override = material
	water.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	water.extra_cull_margin = 0.1
	_add_generated(water)


func _create_fall(index: int) -> void:
	var reach: Vector4 = Profile.REACHES[index]
	# Land on the next clear shelf, beyond any authored intermediate ledge.
	var end_z: float = Profile.REACHES[index + 1].x if index < 2 else reach.y + 0.70
	var end_y: float = Profile.REACHES[index + 1].z if index < 2 else -1.2
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	const ROWS := 32
	const COLUMNS := 16
	for row in ROWS + 1:
		var t := float(row) / ROWS
		# Rounded crest then a falling sheet: no disconnected upright water box.
		var z := lerpf(reach.y - 0.12, end_z, sin(t * PI * 0.5))
		var y := lerpf(reach.z, end_y, t * t)
		var center := lerpf(Profile.center_x(reach.y), Profile.center_x(end_z), t)
		var width := Profile.half_width(reach.y, index) * (1.0 - 0.08 * sin(t * PI))
		for column in COLUMNS + 1:
			var u := float(column) / COLUMNS
			surface.set_uv(Vector2(u, t))
			surface.add_vertex(Vector3(center + (u * 2.0 - 1.0) * width, y, z))
	for row in ROWS:
		for column in COLUMNS:
			var a := row * (COLUMNS + 1) + column
			for vertex in [a, a + 1, a + COLUMNS + 1, a + 1, a + COLUMNS + 2, a + COLUMNS + 1]:
				surface.add_index(vertex)
	surface.generate_normals()
	var material := ShaderMaterial.new()
	material.shader = FallShader
	material.set_shader_parameter("phase", float(index) * 1.7)
	material.set_shader_parameter("fade_bottom", 1.0 if index == 2 else 0.0)
	_fall_materials.append(material)
	var waterfall := MeshInstance3D.new()
	waterfall.name = ["CachoeiraSuperior", "CachoeiraInferior", "CachoeiraDaIlha"][index]
	waterfall.mesh = surface.commit()
	waterfall.material_override = material
	waterfall.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	waterfall.extra_cull_margin = 0.15
	_add_generated(waterfall)
	if index < 2:
		var impact := Vector3(Profile.center_x(end_z), end_y + 0.10, end_z + 0.10)
		_create_spray("EspumaDaQueda%d" % index, impact, Profile.half_width(reach.y, index) * 0.85, 26, false)
		_create_mist("NevoaDaQueda%d" % index, impact)
	else:
		# The final fall leaves the island; there is no imaginary impact in mid-air.
		_create_mist("NevoaSuspensa", Vector3(Profile.center_x(end_z), -0.6, end_z))


func _create_spray(label: String, at: Vector3, width: float, count: int, burst: bool) -> CPUParticles3D:
	var spray := CPUParticles3D.new()
	spray.name = label
	spray.position = at
	spray.amount = count
	spray.lifetime = 0.85
	spray.one_shot = burst
	spray.explosiveness = 1.0 if burst else 0.0
	spray.emitting = not burst
	spray.preprocess = 0.0 if burst else 1.0
	spray.local_coords = false
	spray.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	spray.emission_box_extents = Vector3(width, 0.025, 0.16)
	spray.direction = Vector3(0, 1, 0.28)
	spray.spread = 48.0
	spray.initial_velocity_min = 1.1
	spray.initial_velocity_max = 2.2
	spray.gravity = Vector3(0, -4.0, 0)
	spray.scale_amount_min = 0.06 if burst else 0.09
	spray.scale_amount_max = 0.12 if burst else 0.22
	var scale_curve := Curve.new()
	scale_curve.add_point(Vector2(0, 0.35))
	scale_curve.add_point(Vector2(0.15, 1))
	scale_curve.add_point(Vector2(0.65, 0.7))
	scale_curve.add_point(Vector2(1, 0))
	spray.scale_amount_curve = scale_curve
	var sphere := SphereMesh.new()
	sphere.radius = 1.0
	sphere.height = 2.0
	sphere.radial_segments = 8
	sphere.rings = 4
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.79, 0.97, 0.92)
	material.roughness = 1.0
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sphere.material = material
	spray.mesh = sphere
	spray.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_add_generated(spray)
	return spray


func _create_mist(label: String, at: Vector3) -> void:
	var mist := CPUParticles3D.new()
	mist.name = label
	mist.position = at
	mist.amount = 9
	mist.lifetime = 1.7
	mist.preprocess = 1.7
	mist.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	mist.emission_box_extents = Vector3(0.8, 0.1, 0.2)
	mist.direction = Vector3(0, 1, 0.45)
	mist.spread = 45.0
	mist.gravity = Vector3.ZERO
	mist.initial_velocity_min = 0.2
	mist.initial_velocity_max = 0.55
	mist.scale_amount_min = 0.6
	mist.scale_amount_max = 1.1
	mist.local_coords = false
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1, 1, 1, 0.24))
	gradient.set_color(1, Color(1, 1, 1, 0))
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.width = 64
	texture.height = 64
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(0.5, 0)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	material.albedo_texture = texture
	material.albedo_color = Color(0.73, 0.96, 0.93, 0.50)
	material.vertex_color_use_as_albedo = true
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0))
	fade.set_color(1, Color(1, 1, 1, 0))
	fade.add_point(0.2, Color.WHITE)
	mist.color_ramp = fade
	var quad := QuadMesh.new()
	quad.size = Vector2(2, 2)
	quad.material = material
	mist.mesh = quad
	mist.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_add_generated(mist)


func _create_stones() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 71831
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.37, 0.46, 0.39)
	material.roughness = 1.0
	for z: float in [-5.9, -4.7, -1.5, 0.3, 2.8, 5.4, 6.8, 11.7, 17.6, 22.1, 25.5]:
		var reach := Profile.reach_at(Vector3(Profile.center_x(z), 0, z))
		if reach < 0:
			continue
		for side: float in [-1.0, 1.0]:
			var stone := MeshInstance3D.new()
			stone.name = "Seixo"
			var mesh := SphereMesh.new()
			mesh.radial_segments = 7
			mesh.rings = 3
			stone.mesh = mesh
			stone.material_override = material
			stone.position = Vector3(Profile.center_x(z) + side * (Profile.half_width(z, reach) - 0.06), Profile.REACHES[reach].z - 0.03, z)
			stone.scale = Vector3(rng.randf_range(0.36, 0.62), rng.randf_range(0.16, 0.28), rng.randf_range(0.35, 0.70))
			stone.rotation.y = rng.randf_range(0, TAU)
			_add_generated(stone)


func _update_materials() -> void:
	for material in _materials:
		material.set_shader_parameter("shallow_color", shallow_color)
		material.set_shader_parameter("deep_color", deep_color)
		material.set_shader_parameter("foam_color", foam_color)
		material.set_shader_parameter("flow_speed", flow_speed)
		material.set_shader_parameter("refraction_strength", refraction_strength)
	for material in _fall_materials:
		material.set_shader_parameter("water_color", shallow_color.darkened(0.12))
		material.set_shader_parameter("light_color", shallow_color.lerp(foam_color, 0.40))
		material.set_shader_parameter("foam_color", foam_color)
		material.set_shader_parameter("flow_speed", flow_speed * 1.93)


func _physics_process(delta: float) -> void:
	_clock += delta
	var contact := Vector4.ZERO
	var seen: Array[int] = []
	for actor: Node in get_tree().get_nodes_in_group(interactor_group):
		if not actor is Node3D:
			continue
		var id := actor.get_instance_id()
		seen.append(id)
		var feet := to_local(actor.global_position)
		var reach := Profile.reach_at(feet)
		var touching := false
		if reach >= 0:
			var level: float = Profile.REACHES[reach].z
			touching = feet.y <= level + 0.045 and feet.y >= level - Profile.DEPTH - 0.18
			if touching:
				contact = Vector4(feet.x, level, feet.z, 1)
				var previous: Dictionary = _contacts.get(id, {})
				var entered := previous.is_empty() or int(previous.get("reach", -1)) != reach
				var traveled: float = feet.distance_to(previous.get("position", feet))
				var elapsed: float = _clock - float(previous.get("time", _clock))
				if entered or traveled >= ripple_spacing or elapsed > 0.9:
					_emit_ripple(Vector3(feet.x, level, feet.z))
					_contacts[id] = {"position": feet, "time": _clock, "reach": reach}
					if entered:
						_splash.position = Vector3(feet.x, level + 0.04, feet.z)
						_splash.restart()
						_splash.emitting = true
		if not touching:
			_contacts.erase(id)
	for id: int in _contacts.keys():
		if id not in seen:
			_contacts.erase(id)
	for material in _materials:
		material.set_shader_parameter("ripple_clock", _clock)
		material.set_shader_parameter("ripples", _ripples)
		material.set_shader_parameter("interactor", contact)


func _emit_ripple(at: Vector3) -> void:
	_ripples[_ripple_index] = Vector4(at.x, at.z, _clock, at.y)
	_ripple_index = (_ripple_index + 1) % RIPPLE_COUNT
