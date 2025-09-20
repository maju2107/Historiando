extends Node

@onready var menu_principal = $MenuPrincipal
@onready var login = $Login

func _on_botaoVoltar_mp_pressed() -> void:
	menu_principal.visible = true


func _on_login_pressed() -> void:
	menu_principal.visible = false
