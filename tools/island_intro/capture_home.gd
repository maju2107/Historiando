extends SceneTree
func _initialize() -> void:
	root.hide()
	call_deferred("_run")
func _run() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1600,900)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var home := preload("res://scenes/ui/interface.gd").new()
	viewport.add_child(home)
	for i in 30: await process_frame
	await create_timer(.25).timeout
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://art/island_intro/previews/main_screen.png")
	print("CORRECTED_LOGO_HOME_CAPTURED")
	viewport.queue_free()
	await process_frame
	quit()
