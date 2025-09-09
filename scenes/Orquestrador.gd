extends Node

@onready var menu_principal = $MenuPrincipal
@onready var login = $Login


func _on_button_pressed() -> void:
	menu_principal.visible = false


func _on_button_2_pressed() -> void:
	menu_principal.visible = true
