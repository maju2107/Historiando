extends SceneTree
var player
var frames := 0
var initial_direction := Vector3.ZERO
var previous_yaw := 0.0
func _initialize():
	call_deferred("setup")
func setup():
	player = load("res://_testes/parkour/Player.tscn").instantiate()
	player.follow_behind = true
	root.add_child(player)
	previous_yaw = player.camera_pivo.global_rotation.y
	Input.action_press("ui_right")
func _physics_process(_delta):
	if player == null:
		return false
	frames += 1
	if frames == 3:
		initial_direction = player.last_moviment_dir
	if frames > 3:
		assert(player.last_moviment_dir.dot(initial_direction) > 0.999, "Held direction drifted")
		var behind = player.camera.global_position - player.global_position
		behind.y = 0
		var yaw: float = player.camera_pivo.global_rotation.y
		assert(absf(wrapf(yaw - previous_yaw, -PI, PI)) < 0.12, "Camera turned abruptly")
		previous_yaw = yaw
		if frames > 110:
			assert(behind.normalized().dot(player.gobot.global_basis.z) < -0.999, "Camera did not settle behind player")
		assert(absf(player.camera_pivo.rotation.x - deg_to_rad(-18)) < 0.001)
	if frames == 120:
		Input.action_release("ui_right")
		print("CAMERA_OK: smooth rotation, fixed pitch, settles behind player, no held-input drift")
		player.queue_free()
		quit()
	return false

