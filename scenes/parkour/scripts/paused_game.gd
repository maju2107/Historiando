extends CanvasLayer
			
func _on_comeback_btn_pressed() -> void:
	Transicao.transicionar_para("res://scenes/telaInicial/TelaInicial.tscn")
	#get_tree().change_scene_to_file("res://scenes/telaInicial/TelaInicial.tscn")

func _on_resume_btn_2_pressed() -> void:
	get_tree().paused = false
	queue_free()
