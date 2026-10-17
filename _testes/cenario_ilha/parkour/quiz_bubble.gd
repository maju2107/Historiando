extends Control
signal dismissed
## A nonmodal speech bubble: movement and jumping remain available.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var heading: Label
var question: Label
var instruction: Label
var number := 0
var words := ""
var showing := false
var reduced_motion := false
var _transition: Tween
var _rest_position := Vector2.ZERO
var _slide := 0.0:
	set(value):
		_slide = value
		position = _rest_position+Vector2(0,value)

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	heading = Kit.label(self,"",Rect2(),20,Kit.CLAY,Kit.BOLD)
	question = Kit.label(self,"",Rect2(),34,Kit.INK,Kit.BOLD)
	question.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	instruction = Kit.label(self,"Salte na plataforma com a resposta certa.",Rect2(),19,Kit.INK)
	instruction.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	get_viewport().size_changed.connect(_layout)
	_layout()
	modulate.a = 0.0
	hide()

func present(index: int,text: String) -> void:
	if showing and number == index+1 and words == text: return
	if _transition and _transition.is_valid(): _transition.kill()
	if not visible or number != index+1:
		modulate.a = 0.0
		_slide = 0.0 if reduced_motion else -9.0
	showing = true
	number = index+1
	words = text
	_layout()
	show()
	_transition = create_tween().set_parallel(true)
	var seconds := .16 if reduced_motion else .38
	_transition.tween_property(self,"modulate:a",1.0,seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_transition.tween_property(self,"_slide",0.0,seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)

func dismiss() -> void:
	if not showing: return
	showing = false
	if _transition and _transition.is_valid(): _transition.kill()
	_transition = create_tween().set_parallel(true)
	var seconds := .14 if reduced_motion else .26
	_transition.tween_property(self,"modulate:a",0.0,seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_transition.tween_property(self,"_slide",0.0 if reduced_motion else -5.0,seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_transition.chain().tween_callback(func():
		hide()
		dismissed.emit())

func _layout() -> void:
	if not is_instance_valid(question): return
	var screen := get_viewport_rect().size
	var factor := clampf(screen.x/1600.0,.65,1.15)
	var portrait := screen.x < screen.y
	var compact := screen.y < 550 and not portrait
	position = Vector2(16,8 if compact else 18)*factor if portrait or compact else Vector2(screen.x*.295,18*factor)
	size.x = screen.x-32*factor if portrait or compact else screen.x*.49
	heading.text = "DESAFIO DO KAI · %d / 4" % number
	heading.position = Vector2(28,8 if compact else 17)*factor
	heading.add_theme_font_size_override("font_size",roundi(20*factor))
	question.text = words
	question.position = Vector2(28,36 if compact else 46)*factor
	question.size.x = size.x-56*factor
	question.add_theme_font_size_override("font_size",roundi(33*factor))
	question.reset_size()
	question.size.x = size.x-56*factor
	instruction.position = Vector2(28*factor,question.position.y+question.get_minimum_size().y+8*factor)
	instruction.size.x = size.x-56*factor
	instruction.add_theme_font_size_override("font_size",maxi(13,roundi(19*factor)))
	instruction.reset_size()
	instruction.size.x = size.x-56*factor
	instruction.visible = not compact
	size.y = question.position.y+question.get_minimum_size().y+16*factor if compact else instruction.position.y+instruction.get_minimum_size().y+20*factor
	_rest_position = position
	position = _rest_position+Vector2(0,_slide)
	queue_redraw()

func _draw() -> void:
	var screen := get_viewport_rect().size
	var tail := 9 if screen.y < 550 and screen.x > screen.y else 17
	var points := PackedVector2Array([Vector2(10,2),Vector2(size.x-8,0),Vector2(size.x,size.y-9),Vector2(size.x*.61,size.y),Vector2(size.x*.55,size.y+tail),Vector2(size.x*.54,size.y),Vector2(0,size.y-3)])
	var shadow := PackedVector2Array()
	for point in points: shadow.append(point+Vector2(5,6))
	draw_colored_polygon(shadow,Kit.INK)
	draw_colored_polygon(points,Kit.PAPER)
	points.append(points[0])
	draw_polyline(points,Kit.INK,3,true)
	draw_line(Vector2(28,size.y-10),Vector2(size.x-28,size.y-10),Kit.GOLD,2,true)
