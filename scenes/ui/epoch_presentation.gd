extends PanelContainer
## A short, nonmodal introduction, anchored in the HUD's scaled design canvas.
const Kit = preload("res://scenes/ui/ui_kit.gd")
const DESCRIPTION := "Entre 2,58 milhões e 11,7 mil anos atrás.\nGeleiras avançavam e recuavam pelo planeta.\nGrandes mamíferos formavam a megafauna."
const DISPLAY_SECONDS := 10.0
var description: Label
var animation: Tween
var presentations := 0
var resting_position := Vector2(970,450)

func _ready() -> void:
	name = "EpochPresentation"
	process_mode = Node.PROCESS_MODE_PAUSABLE
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	position = resting_position
	custom_minimum_size = Vector2(584,0)
	var style := StyleBoxFlat.new()
	style.bg_color = Color("1a002cf2")
	style.border_color = Kit.GOLD
	style.border_width_left = 4
	style.border_width_top = 1
	style.content_margin_left = 26
	style.content_margin_right = 26
	style.content_margin_top = 20
	style.content_margin_bottom = 24
	add_theme_stylebox_override("panel",style)
	var column := VBoxContainer.new()
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_theme_constant_override("separation",9)
	add_child(column)
	Kit.label(column,"UMA ÉPOCA A DESCOBRIR",Rect2(),18,Kit.GOLD,Kit.BOLD)
	Kit.label(column,"PLEISTOCENO",Rect2(),38,Kit.PAPER,Kit.BOLD)
	var rule := HSeparator.new()
	var line := StyleBoxLine.new()
	line.color = Color("dda63b88")
	line.thickness = 1
	rule.add_theme_stylebox_override("separator",line)
	column.add_child(rule)
	description = Kit.label(column,DESCRIPTION,Rect2(),25,Kit.PAPER)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.custom_minimum_size.x = 532
	hide()

func present() -> void:
	presentations += 1
	if animation: animation.kill()
	var preferences := ConfigFile.new()
	preferences.load("user://interface.cfg")
	var reduced := bool(preferences.get_value("accessibility","reduce_motion",false))
	position = resting_position + (Vector2.ZERO if reduced else Vector2(40,0))
	modulate.a = 0.0
	show()
	animation = create_tween().set_pause_mode(Tween.TWEEN_PAUSE_BOUND)
	animation.tween_property(self,"modulate:a",1.0,.4)
	if not reduced:
		animation.parallel().tween_property(self,"position",resting_position,.5).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	animation.tween_interval(DISPLAY_SECONDS)
	animation.tween_property(self,"modulate:a",0.0,.5)
	animation.tween_callback(hide)
