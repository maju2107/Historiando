extends Node3D
## Colisao acompanha a geometria das arvores, sem bloquear arbustos e flores.

func _ready() -> void:
	for tree in find_children("Arvore*", "Node3D", true, false):
		var model := tree.get_node_or_null("Modelo") as MeshInstance3D
		if model != null and model.mesh != null:
			model.create_trimesh_collision()
