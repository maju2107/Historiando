extends SceneTree

var failures: Array[String] = []
var report: Dictionary = {"clips": {}, "checks": []}

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool, label: String) -> void:
	report["checks"].append({"check": label, "passed": condition})
	if not condition:
		failures.append(label)
		printerr("YARA_HAIR_FAILED: ", label)

func _run() -> void:
	var model := (load("res://assets/characters/yara/YaraSkin.tscn") as PackedScene).instantiate() as Node3D
	model.scale = Vector3.ONE * 1.25
	root.add_child(model)
	var skeleton := model.find_child("Skeleton3D", true, false) as Skeleton3D
	var hair := skeleton.get_node_or_null("PonytailPhysics") as SkeletonModifier3D
	check(hair != null, "Physics is installed automatically on playable Yara")
	if hair == null:
		_finish()
		return
	check(skeleton.get_bone_count() == 60, "Three ponytail bones imported")
	var animator := model.get_node("AnimationPlayer") as AnimationPlayer
	# Deterministic simulation of the same modifier after animation at 60 Hz.
	hair.active = false
	animator.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var indices: Array[int] = []
	for name in ["Ponytail.1", "Ponytail.2", "Ponytail.3"]:
		indices.append(skeleton.find_bone(name))
	for clip in ["Idle", "Walk", "Run", "Jump", "Fall", "Flip", "VictorySign", "EdgeGrab", "WallSlide"]:
		hair.call("reset_motion")
		animator.play(clip, 0)
		animator.advance(0)
		var clip_bases: Array[Quaternion] = []
		for bone in indices:
			clip_bases.append(skeleton.get_bone_pose_rotation(bone))
		model.position = Vector3.ZERO
		model.rotation = Vector3.ZERO
		var maximum := 0.0
		var finite := true
		var head_unchanged := true
		for frame in 180:
			var t := frame / 60.0
			# Exercise acceleration, stopping, turns and a jump/landing impulse.
			model.position.x = 0.10 * sin(t * 3.0)
			model.rotation.y = 0.16 * sin(t * 2.0)
			if clip == "Jump" or clip == "Fall":
				model.position.y = maxf(0, sin(t * PI)) * 0.25
			for i in indices.size():
				skeleton.set_bone_pose_rotation(indices[i], clip_bases[i])
			animator.advance(1.0 / 60.0)
			var bases: Array[Quaternion] = []
			for bone in indices:
				bases.append(skeleton.get_bone_pose_rotation(bone))
			var head_before := skeleton.get_bone_global_pose(skeleton.find_bone("Head"))
			hair.call("_process_modification_with_delta", 1.0 / 60.0)
			head_unchanged = head_unchanged and head_before.is_equal_approx(skeleton.get_bone_global_pose(skeleton.find_bone("Head")))
			for i in indices.size():
				var rotation := skeleton.get_bone_pose_rotation(indices[i])
				finite = finite and rotation.is_finite()
				maximum = maxf(maximum, bases[i].angle_to(rotation))
		check(finite and maximum < 0.16, clip + " stays finite and within angular limits")
		check(maximum > 0.001, clip + " has secondary motion")
		check(head_unchanged, clip + " keeps head and tie anchored")
		report["clips"][clip] = {"maximum_joint_rotation_degrees": rad_to_deg(maximum), "finite": finite, "head_unchanged": head_unchanged}
	# Settling and pause / teleport protection.
	model.position = Vector3.ZERO
	model.rotation = Vector3.ZERO
	animator.play("Idle", 0)
	animator.seek(0, true)
	animator.pause()
	var resting_bases: Array[Quaternion] = []
	for bone in indices:
		resting_bases.append(skeleton.get_bone_pose_rotation(bone))
	for frame in 360:
		for i in indices.size():
			skeleton.set_bone_pose_rotation(indices[i], resting_bases[i])
		hair.call("_process_modification_with_delta", 1.0 / 60.0)
	var resting := 0.0
	for i in indices.size():
		resting = maxf(resting, resting_bases[i].angle_to(skeleton.get_bone_pose_rotation(indices[i])))
	check(resting < 0.002, "Hair settles at rest")
	# Turning without translation must still produce inertial lag.
	hair.call("reset_motion")
	var turning_motion := 0.0
	for frame in 90:
		model.rotation.y = 0.7 * sin(frame / 60.0 * 4.0)
		for i in indices.size():
			skeleton.set_bone_pose_rotation(indices[i], resting_bases[i])
		hair.call("_process_modification_with_delta", 1.0 / 60.0)
		turning_motion = maxf(turning_motion, resting_bases[0].angle_to(skeleton.get_bone_pose_rotation(indices[0])))
	check(turning_motion > 0.01 and turning_motion < 0.16, "Turning in place produces bounded hair lag")
	report["turning_motion_degrees"] = rad_to_deg(turning_motion)
	model.position = Vector3(20, 10, -20)
	hair.call("_process_modification_with_delta", 1.0 / 60.0)
	var angles: Array = hair.get("_angles")
	check(angles[0].length() < 0.0001, "Teleport resets the spring")
	# Confirm engine schedules the modifier after animation, rather than only manual tests.
	hair.active = true
	animator.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE
	animator.play("Walk", 0)
	animator.advance(0)
	var engine_baseline := skeleton.get_bone_pose_rotation(indices[0])
	var observed := [0.0]
	hair.modification_processed.connect(func():
		observed[0] = maxf(observed[0], engine_baseline.angle_to(skeleton.get_bone_pose_rotation(indices[0]))))
	for frame in 60:
		await process_frame
	check(observed[0] > 0.001 and observed[0] < 0.16, "Engine applies bounded spring physics after animation")
	report["engine_motion_degrees"] = rad_to_deg(observed[0])
	model.queue_free()
	await process_frame
	_finish()

func _finish() -> void:
	report["issues"] = failures
	var file := FileAccess.open("res://art/yara/validation/hair_physics_validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	print("YARA_HAIR_VALIDATION ", JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)
