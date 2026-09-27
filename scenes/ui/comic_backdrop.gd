extends Control
## Original vector scenery, built from the project's palette and spiral motif.
@export var landscape := true
const Dots = preload("res://scenes/ui/halftone.gd")

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color("1a002c"))
	if not landscape:
		Dots.patch(self,Rect2(960,-120,790,615),Color(0.85,0.7,0.5,0.13),17,2.0)
		Dots.patch(self,Rect2(-210,480,850,570),Color(0.85,0.7,0.5,0.1),17,1.8)
		return
	var frame := PackedVector2Array([Vector2(655,58),Vector2(1542,38),Vector2(1515,796),Vector2(615,825)])
	draw_colored_polygon(frame, Color("dda63b"))
	# Comic rays converge behind the time portal.
	for i in range(19):
		var a := float(i) * TAU / 19.0
		var origin := Vector2(1130,370)
		var p1 := origin + Vector2.from_angle(a)*390
		var p2 := origin + Vector2.from_angle(a+0.045)*390
		p1 = p1.clamp(Vector2(696,80),Vector2(1500,780))
		p2 = p2.clamp(Vector2(696,80),Vector2(1500,780))
		draw_colored_polygon(PackedVector2Array([origin,p1,p2]), Color("e9b64e"))
	Dots.patch(self,Rect2(810,74,700,342),Color(0.35,0.15,0.16,0.23),12,2.0)
	draw_circle(Vector2(1120,350),208,Color("f0d090"))
	# Three layers of angular hills, a river, foliage and a portal.
	draw_colored_polygon(PackedVector2Array([Vector2(648,410),Vector2(775,290),Vector2(885,450),Vector2(1030,360),Vector2(1220,460),Vector2(1360,285),Vector2(1534,380),Vector2(1525,650),Vector2(632,650)]),Color("ce6035"))
	draw_colored_polygon(PackedVector2Array([Vector2(640,520),Vector2(798,400),Vector2(910,480),Vector2(1030,455),Vector2(1210,540),Vector2(1390,435),Vector2(1530,500),Vector2(1518,750),Vector2(620,790)]),Color("466750"))
	draw_colored_polygon(PackedVector2Array([Vector2(630,650),Vector2(820,540),Vector2(1040,585),Vector2(1240,510),Vector2(1525,635),Vector2(1515,796),Vector2(615,825)]),Color("2f5143"))
	draw_colored_polygon(PackedVector2Array([Vector2(1160,520),Vector2(1110,570),Vector2(1140,615),Vector2(1020,665),Vector2(1120,718),Vector2(984,813),Vector2(1240,804),Vector2(1235,720),Vector2(1140,665),Vector2(1210,620),Vector2(1150,570)]),Color("b5c5a0"))
	# Stone portal is a deliberately invented fantasy symbol.
	draw_arc(Vector2(1130,389),137,PI,TAU,64,Color("1a002c"),35,true)
	draw_line(Vector2(993,389),Vector2(993,553),Color("1a002c"),35,true)
	draw_line(Vector2(1267,389),Vector2(1267,553),Color("1a002c"),35,true)
	draw_arc(Vector2(1130,389),137,PI,TAU,64,Color("dac7a7"),22,true)
	draw_line(Vector2(993,389),Vector2(993,543),Color("dac7a7"),22,true)
	draw_line(Vector2(1267,389),Vector2(1267,543),Color("dac7a7"),22,true)
	var spiral := PackedVector2Array()
	for i in range(181):
		var t := float(i)/180.0
		spiral.append(Vector2(1130,400)+Vector2.from_angle(t*TAU*2.3)*lerpf(5,94,t))
	draw_polyline(spiral, Color("dda63b"), 12, true)
	for tree: Vector3 in [Vector3(748,690,0.9),Vector3(1385,710,1.0),Vector3(877,610,0.62)]:
		var root := Vector2(tree.x,tree.y)
		draw_line(root,root+Vector2(12,-200)*tree.z,Color("1a002c"),13*tree.z,true)
		for j in range(5):
			var tip := root+Vector2(12,-200)*tree.z
			var dir := Vector2.from_angle(-PI+float(j)*PI/4)
			draw_colored_polygon(PackedVector2Array([tip,tip+dir*115*tree.z,tip+dir.rotated(0.5)*60*tree.z]),Color("1a002c"))
	var edge := frame.duplicate()
	edge.append(frame[0])
	draw_polyline(edge,Color("dac7a7"),4,true)
