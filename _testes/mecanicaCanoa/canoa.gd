extends RigidBody3D

# Sistema de câmera
var mouse_movement = Vector2()
@export var mouse_sensitivity = 0.5

# Física da canoa
@export var paddle_force = 300.0
@export var backward_paddle_force = 150.0
@export var turn_torque = 500.0
@export var max_speed = 22.0
@export var water_resistance = 0.96
@export var stability_force = 800.0

# Sistema de flutuação
@export var water_height = 0.0
@export var buoyancy_strength = 15.0
@export var buoyancy_damping = 5.0
@export var water_drag = 3.0

# NOVOS PARÂMETROS PARA ESTABILIDADE EM CURVAS
@export var anti_roll_strength = 2500.0  # Força anti-tombamento (aumentado)
@export var turn_stability = 2.0  # Reduz inclinação em curvas (0.0 a 1.0)
@export var max_roll_angle = 3.0  # Ângulo máximo de inclinação (graus)
@export var center_of_mass_offset = -0.5  # Centro de massa mais baixo
@export var torque_reduction_speed = 9.0  # Velocidade a partir da qual reduz torque

var current_speed = 0.0
var float_points = []
var water_level = 0.0
var current_roll = 0.0  # Inclinação atual

func _ready():
	# Configuração da câmera
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	
	# Configuração física da canoa
	mass = 50.0
	center_of_mass = Vector3(0, center_of_mass_offset, 0)  # Centro de massa mais baixo
	set_linear_damp(water_resistance)
	set_angular_damp(0.98)
	
	# Aumenta o momento de inércia para mais estabilidade
	set_inertia(Vector3(15, 25, 15))  # Mais resistência à rotação
	
	# Criar pontos de flutuação para a canoa
	setup_buoyancy_points()

func setup_buoyancy_points():
	# Pontos onde a flutuação será calculada
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
		mouse_movement += event.relative * mouse_sensitivity

func _physics_process(delta):
	# Atualiza inclinação atual
	current_roll = rad_to_deg(rotation.x)
	
	# Sistema de câmera
	if mouse_movement != Vector2():
		$H.rotation_degrees.y += -mouse_movement.x
		$H/V.rotation_degrees.x += -mouse_movement.y
		if $H/V.rotation_degrees.x <= -90:
			$H/V.rotation_degrees.x = -90
		if $H/V.rotation_degrees.x >= 0:
			$H/V.rotation_degrees.x = 0
		mouse_movement = Vector2()
	
	# Sistema de flutuação
	apply_buoyancy(delta)
	
	# Movimento da canoa
	handle_paddling()
	handle_steering(delta)  # Passa delta para o steering
	stabilize_canoe(delta)  # Passa delta para estabilização
	update_speed()
	limit_speed()
	
	# Aplicar arrasto extra na água
	apply_water_drag(delta)

func apply_buoyancy(delta):
	# Aplica força de flutuação em vários pontos da canoa
	for point in float_points:
		var global_point = to_global(point)
		
		if global_point.y < water_height:
			var depth = water_height - global_point.y
			
			# Força de flutuação base
			var force = depth * buoyancy_strength * mass
			force = clampf(force, 0.0, 75.0)
			
			# ADICIONADO: Estabilidade extra em curvas
			if abs(current_roll) > 5:
				# Aumenta flutuação no lado que está afundando
				var side_factor = 1.0
				if point.x < 0 and current_roll < 0:  # Lado esquerdo afundando
					side_factor = 1.0 + (abs(current_roll) / max_roll_angle)
				elif point.x > 0 and current_roll > 0:  # Lado direito afundando
					side_factor = 1.0 + (abs(current_roll) / max_roll_angle)
				force *= side_factor
			
			# Adiciona amortecimento para evitar oscilações
			var velocity_at_point = get_velocity_at_point(global_point)
			var damping_force = -velocity_at_point.y * buoyancy_damping
			
			# Aplica a força no ponto específico
			apply_force(Vector3(0, force + damping_force, 0), point)
			
			debug_buoyancy_point(global_point, depth)

func get_velocity_at_point(point):
	var linear_vel = linear_velocity
	var angular_vel = angular_velocity
	var r = point - global_transform.origin
	return linear_vel + angular_vel.cross(r)

func calculate_drag(velocity: float, area: float):
	return 1.0 * 1.0 * velocity * velocity * area

func apply_water_drag(delta):
	var submerged_parts = 0
	
	for point in float_points:
		var global_point = to_global(point)
		if global_point.y < water_height:
			submerged_parts += 1
	
	if submerged_parts > 0:
		var submersion_ratio = (float(submerged_parts) / float_points.size())
		var drag_linear_velocity = calculate_drag(linear_velocity.length(), 2.0) / mass
		var angular_speed = angular_velocity.length()
			
		if angular_speed > 0.001:
			var drag = calculate_drag(angular_speed, 5.0) / mass
			angular_velocity *= 1.0 / (1.0 + drag * delta)
			angular_damp = 20.0

func debug_buoyancy_point(point, depth):
	if Engine.is_editor_hint():
		return
	# Você pode adicionar um MeshInstance3D pequeno ou partículas aqui
	pass

func handle_paddling():
	current_speed = linear_velocity.length()
	
	if Input.is_action_pressed("ui_up"):
		var force_multiplier = max(0.3, 1.0 - (current_speed / max_speed))
		var forward_force = -global_transform.basis.z * paddle_force * force_multiplier
		apply_central_force(forward_force)
		create_paddle_effect()
	
	if Input.is_action_pressed("ui_down") and current_speed < 5.0:
		var backward_force = global_transform.basis.z * backward_paddle_force
		apply_central_force(backward_force)

func handle_steering(delta):
	var turn_multiplier = clamp(current_speed / max_speed, 0.2, 1.0)
	
	# NOVO: Reduz torque em altas velocidades
	var torque_reduction = 1.0
	if current_speed > torque_reduction_speed:
		# Reduz gradualmente o torque acima da velocidade definida
		torque_reduction = lerp(1.0, 0.4, (current_speed - torque_reduction_speed) / (max_speed - torque_reduction_speed))
	
	if Input.is_action_pressed("ui_left"):
		# Aplica torque de direção reduzido
		var torque = turn_torque * turn_multiplier * torque_reduction
		apply_torque(Vector3(0, torque, 0))
		
		# NOVO: Inclinação controlada para curvas
		# Em vez de aplicar torque de inclinação, aplicamos força anti-tombamento
		var target_roll = -turn_torque * turn_multiplier * turn_stability * 0.3
		var roll_correction = (target_roll - rotation.x) * anti_roll_strength * delta
		apply_torque(Vector3(roll_correction, 0, 0))
		
		# NOVO: Reduz força centrífuga
		if current_speed > 3.0:
			var centrifugal_force = current_speed * turn_multiplier * (1.0 - turn_stability) * 30.0
			apply_central_force(global_transform.basis.x * -centrifugal_force)
	
	if Input.is_action_pressed("ui_right"):
		# Aplica torque de direção reduzido
		var torque = -turn_torque * turn_multiplier * torque_reduction
		apply_torque(Vector3(0, torque, 0))
		
		# Inclinação controlada para curvas à direita
		var target_roll = turn_torque * turn_multiplier * turn_stability * 0.3
		var roll_correction = (target_roll - rotation.x) * anti_roll_strength * delta
		apply_torque(Vector3(roll_correction, 0, 0))
		
		# Reduz força centrífuga
		if current_speed > 3.0:
			var centrifugal_force = current_speed * turn_multiplier * (1.0 - turn_stability) * 30.0
			apply_central_force(global_transform.basis.x * centrifugal_force)

func stabilize_canoe(delta):
	var current_rotation = rotation_degrees
	
	# MELHORADO: Estabilidade muito mais forte
	if abs(current_rotation.x) > 3:
		# Força de correção exponencial (mais forte quanto mais inclinado)
		var angle_factor = abs(current_rotation.x) / max_roll_angle
		var correction_strength = anti_roll_strength * (1.0 + angle_factor * 2.0)
		
		var stabilization = -rotation.x * correction_strength
		apply_torque(Vector3(stabilization, 0, 0))
		
		# Debug: Mostra quando está corrigindo inclinação severa
		if abs(current_rotation.x) > max_roll_angle:
			print("Corrigindo inclinação severa: ", current_rotation.x)
	
	# Estabilização longitudinal
	if abs(current_rotation.z) > 10:
		var stabilization_z = -rotation.z * stability_force * 0.5
		apply_torque(Vector3(0, 0, stabilization_z))
	
	# NOVO: Limita rotação máxima para evitar capotamento
	var new_rotation = rotation
	new_rotation.x = clamp(rotation.x, deg_to_rad(-max_roll_angle), deg_to_rad(max_roll_angle))
	new_rotation.z = clamp(rotation.z, deg_to_rad(-15), deg_to_rad(15))
	rotation = new_rotation

func update_speed():
	current_speed = linear_velocity.length()

func limit_speed():
	if current_speed > max_speed:
		linear_velocity = linear_velocity.normalized() * max_speed

func create_paddle_effect():
	pass
