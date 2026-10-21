extends TextureRect
## Shared corner badge and B shortcut for the opening and ending skip buttons.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var button: Button

func _ready() -> void:
	name = "SkipBPrompt"
	button = get_parent() as Button
	texture = preload("res://assets/ui/historiando/controls/button_b.svg")
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	offset_left = -30
	offset_right = 10
	offset_top = -18
	offset_bottom = 22
	_update_visibility()

func _process(_delta: float) -> void:
	_update_visibility()

func _update_visibility() -> void:
	visible = not Kit.uses_touch_controls(get_tree())

func _unhandled_input(event: InputEvent) -> void:
	if get_tree().paused or not button.is_visible_in_tree() or button.disabled: return
	if event is InputEventJoypadButton and event.button_index == JOY_BUTTON_B and event.pressed:
		get_viewport().set_input_as_handled()
		button.pressed.emit()
