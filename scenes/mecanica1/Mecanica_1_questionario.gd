extends Node2D

func _ready():
	pass


func _on_button_3_pressed() -> void:
	$Popup1.popup_centered()
	await get_tree().create_timer(2.0).timeout
	$Popup1.hide() 


func _on_button1_pressed() -> void:
	$Popup2.popup_centered()
	await get_tree().create_timer(2.0).timeout
	$Popup2.hide()
	

func _on_button_4_pressed() -> void:
	$Popup2.popup_centered()
	await get_tree().create_timer(2.0).timeout
	$Popup2.hide()
	

func _on_button_2_pressed() -> void:
	$Popup2.popup_centered()
	await get_tree().create_timer(2.0).timeout
	$Popup2.hide()
