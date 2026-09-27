extends CanvasLayer
## One global pause owner, including cursor restoration and persistent settings.
const Interface = preload("res://scenes/ui/interface.gd")
var pause_screen: Control
var previous_mouse_mode := Input.MOUSE_MODE_VISIBLE
var game_over := false

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 90
	Interface.apply_settings()

func _input(event: InputEvent) -> void:
	if not event.is_action_pressed("menu") or event.is_echo(): return
	if is_instance_valid(pause_screen):
		if is_instance_valid(pause_screen.modal):
			pause_screen.dismiss_modal()
			get_viewport().set_input_as_handled()
			return
		if game_over:
			get_viewport().set_input_as_handled()
			return
		if pause_screen.screen == "pause": toggle_pause()
		else: pause_screen.show_screen("pause")
		get_viewport().set_input_as_handled()
	elif get_tree().get_nodes_in_group("historiando_menu").is_empty():
		toggle_pause()
		get_viewport().set_input_as_handled()

func toggle_pause() -> void:
	if is_instance_valid(pause_screen):
		pause_screen.queue_free()
		pause_screen = null
		get_tree().paused = false
		game_over = false
		Input.set_mouse_mode(previous_mouse_mode)
		return
	previous_mouse_mode = Input.get_mouse_mode()
	get_tree().paused = true
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	pause_screen = Interface.new()
	pause_screen.initial_screen = "pause"
	add_child(pause_screen)
	pause_screen.close_requested.connect(toggle_pause)
	pause_screen.restart_requested.connect(_restart)

func show_game_over() -> void:
	if not is_instance_valid(pause_screen): toggle_pause()
	game_over = true
	pause_screen.show_screen("retry")

func _restart() -> void:
	toggle_pause()
	get_tree().reload_current_scene()
