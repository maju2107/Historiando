extends ColorRect

@export var menu_principal : PackedScene
var mecanica2 = preload("res://scenes/mecanica2/Mecanica2Carta.tscn")
var mecanica3 = preload("res://scenes/mecanica3/mecanica_3.tscn")

func _on_BotaoVoltar_pressed() -> void:
	get_tree().change_scene_to_packed(menu_principal)


func _on_button_mec_2_pressed() -> void:
	get_tree().change_scene_to_packed(mecanica2)
	
func  _on_button_mec_3_pressed() -> void:
	get_tree().change_scene_to_packed(mecanica3)
