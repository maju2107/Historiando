extends Control
## Touch ownership keeps movement, jumping and camera gestures independent.
const Kit = preload("res://scenes/ui/ui_kit.gd")
const SPIRAL = preload("res://assets/ui/historiando/controls/joystick_spiral.svg")
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


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(_layout)
	_layout()


func _layout() -> void:
	reset_touches()
	# Larger thumb targets, lifted clear of the bottom edge / gesture bar.
	_radius = clampf(minf(size.x, size.y) * 0.19, 64.0, 112.0)
	_stick_center = Vector2(_radius * 1.6, size.y - _radius * 1.9)
	_jump_center = Vector2(size.x - _radius * 1.6, size.y - _radius * 1.9)
	queue_redraw()


func set_mobile(enabled: bool) -> void:
	_mobile = enabled
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
	if not _mobile or not is_visible_in_tree() or not player.can_move or player.is_dead:
		return
	if event is InputEventScreenTouch and event.pressed and not event.canceled:
		if event.position.distance_to(_stick_center) <= _radius * 1.25:
			if _move_finger == -1:
				_move_finger = event.index
				_update_stick(event.position)
		elif event.position.distance_to(_jump_center) <= _radius * 0.9:
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
	var line_width := maxf(2.5,_radius*.035)
	var ink := Color(Kit.INK,.85)
	draw_circle(_stick_center+Vector2(3,5),_radius+3,Color(Kit.INK,.45))
	draw_circle(_stick_center,_radius,Color(Kit.INK,.64))
	draw_arc(_stick_center,_radius,0,TAU,96,Kit.PAPER,line_width,true)
	draw_arc(_stick_center,_radius*.88,0,TAU,96,Color(Kit.GOLD,.65),line_width*.6,true)
	# Small compass marks frame the logo without obscuring the world.
	for direction in [Vector2.UP,Vector2.DOWN,Vector2.LEFT,Vector2.RIGHT]:
		draw_line(_stick_center+direction*_radius*.76,_stick_center+direction*_radius*.86,Kit.GOLD,line_width,true)
	var thumb := _stick_center+movement*_radius*.48
	var thumb_radius := _radius*.55
	draw_circle(thumb+Vector2(2,3),thumb_radius+2,ink)
	draw_circle(thumb,thumb_radius,Color(Kit.CLAY,.96))
	draw_arc(thumb,thumb_radius,0,TAU,64,Kit.GOLD,line_width,true)
	draw_texture_rect(SPIRAL,Rect2(thumb-Vector2.ONE*thumb_radius*.87,Vector2.ONE*thumb_radius*1.74),false)
	var jump_radius := _radius*.9
	var tone := Kit.GOLD.lightened(.16) if _jump_finger>=0 else Kit.GOLD
	draw_circle(_jump_center+Vector2(3,5),jump_radius+3,ink)
	draw_circle(_jump_center,jump_radius,Color(tone,.92))
	draw_arc(_jump_center,jump_radius,0,TAU,96,Kit.INK,line_width*1.3,true)
	draw_arc(_jump_center,jump_radius*.87,0,TAU,96,Kit.PAPER,line_width*.7,true)
	var arrow := PackedVector2Array([
		_jump_center+Vector2(-.26,-.05)*_radius,
		_jump_center+Vector2(0,-.33)*_radius,
		_jump_center+Vector2(.26,-.05)*_radius])
	draw_polyline(arrow,Kit.INK,line_width*1.8,true)
	draw_line(_jump_center+Vector2(0,-.31)*_radius,_jump_center+Vector2(0,.16)*_radius,Kit.INK,line_width*1.8,true)
	var font_size := int(_radius*.27)
	var caption := "PULAR"
	var width := Kit.BOLD.get_string_size(caption,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x
	draw_string(Kit.BOLD,_jump_center+Vector2(-width/2,_radius*.54),caption,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size,Kit.INK)
