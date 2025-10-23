extends HBoxContainer

@onready var gear_label: Label = $"../gear_label"

func update_gear(amount: int):
	gear_label.text = "%d" % amount
