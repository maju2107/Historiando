extends Control
## Touch ownership keeps movement, jumping and camera gestures independent.
var player: CharacterBody3D
var movement := Vector2.ZERO
var _mobile := false
var _move_finger := -1
var _jump_finger := -1
var _camera_finger := -1
var _jump_pending := false
var _stick_center := Vector2.ZERO
var _jump_center := Vector2.ZERO
var _radius := 70.0
var _selector: OptionButton


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_selector = OptionButton.new()
	_selector.add_item("Teclado / Joystick", 0)
	_selector.add_item("Fliperama", 1)
	_selector.add_item("Mobile", 2)
	_selector.position = Vector2(32, 90)
	_selector.custom_minimum_size = Vector2(220, 44)
	_selector.tooltip_text = "Controles (F4)"
	_selector.item_selected.connect(func(index: int): player.control_preset = index)
	add_child(_selector)
	resized.connect(_layout)
	_layout()


func open_selector() -> void:
	_selector.show_popup()


func _layout() -> void:
	reset_touches()
	_radius = clampf(minf(size.x, size.y) * 0.13, 42.0, 85.0)
	_stick_center = Vector2(_radius * 1.7, size.y - _radius * 1.7)
	_jump_center = Vector2(size.x - _radius * 1.5, size.y - _radius * 1.6)
	queue_redraw()


func set_mobile(enabled: bool) -> void:
	_mobile = enabled
	_selector.select(player.control_preset)
	reset_touches()


func reset_touches() -> void:
	if is_instance_valid(player):
		player.camera_rotation = Vector2.ZERO
	movement = Vector2.ZERO
	_move_finger = -1
	_jump_finger = -1
	_camera_finger = -1
	_jump_pending = false
	queue_redraw()


func consume_jump() -> bool:
	var requested := _jump_pending
	_jump_pending = false
	return requested


func _notification(what: int) -> void:
	if what == NOTIFICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		reset_touches()


func _input(event: InputEvent) -> void:
	# Release owned fingers even when another UI consumes the release.
	if event is InputEventScreenTouch and (not event.pressed or event.canceled):
		if event.index == _move_finger:
			_move_finger = -1
			movement = Vector2.ZERO
		if event.index == _jump_finger:
			_jump_finger = -1
		if event.index == _camera_finger:
			_camera_finger = -1
		queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not _mobile or not player.can_move or player.is_dead:
		return
	if event is InputEventScreenTouch and event.pressed and not event.canceled:
		if event.position.distance_to(_stick_center) <= _radius * 1.25:
			if _move_finger == -1:
				_move_finger = event.index
				_update_stick(event.position)
		elif event.position.distance_to(_jump_center) <= _radius * 0.8:
			if _jump_finger == -1:
				_jump_finger = event.index
				_jump_pending = true
		elif _camera_finger == -1:
			_camera_finger = event.index
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		if event.index == _move_finger:
			_update_stick(event.position)
		elif event.index == _camera_finger:
			player.camera_rotation += event.relative * deg_to_rad(player.mouse_sensitivity)
		get_viewport().set_input_as_handled()
	queue_redraw()


func _update_stick(position_on_screen: Vector2) -> void:
	var offset := ((position_on_screen - _stick_center) / _radius).limit_length()
	var strength := offset.length()
	movement = offset.normalized() * ((strength - 0.12) / 0.88) if strength > 0.12 else Vector2.ZERO


func _draw() -> void:
	if not _mobile:
		return
	var outline := Color(1, 1, 1, 0.75)
	draw_circle(_stick_center, _radius, Color(0.08, 0.1, 0.14, 0.4))
	draw_arc(_stick_center, _radius, 0, TAU, 64, outline, 2.0, true)
	draw_circle(_stick_center + movement * _radius * 0.65, _radius * 0.4, Color(1, 1, 1, 0.65))
	var jump_radius := _radius * 0.8
	draw_circle(_jump_center, jump_radius, Color(1, 1, 1, 0.55 if _jump_finger >= 0 else 0.25))
	draw_arc(_jump_center, jump_radius, 0, TAU, 64, outline, 2.0, true)
	var arrow := PackedVector2Array([
		_jump_center + Vector2(-0.3, 0.05) * _radius,
		_jump_center + Vector2(0, -0.25) * _radius,
		_jump_center + Vector2(0.3, 0.05) * _radius,
	])
	draw_polyline(arrow, outline, 5.0, true)
	draw_line(_jump_center + Vector2(0, -0.25) * _radius, _jump_center + Vector2(0, 0.3) * _radius, outline, 5.0, true)
