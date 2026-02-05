extends CanvasLayer



func _on_retry_btn_pressed() -> void:
	get_tree().paused = false
	get_tree().reload_current_scene()


func _on_comeback_btn_pressed() -> void:
	Transicao.transicionar_para("res://scenes/telaInicial/TelaInicial.tscn")
