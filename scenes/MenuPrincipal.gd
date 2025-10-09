extends ColorRect

func _on_login_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/Login.tscn")
