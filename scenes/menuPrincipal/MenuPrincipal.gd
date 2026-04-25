extends ColorRect

func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func _on_button_sair_pressed() -> void:
	get_tree().quit()
