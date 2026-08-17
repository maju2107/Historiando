@tool
class_name TerrainChunk
extends StaticBody3D

@export var model: PackedScene:
	set(value):
		model = value
		_queue_rebuild()

var _rebuild_queued := false


func _ready() -> void:
	_rebuild()


func _queue_rebuild() -> void:
	if not is_inside_tree() or _rebuild_queued:
		return
	_rebuild_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_rebuild_queued = false
	for child: Node in get_children(true):
		if child.has_meta(&"terrain_chunk_generated"):
			child.free()

	if model == null:
		return

	var visual := model.instantiate() as Node3D
	visual.set_meta(&"terrain_chunk_generated", true)
	add_child(visual, false, Node.INTERNAL_MODE_FRONT)

	var collision_count := _create_mesh_collisions(visual)
	if collision_count == 0:
		push_warning("O modelo do TerrainChunk não contém uma MeshInstance3D.")


func _create_mesh_collisions(root_node: Node3D) -> int:
	var collision_count := 0
	var entries: Array[Dictionary] = [{
		"node": root_node,
		"transform": Transform3D.IDENTITY,
	}]

	while not entries.is_empty():
		var entry: Dictionary = entries.pop_back()
		var current := entry.node as Node3D
		var current_transform := entry.transform as Transform3D

		if current is MeshInstance3D and current.mesh:
			var shape: Shape3D = current.mesh.create_trimesh_shape()
			if shape:
				var collision := CollisionShape3D.new()
				collision.name = "GeneratedCollision_%02d" % collision_count
				collision.transform = current_transform
				collision.shape = shape
				collision.set_meta(&"terrain_chunk_generated", true)
				add_child(collision, false, Node.INTERNAL_MODE_FRONT)
				collision_count += 1

		for child: Node in current.get_children():
			if child is Node3D:
				entries.append({
					"node": child,
					"transform": current_transform * child.transform,
				})

	return collision_count
