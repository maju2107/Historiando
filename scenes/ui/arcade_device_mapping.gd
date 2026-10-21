extends Node
## The Leonardo exposes ordinary HID buttons; button 11 is not a D-pad Up.
## Supply an SDL mapping so its X/Y axes (or actual hat) drive directions.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	Input.joy_connection_changed.connect(_connection_changed)
	for device in Input.get_connected_joypads(): _configure(device)

func _connection_changed(device: int,connected: bool) -> void:
	if connected: _configure.call_deferred(device)

func _configure(device: int) -> void:
	if not "leonardo" in Input.get_joy_name(device).to_lower(): return
	var guid := Input.get_joy_guid(device)
	if guid.is_empty(): return
	Input.add_joy_mapping(guid+",Historiando Arcade Leonardo,a:b0,b:b1,x:b2,y:b3,back:b6,start:b7,leftshoulder:b4,rightshoulder:b5,leftx:a0,lefty:a1,dpup:h0.1,dpright:h0.2,dpdown:h0.4,dpleft:h0.8,",true)
	# Discard directional states received before the device had its mapping.
	for button in [JOY_BUTTON_DPAD_UP,JOY_BUTTON_DPAD_DOWN,JOY_BUTTON_DPAD_LEFT,JOY_BUTTON_DPAD_RIGHT]:
		var release := InputEventJoypadButton.new()
		release.device = device
		release.button_index = button
		release.pressed = false
		Input.parse_input_event(release)
