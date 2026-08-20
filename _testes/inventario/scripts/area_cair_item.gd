extends Control

const ITEM_MUNDO = preload("uid://bpogtba0nttbc")

@onready var camera: Camera3D = get_viewport().get_camera_3d()
@onready var inventory_grid: GridContainer = _find_inventory_grid()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	
	if not camera:
		push_warning("Nenhuma Camera3D ativa foi encontrada para o inventário.")
	
	if not inventory_grid:
		push_warning("A grade do inventário não foi encontrada na cena.")


func _find_inventory_grid() -> GridContainer:
	var scene_root := get_tree().current_scene
	
	if not scene_root:
		return null
	
	var grid := scene_root.find_child(
		"InventarioGridContainer",
		true,
		false
	)
	
	if not grid:
		grid = scene_root.find_child(
			"GridContainer",
			true,
			false
	)
	
	return grid as GridContainer


# =========================================================
# SOLTAR ITEM DO INVENTÁRIO NO MUNDO
# =========================================================

func _can_drop_data(_at_position: Vector2, _data: Variant) -> bool:
	return true


func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if not data or not data.item:
		return
	
	var node = ITEM_MUNDO.instantiate()
	
	# Guarda o ItemData diretamente no objeto
	node.item_data = data.item
	
	# Define a aparência do objeto
	var mesh_instance: MeshInstance3D = node.get_node("MeshInstance3D")

	mesh_instance.mesh = data.item.mesh
	mesh_instance.scale = data.item.escala_mundo
	# Coloca o objeto no mundo
	get_tree().current_scene.add_child(node)
	
	# Remove o item do slot do inventário
	data.item = null
	data.update_ui()
	
	# Posição temporária
	node.global_position = Vector3(randf(), 1, randf())


# =========================================================
# DRAG AND DROP
# =========================================================

func _notification(what: int) -> void:
	if what == Node.NOTIFICATION_DRAG_BEGIN:
		mouse_filter = Control.MOUSE_FILTER_PASS
	
	if what == Node.NOTIFICATION_DRAG_END:
		mouse_filter = Control.MOUSE_FILTER_IGNORE


# =========================================================
# PEGAR ITEM DO MUNDO
# =========================================================

func _unhandled_input(event: InputEvent) -> void:
	if Input.get_mouse_mode() != Input.MOUSE_MODE_VISIBLE:
		return
	
	if not camera or not inventory_grid:
		return
	
	if event is InputEventMouseButton:
		if event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			
			print("Item Pressionado")
			
			var espaco := camera.get_world_3d().direct_space_state
			
			var parametro := PhysicsRayQueryParameters3D.new()
			
			parametro.from = camera.project_ray_origin(event.position)
			parametro.to = parametro.from + camera.project_ray_normal(event.position) * 100
			
			var ray := espaco.intersect_ray(parametro)
			
			if ray and ray["collider"] is RigidBody3D:
				
				var mundo_item = ray["collider"]
				
				# Verifica se já está sendo pego
				if mundo_item.get_meta("pegando", false):
					return
				
				# Pega o ItemData diretamente
				var item_data: ItemData = mundo_item.item_data
				
				# Verifica se o objeto realmente possui ItemData
				if item_data == null:
					print(
						"ERRO: ",
						mundo_item.name,
						" não possui ItemData."
					)
					return
				
				print("Item encontrado: ", item_data.item_nome)
				print("ID: ", item_data.item_id)
				
				var item_guardado := false
				
				# Procura um slot vazio
				for espacoInv in inventory_grid.get_children():
					
					if espacoInv.item:
						continue
					
					# Coloca o ItemData no inventário
					espacoInv.item = item_data
					espacoInv.update_ui()
					
					# Marca como coletado
					mundo_item.set_meta("pegando", true)
					
					# Remove do mundo
					mundo_item.queue_free()
					
					item_guardado = true
					break
				
				if not item_guardado:
					print("Inventário cheio!")
