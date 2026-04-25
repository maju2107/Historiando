extends Node3D


var pause_menu_scene = preload("res://_testes/parkour/paused_game.tscn")
var pause_menu_instance: Node = null

func _ready() -> void:
	pass

func _input(event):
	if event.is_action_pressed("ui_cancel"):
		toggle_pause()

func toggle_pause():
	if get_tree().paused:
		get_tree().paused = false
		if pause_menu_instance:
			pause_menu_instance.queue_free()
			pause_menu_instance = null
	else:
		get_tree().paused = true
		pause_menu_instance = pause_menu_scene.instantiate()
		add_child(pause_menu_instance)
