extends RigidBody3D

# Sistema de câmera
var mouse_movement = Vector2()
@export var mouse_sensitivity = 0.5

# Física da canoa
@export var paddle_force = 300.0
@export var backward_paddle_force = 150.0
@export var turn_torque = 50.0
@export var max_speed = 12.0
@export var water_resistance = 0.96
@export var stability_force = 800.0

# Sistema de flutuação
@export var water_height = 0.0  # Altura da água (ajuste conforme sua água)
@export var buoyancy_strength = 15.0  # Força de flutuação
@export var buoyancy_damping = 5.0  # Amortecimento para evitar oscilações
@export var water_drag = 3.0  # Arrasto na água

var current_speed = 0.0
var float_points = []  # Pontos de flutuação
var water_level = 0.0

func _ready():
	# Configuração da câmera
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	
	# Configuração física da canoa
	mass = 50.0
	center_of_mass = Vector3(0, -0.3, 0)
	set_linear_damp(water_resistance)
	set_angular_damp(0.98)
	
	# Criar pontos de flutuação para a canoa
	setup_buoyancy_points()

func setup_buoyancy_points():
	# Pontos onde a flutuação será calculada
	# Ajuste esses valores conforme o tamanho da sua canoa
	float_points = [
		Vector3(-0.5, 0, -0.8),  # Frente esquerda
		Vector3(0.5, 0, -0.8),   # Frente direita
		Vector3(-0.5, 0, 0.8),   # Traseira esquerda
		Vector3(0.5, 0, 0.8),    # Traseira direita
		Vector3(0, 0, 0),        # Centro
		Vector3(-0.3, 0, -0.4),  # Meio frente esquerda
		Vector3(0.3, 0, -0.4),   # Meio frente direita
		Vector3(-0.3, 0, 0.4),   # Meio traseira esquerda
		Vector3(0.3, 0, 0.4)     # Meio traseira direita
	]

func _input(event):
	if event is InputEventMouseMotion:
		mouse_movement += event.relative*mouse_sensitivity

func _physics_process(delta):
	# Sistema de câmera
	if mouse_movement != Vector2():
		$H.rotation_degrees.y += -mouse_movement.x
		$H/V.rotation_degrees.x += -mouse_movement.y
		if $H/V.rotation_degrees.x <= -90:
			$H/V.rotation_degrees.x = -90
		if $H/V.rotation_degrees.x >= 0:
			$H/V.rotation_degrees.x = 0
		mouse_movement = Vector2()
	
	# Sistema de flutuação (chamar antes do movimento)
	apply_buoyancy(delta)
	
	# Movimento da canoa
	handle_paddling()
	handle_steering()
	stabilize_canoe()
	update_speed()
	limit_speed()
	
	# Aplicar arrasto extra na água
	apply_water_drag(delta)

func apply_buoyancy(delta):
	# Aplica força de flutuação em vários pontos da canoa
	for point in float_points:
		# Converte o ponto local para global
		var global_point = to_global(point)
		
		# Verifica se o ponto está abaixo da água
		if global_point.y < water_height:
			# Profundidade de submersão
			var depth = water_height - global_point.y
			
			# Força de flutuação (quanto mais fundo, mais força)
			var force = depth * buoyancy_strength * mass
			
			# Adiciona amortecimento para evitar oscilações
			var velocity_at_point = get_velocity_at_point(global_point)
			var damping_force = -velocity_at_point.y * buoyancy_damping
			
			# Aplica a força no ponto específico
			apply_force(Vector3(0, force + damping_force, 0), point)
			
			# Visualização opcional (para debug)
			debug_buoyancy_point(global_point, depth)

func get_velocity_at_point(point):
	# Calcula a velocidade em um ponto específico do corpo rígido
	var linear_vel = linear_velocity
	var angular_vel = angular_velocity
	var r = point - global_transform.origin
	return linear_vel + angular_vel.cross(r)

func apply_water_drag(delta):
	# Aplica arrasto extra quando a canoa está na água
	var submerged_parts = 0
	
	for point in float_points:
		var global_point = to_global(point)
		if global_point.y < water_height:
			submerged_parts += 1
	
	if submerged_parts > 0:
		# Quanto mais submersa, maior o arrasto
		var drag_factor = 1.0 - (float(submerged_parts) / float_points.size())
		linear_velocity = linear_velocity * (1.0 - (water_drag * drag_factor * delta))
		angular_velocity = angular_velocity * (1.0 - (water_drag * drag_factor * delta * 0.5))

func debug_buoyancy_point(point, depth):
	# Desenha pontos de debug (opcional, para visualizar onde a flutuação está atuando)
	if Engine.is_editor_hint():
		return
	# Você pode adicionar um MeshInstance3D pequeno ou partículas aqui
	pass

func handle_paddling():
	current_speed = linear_velocity.length()
	
	if Input.is_action_pressed("w"):
		var force_multiplier = max(0.3, 1.0 - (current_speed / max_speed))
		var forward_force = -global_transform.basis.z * paddle_force * force_multiplier
		apply_central_force(forward_force)
		create_paddle_effect()
	
	if Input.is_action_pressed("s") and current_speed < 5.0:
		var backward_force = global_transform.basis.z * backward_paddle_force
		apply_central_force(backward_force)

func handle_steering():
	var turn_multiplier = clamp(current_speed / max_speed, 0.2, 1.0)
	
	if Input.is_action_pressed("a"):
		apply_torque(Vector3(0, turn_torque * turn_multiplier, 0))
		apply_torque(Vector3(turn_torque * 0.3 * turn_multiplier, 0, 0))
	
	if Input.is_action_pressed("d"):
		apply_torque(Vector3(0, -turn_torque * turn_multiplier, 0))
		apply_torque(Vector3(-turn_torque * 0.3 * turn_multiplier, 0, 0))

func stabilize_canoe():
	var current_rotation = rotation_degrees
	
	if abs(current_rotation.x) > 5:
		var stabilization = -rotation.x * stability_force
		apply_torque(Vector3(stabilization, 0, 0))
	
	if abs(current_rotation.z) > 10:
		var stabilization_z = -rotation.z * stability_force * 0.5
		apply_torque(Vector3(0, 0, stabilization_z))

func update_speed():
	current_speed = linear_velocity.length()

func limit_speed():
	if current_speed > max_speed:
		linear_velocity = linear_velocity.normalized() * max_speed

func create_paddle_effect():
	pass
