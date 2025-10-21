extends ColorRect

func _on_jogar_pressed() -> void:
		get_tree().change_scene_to_file("res://scenes/telaInicial/TelaInicial.tscn")
