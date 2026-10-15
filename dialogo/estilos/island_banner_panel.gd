extends Control
const Kit = preload("res://scenes/ui/ui_kit.gd")

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)

func _draw() -> void:
	var w := size.x
	var h := size.y
	var points := PackedVector2Array([Vector2(22,4),Vector2(w-25,0),Vector2(w,h*.32),Vector2(w-18,h-8),Vector2(26,h),Vector2(0,h*.70)])
	var shadow := PackedVector2Array()
	for point in points: shadow.append(point + Vector2(3,8))
	draw_colored_polygon(shadow,Color("10001de0"))
	draw_colored_polygon(points,Kit.PAPER.lightened(.24))
	points.append(points[0])
	draw_polyline(points,Kit.INK,5,true)
	draw_line(Vector2(50,h-15),Vector2(w-48,h-18),Kit.GOLD,4,true)
