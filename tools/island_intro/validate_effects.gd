extends SceneTree
## Checks the shared burst at the sizes used by the opening and ending.
const Burst = preload("res://_testes/cenario_ilha/intro/comic_reaction.gd")
const Kit = preload("res://scenes/ui/ui_kit.gd")
var failures := 0
var measurements: Array = []

func _initialize() -> void:
	root.hide()
	call_deferred("_run")

func check(value: bool,message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func inspect(mark: Control) -> void:
	var label: Label = mark.title
	var font_size: int = label.get_theme_font_size("font_size")
	check(label.text.replace("\n"," ") == mark.words,"Effect lost words: "+mark.words)
	check(font_size >= 20,"Effect text is too small at its authored size: "+mark.words)
	for line in label.text.split("\n"):
		check(Kit.BOLD.get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x <= label.size.x+.1,"Effect text overflows horizontally: "+mark.words)
	check(label.get_line_height()*label.get_line_count() <= label.size.y+.1,"Effect text overflows vertically: "+mark.words)
	# Check the actual Label bounds against the drawn solid burst, not its
	# much larger spike-to-spike Control bounds.
	var polygon := PackedVector2Array()
	for index in 24:
		var angle := TAU*index/24
		var radius := 1.0 if index%2 == 0 else .77
		polygon.append(mark.size/2+Vector2(cos(angle)*mark.size.x*.48,sin(angle)*mark.size.y*.45)*radius)
	var bounds := label.get_rect()
	for corner in [bounds.position,bounds.end,Vector2(bounds.end.x,bounds.position.y),Vector2(bounds.position.x,bounds.end.y)]:
		check(Geometry2D.is_point_in_polygon(corner,polygon),"Text bounds leave the solid burst: "+mark.words)
	measurements.append({"words":mark.words,"size":[mark.size.x,mark.size.y],"font_size":font_size,"lines":label.get_line_count()})

func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1200,640)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var background := ColorRect.new()
	background.color = Kit.INK
	background.size = viewport.size
	viewport.add_child(background)
	var samples := [
		["TODOS OS FRAGMENTOS!",Vector2(480,220),Vector2(40,60)],
		["DE VOLTA PRA CASA!",Vector2(480,220),Vector2(640,60)],
		["PLEISTOCENO",Vector2(400,170),Vector2(50,380)],
		["?!",Vector2(180,160),Vector2(590,380)],
		["?!",Vector2(185,170),Vector2(920,380)]
	]
	for sample in samples:
		var mark := Burst.new()
		mark.words = sample[0]
		mark.size = sample[1]
		mark.position = sample[2]
		viewport.add_child(mark)
		await process_frame
		inspect(mark)
	# Resizing must refit an existing burst, including its Label minimum size.
	var resized := Burst.new()
	resized.words = "DE VOLTA PRA CASA!"
	resized.size = Vector2(480,220)
	viewport.add_child(resized)
	await process_frame
	resized.size = Vector2(400,170)
	await process_frame
	inspect(resized)
	resized.queue_free()
	await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png("res://art/island_intro/previews/ending/effect_text_fit.png")
	var file := FileAccess.open("res://art/island_intro/effect_text_validation.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"failures":failures,"measurements":measurements},"\t"))
	viewport.queue_free()
	await process_frame
	print("COMIC_EFFECT_TEXT ","PASS" if failures == 0 else "FAIL"," failures=",failures)
	quit(1 if failures else 0)
