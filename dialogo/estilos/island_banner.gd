extends DialogicLayoutBase
## Full-width top-screen Dialogic textbox, independent of world/camera position.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var panel: Control
var text_node: DialogicNode_DialogText
var name_label: Label
var advance_prompt: TextureRect

func _ready() -> void:
	set("layer",60)
	panel = preload("res://dialogo/estilos/island_banner_panel.gd").new()
	panel.name = "SpeechBanner"
	add_child(panel)
	name_label = Kit.label(panel,"YARA",Rect2(),24,Kit.CLAY,Kit.BOLD)
	text_node = DialogicNode_DialogText.new()
	text_node.name = "DialogText"
	text_node.textbox_root = panel
	text_node.fit_content = true
	text_node.scroll_active = false
	text_node.add_theme_font_override("normal_font",Kit.BOLD)
	text_node.add_theme_font_override("bold_font",Kit.BOLD)
	text_node.add_theme_color_override("default_color",Kit.INK)
	panel.add_child(text_node)
	text_node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Suppress Dialogic's global mouse handler. Unhandled input lets real UI
	# (pause and skip) consume clicks before screen-wide dialogue advance.
	var input_scope := Control.new()
	input_scope.name = "DialogueInputScope"
	input_scope.mouse_filter = Control.MOUSE_FILTER_IGNORE
	input_scope.add_to_group("dialogic_input")
	panel.add_child(input_scope)
	advance_prompt = Kit.texture(panel,"res://assets/ui/historiando/controls/button_a.svg",Rect2())
	advance_prompt.name = "APrompt"
	text_node.started_revealing_text.connect(_fit_banner)
	text_node.finished_revealing_text.connect(_fit_banner)
	get_viewport().size_changed.connect(_layout)
	DialogicUtil.autoload().Text.speaker_updated.connect(_speaker_changed)
	_layout()

func _speaker_changed(character: DialogicCharacter) -> void:
	name_label.text = character.display_name.to_upper() if character else ""

func _layout() -> void:
	var viewport_size := get_viewport().get_visible_rect().size
	var factor := clampf(viewport_size.x / 1600.0,.65,1.25)
	panel.position = Vector2(20*factor,22*factor)
	panel.size = Vector2(viewport_size.x-40*factor,205*factor)
	name_label.position = Vector2(45,18)*factor
	name_label.add_theme_font_size_override("font_size",int(23*factor))
	text_node.position = Vector2(45,60)*factor
	text_node.size = Vector2(panel.size.x-90*factor,80*factor)
	text_node.add_theme_font_size_override("normal_font_size",int(38*factor))
	text_node.add_theme_font_size_override("bold_font_size",int(38*factor))
	advance_prompt.size = Vector2.ONE*46*factor
	_fit_banner()

func _fit_banner() -> void:
	if not is_instance_valid(advance_prompt): return
	var factor := clampf(get_viewport().get_visible_rect().size.x/1600.0,.65,1.25)
	panel.size.y = text_node.position.y+maxf(text_node.get_content_height(),48*factor)+42*factor
	# Center the badge across the lower edge, like Y on the pause button.
	advance_prompt.position = panel.size-Vector2(58,30)*factor

func _process(_delta: float) -> void:
	advance_prompt.visible = not Kit.uses_touch_controls(get_tree())

func _unhandled_input(event: InputEvent) -> void:
	if not panel.is_visible_in_tree() or get_tree().paused: return
	var advance: bool = event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT
	# With mouse emulation on, the generated mouse event goes through GUI first
	# and advances once. Raw touch also works when emulation is disabled.
	if event is InputEventScreenTouch and not ProjectSettings.get_setting("input_devices/pointing/emulate_mouse_from_touch",true):
		advance = event.pressed and not event.canceled
	if advance:
		_advance()
		get_viewport().set_input_as_handled()

func _advance() -> void:
	if not panel.is_visible_in_tree() or get_tree().paused: return
	DialogicUtil.autoload().Inputs.handle_input()
