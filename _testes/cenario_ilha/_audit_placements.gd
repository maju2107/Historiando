extends SceneTree

const GROUPS := [
	"CampoAberto",
	"MataDeGaleria",
	"FlorestaDeAltitude",
	"EstratoBaixo",
	"EstratoRibeirinho",
	"FloresDoCampo",
	"Fungos",
	"Afloramentos",
]

var _island: Node3D
var _frames := 0


func _initialize() -> void:
	var packed := load("res://_testes/cenario_ilha/CenarioIlha.tscn") as PackedScene
	_island = packed.instantiate() as Node3D
	root.add_child(_island)


func _physics_process(_delta: float) -> bool:
	_frames += 1
	if _frames < 5:
		return false
	var space := _island.get_world_3d().direct_space_state
	var vegetation := _island.get_node("Vegetation")
	var total := 0
	var unsupported := 0
	for group_name: String in GROUPS:
		var group := vegetation.get_node(group_name)
		for placement: Node in group.get_children():
			if not placement is Node3D:
				continue
			total += 1
			var spatial := placement as Node3D
			var origin := spatial.global_position
			var bounds := _combined_bounds(spatial)
			var visual_center := bounds.get_center()
			var target_y := 12.0 if bounds.position.y > 10.0 else 8.0 if bounds.position.y > 6.0 else 4.0
			var result := _find_nearest_surface(space, Vector2(visual_center.x, visual_center.z), target_y, placement.name.hash())
			if result.is_empty():
				unsupported += 1
				print("SEM_SOLUCAO\t%s\t%s\tx=%.2f\tz=%.2f" % [group_name, placement.name, origin.x, origin.z])
				continue
			var point := result.position as Vector3
			var delta_x := point.x - visual_center.x
			var delta_z := point.z - visual_center.z
			var moved := Vector2(delta_x, delta_z).length()
			var delta_y := point.y - bounds.position.y
			if moved > 0.05 or absf(delta_y) > 0.05:
				unsupported += 1
				print("SUGESTAO\t%s\t%s\tx=%.2f\tz=%.2f\tground=%.2f\tdx=%.2f\tdz=%.2f\tdy=%.2f" % [group_name, placement.name, origin.x + delta_x, origin.z + delta_z, point.y, delta_x, delta_z, delta_y])
	print("PLACEMENTS total=%d ajustar=%d" % [total, unsupported])
	_island.queue_free()
	quit()
	return false


func _find_nearest_surface(space: PhysicsDirectSpaceState3D, origin: Vector2, target_y: float, hash_value: int) -> Dictionary:
	var angle_offset := deg_to_rad(float(absi(hash_value) % 360))
	for radius_step: int in 13:
		var radius := radius_step * 1.25
		var sample_count := 1 if radius_step == 0 else 24
		for sample: int in sample_count:
			var angle := angle_offset + TAU * sample / sample_count
			var point := origin + Vector2(cos(angle), sin(angle)) * radius
			var query := PhysicsRayQueryParameters3D.create(Vector3(point.x, 40, point.y), Vector3(point.x, -3, point.y), 1)
			var result := space.intersect_ray(query)
			if result.is_empty() or not (result.collider as Node) is TerrainChunk:
				continue
			var hit := result.position as Vector3
			if absf(hit.y - target_y) <= 0.36:
				return result
	return {}


func _combined_bounds(root_node: Node3D) -> AABB:
	var result := AABB()
	var has_bounds := false
	var pending: Array[Node] = [root_node]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		if node is MeshInstance3D and (node as MeshInstance3D).mesh:
			var mesh_node := node as MeshInstance3D
			var bounds := mesh_node.global_transform * mesh_node.get_aabb()
			result = result.merge(bounds) if has_bounds else bounds
			has_bounds = true
		for child: Node in node.get_children():
			pending.append(child)
	return result
