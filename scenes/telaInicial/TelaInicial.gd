extends ColorRect

func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func _on_BotaoVoltar_pressed() -> void:
	Transicao.transicionar_para("res://scenes/menuPrincipal/MenuPrincipal.tscn")

func _on_button_mec_2_pressed() -> void:
	Transicao.transicionar_para("res://scenes/mecanica2/Mecanica2Carta.tscn")
	
func  _on_button_mec_3_pressed() -> void:
	Transicao.transicionar_para("res://scenes/mecanica3/mecanica_3.tscn")


func _on_button_mec_1_pressed() -> void:
	Transicao.transicionar_para("res://scenes/mecanica1/Mecanica1Questionario.tscn")
