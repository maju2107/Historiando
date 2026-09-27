extends Button
## A native Button: focus, keyboard, controller and accessibility remain available.
@export var fill := Color("dda63b")
@export var compact := false
var _hover := false
const Dots = preload("res://scenes/ui/halftone.gd")

func _ready() -> void:
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	for state in ["normal", "hover", "pressed", "focus", "disabled"]:
		add_theme_stylebox_override(state, StyleBoxEmpty.new())
	add_theme_font_override("font", preload("res://common/fonts/historiando/BarlowCondensed-Bold.ttf"))
	add_theme_font_size_override("font_size", 26 if compact else 38)
	for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		add_theme_color_override(state, Color("1a002c"))
	add_theme_color_override("font_disabled_color", Color("ab9d9d"))
	mouse_entered.connect(func(): _hover = true; queue_redraw())
	mouse_exited.connect(func(): _hover = false; queue_redraw())
	focus_entered.connect(queue_redraw)
	focus_exited.connect(queue_redraw)
	button_down.connect(queue_redraw)
	button_up.connect(queue_redraw)

func _draw() -> void:
	var shift := Vector2(3, 4) if is_pressed() else Vector2.ZERO
	var outline := Color("1a002c")
	var points := PackedVector2Array([Vector2(12, 2), Vector2(size.x-3, 0), Vector2(size.x-12, size.y-8), Vector2(0, size.y-3)])
	var shadow := PackedVector2Array()
	var face := PackedVector2Array()
	for p in points:
		shadow.append(p+Vector2(5, 6))
		face.append(p+shift)
	draw_colored_polygon(shadow, outline)
	var tone := fill.lightened(0.12) if (_hover or has_focus()) else fill
	if disabled: tone = Color("514155")
	draw_colored_polygon(face, tone)
	var border := face.duplicate()
	border.append(face[0])
	draw_polyline(border, outline, 4, true)
	if has_focus():
		draw_line(Vector2(25, size.y-16), Vector2(size.x-30, size.y-20), Color("fff0cc"), 3, true)
	if not compact:
		Dots.patch(self,Rect2(Vector2(size.x-145,8)+shift,Vector2(122,size.y-24)),Color(0.1,0,0.17,0.21),8,1.5)
	# Native Button draws its text before the scripted canvas commands. Redraw
	# the caption above the polygon while retaining native text/accessibility.
	var font := get_theme_font("font")
	var font_size := get_theme_font_size("font_size")
	while font.get_string_size(text,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x > size.x-38 and font_size > 16:
		font_size -= 1
	var width := font.get_string_size(text,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x
	var baseline := (size.y-8-font.get_height(font_size))/2.0+font.get_ascent(font_size)
	draw_string(font,Vector2((size.x-width)/2.0,baseline)+shift,text,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size,Color("ab9d9d") if disabled else outline)
