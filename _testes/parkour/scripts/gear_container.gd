extends HBoxContainer

@onready var gear_label: Label = $gear_label
@onready var life_label: Label = $life_label

func update_gear(amount: int):
	gear_label.text = "%d" % amount

func update_life(health: int):
	life_label.text = "%d" % health
	
