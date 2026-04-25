extends CanvasLayer

@onready var popupMenu = $Popup

func BotaoGlobal_on_button_pressed() -> void:
	get_tree().quit()
	
	
func _input(_event: InputEvent) -> void:
	if Input.is_action_just_pressed("menu"):
		if popupMenu.visible:
			popupMenu.hide()
		else:
			popupMenu.popup_centered()
			
			
func _on_popup_visibility_changed() -> void:
	var popup = get_node("Popup")
	get_tree().paused = popup.visible
	
