extends CharacterBody3D

@export var target_path: NodePath
@export var chase_speed := 3.5
@export var acceleration := 10.0
@export var stopping_distance := 1.1
@export var damage := 1
@export var damage_interval := 1.2

@export_group("Desvio de obstáculos")
@export var avoidance_distance := 3.5
@export_range(30.0, 110.0, 1.0) var avoidance_angle := 70.0
@export var avoidance_commit_duration := 0.85
@export_flags_3d_physics var obstacle_collision_mask := 1

@onready var target: CharacterBody3D = get_node_or_null(target_path) as CharacterBody3D
@onready var animation_player: AnimationPlayer = find_child("AnimationPlayer", true, false) as AnimationPlayer

var player_in_hitbox: CharacterBody3D
var damage_cooldown := 0.0
var spawn_transform: Transform3D
var is_attacking := false
var preferred_avoidance_side := 1.0
var avoidance_commit_remaining := 0.0

func _ready() -> void:
	spawn_transform = global_transform

	if not target:
		target = get_tree().get_first_node_in_group("player") as CharacterBody3D

	if not target:
		push_warning("O tigre temporário não encontrou um jogador para perseguir.")
		set_physics_process(false)
		return

	_play_animation("walk")

func _physics_process(delta: float) -> void:
	damage_cooldown = maxf(damage_cooldown - delta, 0.0)
	avoidance_commit_remaining = maxf(avoidance_commit_remaining - delta, 0.0)
	_try_damage_player()

	if is_attacking:
		_slow_down(delta)
		if not is_on_floor():
			velocity += get_gravity() * delta
		move_and_slide()
		return

	if not is_instance_valid(target) or target.get("is_dead"):
		_slow_down(delta)
		_play_animation("idle")
		move_and_slide()
		return

	if not is_on_floor():
		velocity += get_gravity() * delta

	var offset := target.global_position - global_position
	offset.y = 0.0
	var distance := offset.length()

	if distance > stopping_distance:
		var desired_direction := offset.normalized()
		var direction := _get_avoidance_direction(desired_direction)
		velocity.x = move_toward(velocity.x, direction.x * chase_speed, acceleration * delta)
		velocity.z = move_toward(velocity.z, direction.z * chase_speed, acceleration * delta)

		var look_target := global_position + direction
		if global_position.distance_squared_to(look_target) > 0.001:
			look_at(look_target, Vector3.UP)
	else:
		_slow_down(delta)

	move_and_slide()
	_update_movement_animation()

func _slow_down(delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0.0, acceleration * delta)
	velocity.z = move_toward(velocity.z, 0.0, acceleration * delta)

func _get_avoidance_direction(desired_direction: Vector3) -> Vector3:
	if avoidance_distance <= 0.0:
		return desired_direction

	if avoidance_commit_remaining > 0.0:
		return desired_direction.rotated(
			Vector3.UP,
			deg_to_rad(avoidance_angle * preferred_avoidance_side)
		).normalized()

	if _get_direction_clearance(desired_direction) >= 0.98:
		return desired_direction

	var left_direction := desired_direction.rotated(Vector3.UP, deg_to_rad(avoidance_angle)).normalized()
	var right_direction := desired_direction.rotated(Vector3.UP, deg_to_rad(-avoidance_angle)).normalized()
	var left_clearance := _get_direction_clearance(left_direction)
	var right_clearance := _get_direction_clearance(right_direction)

	if not is_equal_approx(left_clearance, right_clearance):
		preferred_avoidance_side = 1.0 if left_clearance > right_clearance else -1.0

	avoidance_commit_remaining = avoidance_commit_duration
	return left_direction if preferred_avoidance_side > 0.0 else right_direction

func _get_direction_clearance(direction: Vector3) -> float:
	var space_state := get_world_3d().direct_space_state
	var lowest_clearance := 1.0
	var excluded_bodies: Array[RID] = [get_rid()]
	if is_instance_valid(target):
		excluded_bodies.append(target.get_rid())

	for ray_height: float in [0.35, 1.0]:
		var origin := global_position + Vector3.UP * ray_height
		var destination := origin + direction * avoidance_distance
		var query := PhysicsRayQueryParameters3D.create(
			origin,
			destination,
			obstacle_collision_mask,
			excluded_bodies
		)
		query.collide_with_areas = false
		var collision := space_state.intersect_ray(query)
		if collision:
			var hit_position: Vector3 = collision["position"]
			var clearance := origin.distance_to(hit_position) / avoidance_distance
			lowest_clearance = minf(lowest_clearance, clearance)

	return lowest_clearance

func _on_hitbox_body_entered(body: Node3D) -> void:
	if body is CharacterBody3D and body.is_in_group("player"):
		player_in_hitbox = body
		_try_damage_player()

func _on_hitbox_body_exited(body: Node3D) -> void:
	if body == player_in_hitbox:
		player_in_hitbox = null

func _try_damage_player() -> void:
	if is_attacking or damage_cooldown > 0.0 or not is_instance_valid(player_in_hitbox):
		return
	if not player_in_hitbox.has_method("take_damage"):
		return
	if player_in_hitbox.get("is_dead") or player_in_hitbox.get("is_invulnerable"):
		return

	is_attacking = true
	damage_cooldown = damage_interval
	_attack_player(player_in_hitbox)

func _attack_player(player: CharacterBody3D) -> void:
	velocity.x = 0.0
	velocity.z = 0.0

	if _play_animation("headbutt", true):
		await animation_player.animation_finished
	else:
		await get_tree().create_timer(0.35).timeout

	if is_instance_valid(player) and not player.get("is_dead") and not player.get("is_invulnerable"):
		player.take_damage(damage)
		reset_to_spawn()

	is_attacking = false
	if is_instance_valid(target) and not target.get("is_dead"):
		_play_animation("walk", true)
	else:
		_play_animation("idle", true)

func reset_to_spawn() -> void:
	global_transform = spawn_transform
	velocity = Vector3.ZERO
	player_in_hitbox = null
	avoidance_commit_remaining = 0.0

func _update_movement_animation() -> void:
	var horizontal_speed := Vector2(velocity.x, velocity.z).length()
	if horizontal_speed > 0.1:
		_play_animation("walk")
	else:
		_play_animation("idle")

func _play_animation(animation_name: StringName, restart := false) -> bool:
	if not animation_player or not animation_player.has_animation(animation_name):
		return false
	if restart or animation_player.current_animation != animation_name or not animation_player.is_playing():
		animation_player.play(animation_name)
	return true
