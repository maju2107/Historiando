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
	
func _notification(what: int) -> void:
	if what == Node.NOTIFICATION_DRAG_BEGIN:
		mouse_filter = Control.MOUSE_FILTER_PASS
	if what == Node.NOTIFICATION_DRAG_END:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
	
	
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.pressed:
			print("Item Pressionado")
				
			var camera := get_viewport().get_camera_3d()
			var espaco := camera.get_world_3d().direct_space_state
			
			var parametro = PhysicsRayQueryParameters3D.new()
			parametro.from = camera.project_ray_origin(event.position)
			parametro.to = parametro.from + camera.project_ray_normal(event.position) * 100
			
			var ray := espaco.intersect_ray(parametro)
			if ray and ray["collider"] is RigidBody3D:
				var mundo_item = ray["collider"]
				for espacoInv in %InventarioGridContainer.get_children():
					if espacoInv.item: continue
					
					# pega o primeiro espacoInv vazio
					espacoInv.item = ray["collider"].get_meta("item_data")
					espacoInv.update_ui()
					mundo_item.queue_free()
					break 
