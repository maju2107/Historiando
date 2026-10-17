extends SceneTree
## Cache the authored shapes, never synthesize spatial mouth masks in engine.
func _initialize() -> void:
	var model := load("res://assets/characters/yara/yara_playable.glb").instantiate() as Node3D
	var source: ArrayMesh = model.find_child("Yara_PaintedSkin",true,false).mesh
	assert(source.get_blend_shape_count()==17)
	var error := ResourceSaver.save(source,"res://assets/characters/yara/yara_expressions.res",ResourceSaver.FLAG_COMPRESS)
	print("YARA_AUTHORED_FACE_CACHE ",error," shapes=",source.get_blend_shape_count())
	model.free()
	quit(error)
