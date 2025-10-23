extends CharacterBody3D

#constantes
const SPEED = 15.0
const JUMP_VELOCITY = 6.0
const ACCELERATION = 2.0

#acesso a camera_pivo e camera para visão presa ao player
@onready var camera_pivo: Node3D = $camera_pivo
@onready var camera: Camera3D = $camera_pivo/camera

#acesso ao modelo e à animação
@onready var gobot: Node3D = $gobot
@onready var anim_player: AnimationPlayer = gobot.get_node("AnimationPlayer")

#acesso ao label para a contagem do hub
@onready var gear_container: HBoxContainer = $HUD/gear_container
var gears := 0

var mouse_sensitivity: float = 0.15
var camera_rotation: Vector2 = Vector2.ZERO
var last_moviment_dir := Vector3.BACK
var is_jumping

#sensibilidade do analógico
var joystick_sensitivity = 2.5

#funções
func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	anim_player.play("Idle")

func _unhandled_input(event: InputEvent) -> void:
	var is_camera_motion := (
		event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED
	)
	if is_camera_motion:
		camera_rotation = event.screen_relative * mouse_sensitivity

func  _input(_event: InputEvent) -> void:
	if Input.is_action_just_pressed("ui_cancel"):
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		
	if Input.is_action_just_pressed("left_click"):
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _physics_process(delta: float) -> void:
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
		velocity.y = JUMP_VELOCITY

	#movimentação padrão
	var input_dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var forward := camera.global_basis.z
	var right := camera.global_basis.x
	var direction := (forward * input_dir.y + right * input_dir.x).normalized()
	direction.y = 0.0
	
	var y_velocity = velocity.y
	velocity.y = 0.0
	
	if is_on_floor():
		if direction:
			velocity = velocity.move_toward(direction * SPEED, ACCELERATION * delta)
		else:
			velocity = velocity.move_toward(Vector3.ZERO, ACCELERATION * delta)
	
	velocity.y = y_velocity
	
	_handle_animation()
	move_and_slide()
	
	
	if direction.length() >0.1:
		last_moviment_dir = direction
	
	var target_angle := Vector3.BACK.signed_angle_to(last_moviment_dir, Vector3.UP)
	gobot.global_rotation.y = lerp_angle(gobot.global_rotation.y, target_angle, ACCELERATION * delta)

func _handle_animation():
	if not is_on_floor():
		if velocity.y > 0.1:
			if anim_player.current_animation != "Jump":
				anim_player.play("Jump", 0.2)
		elif velocity.y < -0.1:
			if anim_player.current_animation != "Fall":
				anim_player.play("Fall", 0.2)
	else:
		if velocity.length() > 0.1:
			if anim_player.current_animation != "Run":
				anim_player.play("Run", 0.2)
		else:
			if anim_player.current_animation != "Idle":
				anim_player.play("Idle", 0.2)


func collect_gear():
	gears += 1
	gear_container.update_gear(gears)
