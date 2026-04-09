extends "res://scenes/parkour/player.gd"

@onready var raycast : RayCast3D = $camera_pivo/camera/raycast
@onready var hold_point: Marker3D = $camera_pivo/camera/hold_point
@onready var canvas_layer: CanvasLayer = $"../mundo/CanvasLayer"


func _unhandled_input(_event: InputEvent) -> void:
	if Input.is_action_just_pressed("AbrirInventario"):
		canvas_layer.show()
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		
