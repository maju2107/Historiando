extends Node3D
## Kai's cutscene actor. Clips are skinned/baked from the editable Kai source.
var animator: AnimationPlayer
var skeleton: Skeleton3D
var last_gesture := "Idle"
var gesture_count := 0
var face: Node

func _ready() -> void:
	animator = find_child("AnimationPlayer",true,false) as AnimationPlayer
	skeleton = find_child("Skeleton3D",true,false) as Skeleton3D
	if animator == null or skeleton == null:
		push_error("Kai's imported skin is missing its rig or animations.")
		return
	for clip in ["Idle","Walk","Run","Talk"]:
		if animator.has_animation(clip): animator.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	animator.animation_finished.connect(_on_animation_finished)
	play_gesture("Idle")
	face = preload("res://assets/characters/FacialAnimator.gd").new()
	face.name = "FacialPerformance"
	add_child(face)
	face.configure(self)

func play_gesture(clip: String, speed := 1.0) -> void:
	if animator == null or not animator.has_animation(clip): return
	last_gesture = clip
	gesture_count += 1
	animator.speed_scale = speed
	animator.play(clip,.22)

func face_position(target: Vector3) -> void:
	var flat := Vector3(target.x,global_position.y,target.z)
	if global_position.distance_squared_to(flat) > .001:
		look_at(flat,Vector3.UP,true)

func _on_animation_finished(clip: StringName) -> void:
	if clip not in [&"Idle",&"Walk",&"Run",&"Talk"]: play_gesture("Idle")
