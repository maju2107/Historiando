extends SceneTree

const ROOT := "res://assets/models/creative_trio/"
const SHEETS := {
	"Trees01": ["Tree_001", "Tree_002", "Tree_003", "Tree_004", "Tree_005", "Tree_006", "Tree_007", "Tree_008", "Tree_009", "Tree_010", "Tree_011", "Tree_012", "Tree_013", "Tree_014", "Tree_015", "Tree_016", "Tree_017", "Tree_018", "Tree_019", "Tree_020", "Tree_021", "Tree_026", "Tree_027"],
	"Trees02": ["Tree_001", "Tree_002", "Tree_003", "Tree_004", "Tree_008", "Tree_009", "Tree_010", "Tree_011", "Tree_015", "Tree_016", "Tree_017", "Tree_018", "Tree_022", "Tree_023", "Tree_024", "Tree_025", "Tree_029", "Tree_030", "Tree_031", "Tree_032", "Tree_036", "Tree_037", "Tree_038", "Tree_039"],
	"Plants02": ["Plant_003", "Plant_004", "Plant_005", "Plant_006", "Plant_007", "Plant_008", "Plant_010", "Plant_013", "Plant_020", "Plant_027", "Plant_028", "Plant_030", "Plant_037", "Plant_047"],
}

var _world: Node3D
var _camera: Camera3D
var _sheet_names: Array
var _sheet_index := 0
var _frames := 0


func _initialize() -> void:
	root.size = Vector2i(1800, 1100)
	_world = Node3D.new()
	root.add_child(_world)

	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#cad8d0")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.WHITE
	env.ambient_light_energy = 1.0
	environment.environment = env
	_world.add_child(environment)

	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-35, -25, 0)
	light.light_energy = 1.4
	light.shadow_enabled = true
	_world.add_child(light)

	_camera = Camera3D.new()
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.position = Vector3(0, 10, 50)
	_camera.size = 28.0
	_world.add_child(_camera)
	_camera.current = true

	_sheet_names = SHEETS.keys()
	_build_sheet(_sheet_names[_sheet_index])


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames < 8:
		return false
	var image := root.get_texture().get_image()
	var output := "res://_testes/cenario_ilha/_%s.png" % _sheet_names[_sheet_index]
	image.save_png(ProjectSettings.globalize_path(output))
	print("SAVED ", output)
	_sheet_index += 1
	if _sheet_index >= _sheet_names.size():
		quit()
		return false
	_frames = 0
	_build_sheet(_sheet_names[_sheet_index])
	return false


func _build_sheet(folder: String) -> void:
	for child: Node in _world.get_children():
		if child.has_meta("preview"):
			child.free()
	var names: Array = SHEETS[folder]
	var columns := 6
	var rows := ceili(float(names.size()) / columns)
	var cell_width := 5.0
	var cell_height := 5.2
	var top := (rows - 1) * cell_height * 0.5
	for index: int in names.size():
		var model_name: String = names[index]
		var packed := load(ROOT + folder + "/" + model_name + ".fbx") as PackedScene
		if packed == null:
			continue
		var instance := packed.instantiate() as Node3D
		instance.set_meta("preview", true)
		_world.add_child(instance)
		var bounds := _combined_bounds(instance)
		var fit := 3.8 / maxf(bounds.size.x, bounds.size.y)
		var column := index % columns
		var row := index / columns
		var left := -(columns - 1) * cell_width * 0.5
		instance.scale = Vector3.ONE * fit
		instance.position = Vector3(left + column * cell_width - bounds.get_center().x * fit, top - row * cell_height - bounds.position.y * fit, 0)

		var label := Label3D.new()
		label.set_meta("preview", true)
		label.text = model_name
		label.font_size = 28
		label.modulate = Color("#15241c")
		label.outline_size = 5
		label.outline_modulate = Color("#eaf0ec")
		label.position = Vector3(left + column * cell_width, top - row * cell_height - 0.55, 0.1)
		_world.add_child(label)
	_camera.position.y = 0.3 if rows >= 4 else 2.7


func _combined_bounds(root_node: Node) -> AABB:
	var result := AABB()
	var has_bounds := false
	var entries: Array[Dictionary] = [{"node": root_node, "transform": Transform3D.IDENTITY}]
	while not entries.is_empty():
		var entry: Dictionary = entries.pop_back()
		var node := entry.node as Node
		var transform := entry.transform as Transform3D
		if node is Node3D and node != root_node:
			transform *= (node as Node3D).transform
		if node is MeshInstance3D and (node as MeshInstance3D).mesh:
			var mesh_bounds := transform * (node as MeshInstance3D).get_aabb()
			result = result.merge(mesh_bounds) if has_bounds else mesh_bounds
			has_bounds = true
		for child: Node in node.get_children():
			entries.append({"node": child, "transform": transform})
	return result
