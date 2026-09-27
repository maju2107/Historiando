extends HBoxContainer

@onready var gear_label: Label = $gear_label
@onready var life_label: Label = $life_label
var comic_hud: Control

func _ready() -> void:
	# Preserve this adapter's existing NodePath and API for both player scripts.
	hide()
	comic_hud = preload("res://scenes/ui/historiando_hud.tscn").instantiate()
	get_parent().add_child.call_deferred(comic_hud)

func update_gear(amount: int):
	gear_label.text = "Itens: %d" % amount
	if is_instance_valid(comic_hud):
		comic_hud.set_collectibles(amount)
		if comic_hud.is_node_ready(): comic_hud.notify("+1 FRAGMENTO  /  NOVA DESCOBERTA!")

func update_life(health: int):
	life_label.text = "Vidas: %d" % health
	if is_instance_valid(comic_hud): comic_hud.set_health(health)
	if health <= 0:
		var manager := get_node_or_null("/root/BotaoGlobal")
		if manager and manager.has_method("show_game_over"):
			manager.show_game_over.call_deferred()
	
