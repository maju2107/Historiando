extends CanvasLayer



func _on_retry_btn_pressed() -> void:
	get_tree().paused = false
	get_tree().reload_current_scene()


func _on_comeback_btn_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/telaInicial/TelaInicial.tscn")
