extends Node
## Local pose overlay for this cutscene; leaves existing locomotion clips intact.
var model: Node3D
var skeleton: Skeleton3D
var animator: AnimationPlayer
var _original_position: Vector3
var _rest := {}
var seated := 1.0
var nod := 0.0
var blink := 0.0
var _eyes: Array[Dictionary] = []
var _lashes: Array[Dictionary] = []
var _original_meshes: Array[Dictionary] = []

func configure(character: Node3D) -> void:
	model = character
	skeleton = model.find_child("Skeleton3D",true,false)
	animator = model.get_node("AnimationPlayer")
	_original_position = model.position
	animator.play("Idle")
	animator.advance(0)
	animator.pause()
	for bone in ["Body","Hips","Spine","Chest","Neck","Head","UpperLeg.L","UpperLeg.R","LowerLeg.L","LowerLeg.R","Foot.L","Foot.R","UpperArm.L","UpperArm.R","LowerArm.L","LowerArm.R"]:
		var index := skeleton.find_bone(bone)
		_rest[bone] = {"index":index,"rotation":skeleton.get_bone_pose_rotation(index)}
	for skin: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		var bounds := {}
		for surface in skin.mesh.get_surface_count():
			var original := skin.get_active_material(surface) as StandardMaterial3D
			if original == null or not "cartoon eye" in original.resource_name.to_lower(): continue
			var vertices: PackedVector3Array = skin.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var lo := Vector2(INF,INF)
			var hi := Vector2(-INF,-INF)
			for vertex in vertices:
				lo = lo.min(Vector2(vertex.x,vertex.y)); hi = hi.max(Vector2(vertex.x,vertex.y))
			bounds["L" if original.resource_name.ends_with(".L") else "R"] = Rect2(lo,hi-lo)
		if bounds.is_empty(): continue
		var source := skin.mesh
		var posed_mesh := ArrayMesh.new()
		for surface in source.get_surface_count():
			var original := skin.get_active_material(surface) as StandardMaterial3D
			var arrays := source.surface_get_arrays(surface)
			var is_eye := original != null and "cartoon eye" in original.resource_name.to_lower()
			var is_lash := original != null and "chr_eyebrow" in original.resource_name.to_lower()
			if is_eye or is_lash:
				var box: Rect2 = bounds["L" if original.resource_name.ends_with(".L") else "R"]
				var coordinates := PackedVector2Array()
				for vertex: Vector3 in arrays[Mesh.ARRAY_VERTEX]:
					coordinates.append((Vector2(vertex.x,vertex.y)-box.position)/box.size)
				arrays[Mesh.ARRAY_TEX_UV2] = coordinates
				var shader := ShaderMaterial.new()
				shader.shader = preload("res://_testes/cenario_ilha/intro/eye_blink.gdshader") if is_eye else preload("res://_testes/cenario_ilha/intro/eyelash_blink.gdshader")
				shader.set_shader_parameter("eye_texture",original.albedo_texture)
				shader.set_shader_parameter("eye_tint",original.albedo_color)
				var record := {"mesh":skin,"surface":surface,"original":skin.get_surface_override_material(surface),"shader":shader}
				if is_eye: _eyes.append(record)
				else:
					shader.set_shader_parameter("eye_height",box.size.y)
					_lashes.append(record)
				skin.set_surface_override_material(surface,shader)
			posed_mesh.add_surface_from_arrays(source.surface_get_primitive_type(surface),arrays)
			posed_mesh.surface_set_material(surface,source.surface_get_material(surface))
		_original_meshes.append({"mesh":skin,"original":source})
		skin.mesh = posed_mesh
	apply_pose()

func _rotate(bone: String, axis: Vector3, angle: float) -> void:
	var data: Dictionary = _rest[bone]
	skeleton.set_bone_pose_rotation(data.index,data.rotation * Quaternion(axis,angle))

func _seat_rotation(bone: String,offset: Quaternion) -> void:
	var data: Dictionary = _rest[bone]
	# Idle contains asymmetric leg motion; build the sitting pose from the bind rig.
	var target := skeleton.get_bone_rest(data.index).basis.get_rotation_quaternion()*offset
	skeleton.set_bone_pose_rotation(data.index,data.rotation.slerp(target,seated))

func apply_pose() -> void:
	if skeleton == null: return
	for eye in _eyes: eye.shader.set_shader_parameter("blink",blink)
	# Ground sitting: hips down, legs extended in a relaxed V, rather than a squat.
	model.position = _original_position + Vector3.DOWN * .44 * seated
	_seat_rotation("Body",Quaternion.IDENTITY)
	_seat_rotation("Hips",Quaternion.IDENTITY)
	for side in ["L","R"]:
		var outward := 1.0 if side == "L" else -1.0
		_seat_rotation("UpperLeg."+side,Quaternion(Vector3.RIGHT,deg_to_rad(90))*Quaternion(Vector3.BACK,deg_to_rad(26)*outward))
		_seat_rotation("LowerLeg."+side,Quaternion(Vector3.RIGHT,deg_to_rad(-2)))
		_seat_rotation("Foot."+side,Quaternion(Vector3.RIGHT,deg_to_rad(-35)))
		_rotate("UpperArm."+side,Vector3.RIGHT,deg_to_rad(-10)*seated)
		_rotate("LowerArm."+side,Vector3.RIGHT,deg_to_rad(-12)*seated)
	_seat_rotation("Spine",Quaternion(Vector3.RIGHT,deg_to_rad(-4)))
	_rotate("Head",Vector3.RIGHT,deg_to_rad(13)*seated+nod)
	var head: Dictionary = _rest["Head"]
	skeleton.set_bone_pose_rotation(head.index,skeleton.get_bone_pose_rotation(head.index) * Quaternion(Vector3.UP,sin(nod*5)*.12))
	var eye_up := (skeleton.get_bone_global_pose(head.index).basis * skeleton.get_bone_global_rest(head.index).basis.inverse() * Vector3.UP).normalized()
	for lash in _lashes:
		lash.shader.set_shader_parameter("blink",blink)
		lash.shader.set_shader_parameter("eye_up",eye_up)

func _process(_delta: float) -> void:
	apply_pose()

func release() -> void:
	set_process(false)
	for data: Dictionary in _rest.values():
		skeleton.set_bone_pose_rotation(data.index,data.rotation)
	model.position = _original_position
	for eye in _eyes: eye.mesh.set_surface_override_material(eye.surface,eye.original)
	for lash in _lashes: lash.mesh.set_surface_override_material(lash.surface,lash.original)
	for original in _original_meshes: original.mesh.mesh = original.original
	animator.play("Idle",.15)
	animator.advance(0)
