extends "res://_testes/parkour/player.gd"


func _input(_event: InputEvent) -> void:
	if Input.is_action_just_pressed("AbrirInventario"):
		if Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)		
		else:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	
		
