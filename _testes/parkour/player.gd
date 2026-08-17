extends CharacterBody3D

#constantes
@export_category("Movimento")
@export var walk_speed := 7.0
@export var run_speed := 11.0
@export var jump_velocity := 6.5
@export var model_turn_speed := 10.0



#acesso a camera_pivo e camera para visão presa ao player
@onready var camera_pivo: Node3D = $camera_pivo
@onready var camera: Camera3D = $camera_pivo/camera

#acesso ao modelo e à animação
@onready var gobot: Node3D = $gobot
@onready var anim_player: AnimationPlayer = gobot.get_node("AnimationPlayer")

#acesso ao label para a contagem do hub
@onready var gear_container: HBoxContainer = get_node_or_null("HUD/gear_container")
var gears := 0

#posição inicial
@onready var player_start_position := global_transform.origin
var can_move := true

#sitema de vida
@export var invulnerability_duration := 1.0
var health := 3
var is_dead := false
var is_invulnerable := false

#sencibilidade do mouse/rotação da camera
var mouse_sensitivity: float = 0.15
var camera_rotation: Vector2 = Vector2.ZERO
var last_moviment_dir := Vector3.BACK
var is_jumping := false

#sensibilidade do analógico
var joystick_sensitivity = 2.5

#funções
func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	anim_player.play("Idle")
	if not gear_container:
		push_warning("O HUD do jogador não foi encontrado; a contagem ficará desativada.")
	_update_life_hud()

func _unhandled_input(event: InputEvent) -> void:
	var is_camera_motion := (
		event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED
	)
	if is_camera_motion:
		camera_rotation += event.screen_relative * mouse_sensitivity
	

func  _input(event: InputEvent) -> void:
	if Input.is_action_just_pressed("ui_cancel"):
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		
		
	if Input.is_action_just_pressed("left_click"):
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _physics_process(delta: float) -> void:
	if not can_move or is_dead:
		return

	# rotação da camera
	
	#leitura do analógico direito
	var joy_x = Input.get_joy_axis(0, JOY_AXIS_RIGHT_X) # eixo horizontal
	var joy_y = Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y) # eixo vertical

	#atualiza rotação da câmera com joystick
	camera_rotation.x += joy_x * joystick_sensitivity
	camera_rotation.y += joy_y * joystick_sensitivity
	
	#rotação com o mouse
	camera_pivo.rotation.x += camera_rotation.y * delta
	camera_pivo.rotation.x = clamp(camera_pivo.rotation.x, deg_to_rad(-75), deg_to_rad(20))
	camera_pivo.rotation.y -= camera_rotation.x * delta
	
	camera_rotation = Vector2.ZERO
	
	#gravidade
	if not is_on_floor():
		velocity += get_gravity() * delta
		
	is_jumping = Input.is_action_just_pressed("ui_accept") and is_on_floor()

	#pulo
	if is_jumping:
		velocity.y = jump_velocity

	#movimentação padrão
	var input_dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var forward := camera.global_basis.z
	var right := camera.global_basis.x
	forward.y = 0.0
	right.y = 0.0
	forward = forward.normalized()
	right = right.normalized()
	var direction := forward * input_dir.y + right * input_dir.x
	direction.y = 0.0
	direction = direction.normalized()

	var is_running := Input.is_action_pressed("sprint")
	var movement_speed := run_speed if is_running else walk_speed
	
	if is_on_floor():
		velocity.x = direction.x * movement_speed
		velocity.z = direction.z * movement_speed
	
	_handle_animation(is_running)
	move_and_slide()
	
	
	if direction.length() >0.1:
		last_moviment_dir = direction
	
	var target_angle := Vector3.BACK.signed_angle_to(last_moviment_dir, Vector3.UP)
	gobot.global_rotation.y = lerp_angle(
		gobot.global_rotation.y,
		target_angle,
		minf(model_turn_speed * delta, 1.0)
	)

func _handle_animation(is_running: bool) -> void:
	if not is_on_floor():
		if velocity.y > 0.1:
			if anim_player.current_animation != "Jump":
				anim_player.play("Jump", 0.2)
		elif velocity.y < -0.1:
			if anim_player.current_animation != "Fall":
				anim_player.play("Fall", 0.2)
	else:
		var is_moving := Vector2(velocity.x, velocity.z).length() > 0.1
		if is_moving:
			var movement_animation := "Run" if is_running else "Walk"
			if anim_player.current_animation != movement_animation:
				anim_player.play(movement_animation, 0.15)
		else:
			if anim_player.current_animation != "Idle":
				anim_player.play("Idle", 0.2)

func collect_gear():
	gears += 1
	if gear_container and gear_container.has_method("update_gear"):
		gear_container.update_gear(gears)
	

func take_damage(amount: int = 1) -> void:
	if amount <= 0 or is_dead or is_invulnerable:
		return

	is_invulnerable = true
	health = maxi(health - amount, 0)
	_update_life_hud()

	global_position = player_start_position
	velocity = Vector3.ZERO
	anim_player.play("Idle", 0.0)

	if health == 0:
		_die()
		return

	can_move = false

	await get_tree().create_timer(0.5).timeout
	can_move = true

	var remaining_invulnerability := maxf(invulnerability_duration - 0.5, 0.0)
	if remaining_invulnerability > 0.0:
		await get_tree().create_timer(remaining_invulnerability).timeout
	is_invulnerable = false

func respawn_player() -> void:
	take_damage(1)

func _update_life_hud() -> void:
	if gear_container and gear_container.has_method("update_life"):
		gear_container.update_life(health)

func _die() -> void:
	is_dead = true
	can_move = false
	velocity = Vector3.ZERO
	set_physics_process(false)

	var game_over_ui := get_parent().get_node_or_null("GameOver")
	if game_over_ui:
		game_over_ui.show()
	else:
		push_warning("A interface GameOver não foi encontrada na cena.")
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		
		


	
