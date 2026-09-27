extends Control
@export var fill := Color("dac7a7")
@export var textured := true
const Dots = preload("res://scenes/ui/halftone.gd")

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)

func _draw() -> void:
	var points := PackedVector2Array([Vector2(13,5),Vector2(size.x-3,0),Vector2(size.x-14,size.y-7),Vector2(0,size.y)])
	var shadow := PackedVector2Array()
	for point in points: shadow.append(point+Vector2(9,10))
	draw_colored_polygon(shadow,Color("0e0018"))
	draw_colored_polygon(points,fill)
	points.append(points[0])
	draw_polyline(points,Color("1a002c"),4,true)
	if textured:
		Dots.patch(self,Rect2(size.x-230,14,205,minf(135,size.y-26)),Color(0.1,0,0.17,0.18),11,1.8)
