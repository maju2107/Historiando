extends SceneTree
var frames := 0
func _initialize() -> void:
	root.size = Vector2i(1440, 1000)
	var island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	island.get_node("Player").free()
	var camera := Camera3D.new()
	island.add_child(camera)
	camera.position = Vector3(48, 44, 62)
	camera.look_at_from_position(Vector3(48, 44, 62), Vector3(0, 6, -2))
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 73
	camera.current = true
func _process(_delta: float) -> bool:
	frames += 1
	if frames == 35:
		root.get_texture().get_image().save_png("res://_testes/cenario_ilha/_ambientacao_preview.png")
		quit()
	return false

