extends CanvasLayer

func BotaoGlobal_on_button_pressed() -> void:
	get_tree().quit()
	
func _unhandled_input(_event: InputEvent) -> void:
	if Input.is_action_just_pressed("sair"):
		get_tree().quit()
