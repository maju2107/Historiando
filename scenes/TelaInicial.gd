extends ColorRect

@export var menu_principal : PackedScene

func _on_BotaoVoltar_pressed() -> void:
	get_tree().change_scene_to_packed(menu_principal)
