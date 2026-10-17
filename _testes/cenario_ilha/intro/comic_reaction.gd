extends Control
## Ink-and-paper stickers, matching the game's printed comic interface.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var words := "?!"
var accent := Kit.GOLD
var rays := true
var title: Label
var content_rect := Rect2()
var fitted_font_size := 49
var text_lines: PackedStringArray

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	title = Label.new()
	title.name = "EffectText"
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title.clip_text = true # Keep an earlier long line from forcing a larger minimum width on resize.
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title.add_theme_font_override("font",Kit.BOLD)
	title.add_theme_constant_override("line_spacing",0)
	title.add_theme_color_override("font_color",Kit.INK)
	add_child(title)
	resized.connect(_fit_text)
	_fit_text()

func _fit_text() -> void:
	if not is_instance_valid(title): return
	# The center is narrower than the spike-to-spike bounds of the burst.
	content_rect = Rect2(size*Vector2(.20,.31),size*Vector2(.60,.38))
	var maximum := 90 if words == "?!" else 49
	for candidate in range(maximum,11,-1):
		var lines := PackedStringArray()
		for paragraph in words.split("\n"):
			var line := ""
			for word in paragraph.split(" ",false):
				var next := word if line.is_empty() else line+" "+word
				if not line.is_empty() and Kit.BOLD.get_string_size(next,HORIZONTAL_ALIGNMENT_LEFT,-1,candidate).x > content_rect.size.x:
					lines.append(line)
					line = word
				else: line = next
			lines.append(line)
		var widest := 0.0
		for line in lines:
			widest = maxf(widest,Kit.BOLD.get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,candidate).x)
		if widest <= content_rect.size.x and Kit.BOLD.get_height(candidate)*lines.size() <= content_rect.size.y:
			fitted_font_size = candidate
			text_lines = lines
			break
	title.text = "\n".join(text_lines)
	title.add_theme_font_size_override("font_size",fitted_font_size)
	title.position = content_rect.position
	title.size = content_rect.size
	queue_redraw()

func _draw() -> void:
	var center := size/2
	var points := PackedVector2Array()
	var n := 24
	for i in n:
		var a := TAU*i/n
		var spike := 1.0 if i%2==0 else .77
		points.append(center+Vector2(cos(a)*(size.x*.48),sin(a)*(size.y*.45))*spike)
	var shadow := PackedVector2Array()
	for p in points: shadow.append(p+Vector2(7,9))
	draw_colored_polygon(shadow,Kit.INK)
	draw_colored_polygon(points,accent)
	points.append(points[0])
	draw_polyline(points,Kit.INK,4,true)
	for x in range(40,int(size.x)-20,13):
		for y in [30,int(size.y)-29]: draw_circle(Vector2(x,y),1.6,Color(Kit.INK,.22))
	if rays:
		for i in 7:
			var a := -.95+float(i)*.34
			var start := center+Vector2(cos(a)*size.x*.52,sin(a)*size.y*.55)
			var end := center+Vector2(cos(a)*size.x*.58,sin(a)*size.y*.72)
			draw_line(start,end,Kit.PAPER,5,true)
	for at in [Vector2(-7,30),Vector2(size.x+8,size.y*.77)]:
		draw_line(at-Vector2(9,0),at+Vector2(9,0),Kit.GOLD,4,true)
		draw_line(at-Vector2(0,9),at+Vector2(0,9),Kit.GOLD,4,true)
