extends SkeletonModifier3D
## Damped secondary motion after animation. Only the painted ponytail is affected.
## Angular limits keep the broad cartoon hair away from the face and torso.

@export_range(0.0, 2.0) var motion_strength: float = 1.0
@export_range(0.5, 3.0) var settling_speed: float = 1.0

const HAIR_BONES: Array[String] = ["Ponytail.1", "Ponytail.2", "Ponytail.3"]
var _bones: Array[int] = []
var _angles: Array[Vector2] = [Vector2.ZERO, Vector2.ZERO, Vector2.ZERO]
var _speeds: Array[Vector2] = [Vector2.ZERO, Vector2.ZERO, Vector2.ZERO]
var _head: int = -1
var _head_rest: Basis
var _animator: AnimationPlayer
var _previous_position := Vector3.ZERO
var _previous_velocity := Vector3.ZERO
var _previous_basis := Basis.IDENTITY
var _filtered_acceleration := Vector3.ZERO
var _initialized := false
var _configured := false


func _ready() -> void:
	var skeleton := get_skeleton()
	if skeleton == null:
		return
	_head = skeleton.find_bone("Head")
	if _head < 0:
		return
	_head_rest = skeleton.get_bone_global_rest(_head).basis.orthonormalized()
	for bone_name in HAIR_BONES:
		var bone := skeleton.find_bone(bone_name)
		if bone < 0:
			push_error("Yara hair bone is missing: " + bone_name)
			return
		_bones.append(bone)
	var ancestor: Node = skeleton
	while ancestor != null:
		_animator = ancestor.get_node_or_null("AnimationPlayer") as AnimationPlayer
		if _animator != null:
			break
		ancestor = ancestor.get_parent()
	_configured = true


func reset_motion() -> void:
	_initialized = false
	_filtered_acceleration = Vector3.ZERO
	for i in 3:
		_angles[i] = Vector2.ZERO
		_speeds[i] = Vector2.ZERO


func _process_modification_with_delta(delta: float) -> void:
	if not _configured or delta <= 0.0:
		return
	var skeleton := get_skeleton()
	var head_pose := skeleton.get_bone_global_pose(_head)
	var head_position := skeleton.global_transform * head_pose.origin
	# Convert the imported bone axes to the character's anatomical axes.
	var head_basis := (skeleton.global_basis.orthonormalized() * head_pose.basis.orthonormalized() * _head_rest.inverse()).orthonormalized()
	if not _initialized or delta > 0.25 or head_position.distance_to(_previous_position) > 2.0:
		reset_motion()
		_previous_position = head_position
		_previous_velocity = Vector3.ZERO
		_previous_basis = head_basis
		_initialized = true
		return
	var dt := minf(delta, 1.0 / 15.0)
	var velocity := (head_position - _previous_position) / delta
	var acceleration := ((velocity - _previous_velocity) / delta).limit_length(120.0)
	_filtered_acceleration = _filtered_acceleration.lerp(acceleration, 1.0 - exp(-12.0 * dt))
	var local_force := head_basis.inverse() * (-_filtered_acceleration - velocity * 0.35)
	var gravity := head_basis.inverse() * Vector3.DOWN
	var angular_velocity := (_previous_basis.inverse() * head_basis).get_rotation_quaternion().get_euler() / delta
	_previous_position = head_position
	_previous_velocity = velocity
	_previous_basis = head_basis
	var target := Vector2(-local_force.z * 0.0025 - gravity.z * 0.08 + angular_velocity.x * 0.018, local_force.x * 0.0025 + gravity.x * 0.08 - angular_velocity.z * 0.018 + angular_velocity.y * 0.02)
	# A small step impulse complements real head acceleration at steady speed.
	# The spring filters it continuously across clips instead of snapping poses.
	if _animator != null and _animator.is_playing():
		var clip := _animator.current_animation
		if clip == "Walk" or clip == "Run":
			var duration := _animator.current_animation_length
			var phase := TAU * _animator.current_animation_position / maxf(duration, 0.001)
			var amplitude := 0.023 if clip == "Walk" else 0.038
			target += Vector2(sin(phase * 2.0) * amplitude * 0.45, sin(phase) * amplitude)
	target *= motion_strength
	target.x = clampf(target.x, -0.035, 0.10)
	target.y = clampf(target.y, -0.065, 0.065)
	var steps := maxi(1, ceili(dt * 120.0))
	var step := dt / steps
	for substep in steps:
		for i in 3:
			var drive := target * (1.0 + i * 0.12)
			if i > 0:
				drive = drive.lerp(_angles[i - 1], 0.5)
			var omega := (22.0 - i * 3.5) * settling_speed
			_speeds[i] += (omega * omega * (drive - _angles[i]) - 2.0 * 0.78 * omega * _speeds[i]) * step
			_angles[i] += _speeds[i] * step
			_angles[i].x = clampf(_angles[i].x, -0.04, 0.11)
			_angles[i].y = clampf(_angles[i].y, -0.075, 0.075)
	for i in 3:
		# Use animated bone axes: glTF may encode its bind orientation in the pose.
		var inverse_pose := skeleton.get_bone_global_pose(_bones[i]).basis.orthonormalized().inverse()
		var head_axes := head_pose.basis.orthonormalized() * _head_rest.inverse()
		var pitch := Quaternion((inverse_pose * head_axes * Vector3.RIGHT).normalized(), _angles[i].x)
		var sway := Quaternion((inverse_pose * head_axes * Vector3.BACK).normalized(), _angles[i].y)
		var animated := skeleton.get_bone_pose_rotation(_bones[i])
		skeleton.set_bone_pose_rotation(_bones[i], (animated * pitch * sway).normalized())
