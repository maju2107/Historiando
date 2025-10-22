extends Node

@onready var player := $AudioStreamPlayer

func play_music():
	player.play()

func stop_music():
	player.stop()
