extends RefCounted
## Stable print-like dots: staggered rows, soft falloff and slight irregularity.
static func patch(target: CanvasItem, area: Rect2, tint: Color, spacing: float = 13.0, radius: float = 2.0) -> void:
	var rows := int(area.size.y / spacing)
	var columns := int(area.size.x / spacing)
	for row in range(rows+1):
		for column in range(columns+1):
			var phase := float(row*37+column*19)
			var point := Vector2(column*spacing+fmod(float(row),2.0)*spacing*0.5,row*spacing)
			point += Vector2(sin(phase*1.71),cos(phase*0.93))*spacing*0.065
			var distance := ((point-area.size*0.5)/(area.size*0.5)).length()
			var density := smoothstep(1.0,0.1,distance)
			if density < 0.025: continue
			var color := tint
			color.a *= sqrt(density)*(0.86+0.14*sin(phase))
			target.draw_circle(area.position+point,radius*(0.35+0.65*density),color,true,-1,true)
