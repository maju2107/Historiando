extends Panel

func _process(delta: float) -> void: # tirar símbolo de bloqueio do mouse
	if Input.get_current_cursor_shape() == CURSOR_FORBIDDEN:
		DisplayServer.cursor_set_shape(DisplayServer.CURSOR_ARROW)
		
var dataFundo 

func _notification(what: int) -> void: # impedir que o item suma na área não delimitada
	if what == Node.NOTIFICATION_DRAG_BEGIN:
		dataFundo = get_viewport().gui_get_drag_data()
	if what == Node.NOTIFICATION_DRAG_END:
		if not is_drag_successful():
			if dataFundo:
				dataFundo.icone.show()
				dataFundo = null
