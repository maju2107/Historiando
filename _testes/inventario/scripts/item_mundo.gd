extends RigidBody3D

@export var item_data: ItemData

func _ready() -> void:
	if item_data:
		print("Item: ", item_data.item_nome)
		print("ID: ", item_data.item_id)
	else:
		print("ERRO: ItemData não configurado em: ", get_path())
