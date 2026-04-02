extends CharacterBody3D

@onready var cabeca: Node3D = $cabeca
@onready var camera_3d: Camera3D = $cabeca/Camera3D

const SPEED = 30.0
const JUMP_VELOCITY = 4.5
const MOUSE_SENSIBILITY: float = 0.0003

func _ready() :
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED) # tirar o ponteiro do mouse da tela

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		cabeca.rotate_y(-event.relative.x * MOUSE_SENSIBILITY)
		camera_3d.rotate_x(-event.relative.y * MOUSE_SENSIBILITY)
		camera_3d.rotation.x = clamp(camera_3d.rotation.x, deg_to_rad(-90), deg_to_rad(90))


func _physics_process(delta: float) -> void:
	# Add the gravity.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Handle jump.
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Get the input direction and handle the movement/deceleration.
	# As good practice, you should replace UI actions with custom gameplay actions.
	
	var input_dir : Vector2 = Input.get_vector("left", "right", "up", "down")
	var direction : Vector3 = (cabeca.transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	if direction:
		velocity.x = direction.x * SPEED
		velocity.z = direction.z * SPEED
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED)
		velocity.z = move_toward(velocity.z, 0, SPEED)

	move_and_slide()
