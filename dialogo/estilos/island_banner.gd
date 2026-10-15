extends DialogicLayoutBase
## Full-width top-screen Dialogic textbox, independent of world/camera position.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var panel: Control
var text_node: DialogicNode_DialogText
var name_label: Label

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
	text_node.finished_revealing_text.connect(_fit_banner)
	get_viewport().size_changed.connect(_layout)
	DialogicUtil.autoload().Text.speaker_updated.connect(_speaker_changed)
	_layout()

func _speaker_changed(character: DialogicCharacter) -> void:
	name_label.text = character.display_name.to_upper() if character else ""

func _layout() -> void:
	var viewport_size := get_viewport().get_visible_rect().size
	var factor := clampf(viewport_size.x / 1600.0,.5,1.5)
	panel.position = Vector2(20*factor,22*factor)
	panel.size = Vector2(viewport_size.x-40*factor,205*factor)
	name_label.position = Vector2(45,18)*factor
	name_label.add_theme_font_size_override("font_size",int(23*factor))
	text_node.position = Vector2(45,60)*factor
	text_node.size = Vector2(panel.size.x-90*factor,120*factor)
	text_node.add_theme_font_size_override("normal_font_size",int(42*factor))
	text_node.add_theme_font_size_override("bold_font_size",int(42*factor))
	_fit_banner()

func _fit_banner() -> void:
	var factor := clampf(get_viewport().get_visible_rect().size.x/1600.0,.5,1.5)
	panel.size.y = maxf(170*factor,text_node.position.y+text_node.get_content_height()+36*factor)
