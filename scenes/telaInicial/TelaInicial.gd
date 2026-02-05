extends ColorRect

func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)


func _on_BotaoVoltar_pressed() -> void:
	Transicao.transicionar_para("res://scenes/menuPrincipal/MenuPrincipal.tscn")


func _on_button_jogar_pressed() -> void:
	Transicao.transicionar_para("res://scenes/menuDeFases/MenuDeFases.tscn") # Replace with function body.
