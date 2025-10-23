extends Node2D

func _ready():
	var option_button = $OptionButton
	option_button.add_item("Fácil", 0)
	option_button.add_item("Médio", 1)
	option_button.add_item("Difícil", 2)
