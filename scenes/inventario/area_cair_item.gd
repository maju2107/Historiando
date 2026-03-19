extends Control

const ITEM_MUNDO = preload("uid://bpogtba0nttbc")

func _can_drop_data(_at_position: Vector2, _data: Variant) -> bool:
	return true
		
		
func _drop_data(_at_position: Vector2, data: Variant) -> void:
	var node = ITEM_MUNDO.instantiate()
	
	node.set_meta("item_data", data.item)
	node.get_node("MeshInstance3D").mesh = data.item.mesh
	
	get_tree().current_scene.add_child(node)
	data.item = null
	node.global_position = Vector3(randf(), 1, randf())
