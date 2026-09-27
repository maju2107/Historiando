extends Control
## Reusable HUD. Call set_health, set_collectibles, set_objective and
## set_interaction from the relevant gameplay systems.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var canvas: Control
var hearts: Label
var counter: Label
var objective: Label
var interaction: Control
var prompt: Label
var notification: Label
var notice_timer: Timer
var health := 3
var collectibles := 0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	canvas = Control.new()
	canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(canvas)
	Kit.rect(canvas, Rect2(43,43,350,103), Kit.INK)
	Kit.rect(canvas, Rect2(48,48,340,93), Kit.PAPER)
	Kit.brand(canvas, Rect2(58,53,78,78), true)
	Kit.label(canvas,"VIAJANTE",Rect2(150,53,200,25),20,Kit.INK,Kit.BOLD)
	hearts = Kit.label(canvas,"",Rect2(148,76,220,48),34,Kit.CLAY,Kit.BOLD)
	Kit.rect(canvas,Rect2(46,158,340,7),Kit.INK)
	Kit.rect(canvas,Rect2(46,158,340,4),Kit.GOLD)
	Kit.rect(canvas,Rect2(1200,48,352,62),Kit.INK)
	counter = Kit.label(canvas,"",Rect2(1220,51,318,50),28,Kit.PAPER,Kit.BOLD)
	Kit.label(canvas,"P I N D O R A M A",Rect2(665,42,300,26),21,Kit.PAPER,Kit.BOLD).horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.label(canvas,"EXPLORAÇÃO",Rect2(665,68,300,24),16,Kit.PAPER).horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	Kit.rect(canvas,Rect2(46,204,328,106),Color("1a002ce8"))
	Kit.rect(canvas,Rect2(46,204,5,106),Kit.GOLD)
	Kit.label(canvas,"SUA JORNADA",Rect2(65,215,280,26),20,Kit.GOLD,Kit.BOLD)
	objective = Kit.label(canvas,"Explore os caminhos da ilha.",Rect2(65,248,287,54),25)
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	interaction = Control.new()
	interaction.position = Vector2(585,720)
	interaction.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(interaction)
	Kit.rect(interaction,Rect2(0,0,430,65),Kit.INK)
	Kit.rect(interaction,Rect2(8,8,49,49),Kit.GOLD)
	Kit.label(interaction,"E",Rect2(8,8,49,49),30,Kit.INK,Kit.BOLD).horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt = Kit.label(interaction,"Interagir",Rect2(74,10,343,45),28)
	interaction.hide()
	Kit.rect(canvas,Rect2(45,819,385,40),Color("1a002ce8"))
	Kit.label(canvas,"W A S D  Mover     ESPAÇO  Pular",Rect2(57,821,370,36),22)
	Kit.button(canvas,"II   PAUSA",Rect2(1365,814,180,49),_pause,Kit.PAPER,true)
	notification = Kit.label(canvas,"",Rect2(505,156,590,63),30,Kit.INK,Kit.BOLD)
	notification.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var bg := preload("res://scenes/ui/comic_panel.gd").new()
	bg.fill = Kit.GOLD
	bg.size = Vector2(620,69)
	bg.position = Vector2(-15,-3)
	bg.show_behind_parent = true
	notification.add_child(bg)
	notification.hide()
	notice_timer = Timer.new()
	notice_timer.one_shot = true
	notice_timer.timeout.connect(notification.hide)
	add_child(notice_timer)
	set_health(health)
	set_collectibles(collectibles)
	get_viewport().size_changed.connect(_resize)
	_resize()

func _resize() -> void:
	var viewport := get_viewport_rect().size
	var factor := minf(viewport.x/1600.0,viewport.y/900.0)
	canvas.scale = Vector2.ONE*factor
	canvas.position = (viewport-Vector2(1600,900)*factor)/2

func set_health(value: int, maximum: int = 3) -> void:
	health = clampi(value,0,maximum)
	if hearts:
		hearts.text = "VIDAS  " + "● ".repeat(health) + "○ ".repeat(maximum-health)

func set_collectibles(value: int) -> void:
	collectibles = maxi(value,0)
	if counter: counter.text = "FRAGMENTOS      %02d" % collectibles

func set_objective(text: String) -> void:
	if objective: objective.text = text

func set_interaction(text: String, key: String = "E") -> void:
	if not interaction: return
	prompt.text = text
	(interaction.get_child(2) as Label).text = key
	interaction.visible = not text.is_empty()

func notify(text: String) -> void:
	notification.text = text
	notification.show()
	notice_timer.start(3.0)

func _pause() -> void:
	var manager := get_node_or_null("/root/BotaoGlobal")
	if manager and manager.has_method("toggle_pause"): manager.toggle_pause()
