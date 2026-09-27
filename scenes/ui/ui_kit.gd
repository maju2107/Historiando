extends RefCounted
const INK := Color("1a002c")
const PAPER := Color("dac7a7")
const GOLD := Color("dda63b")
const CLAY := Color("ce6035")
const GREEN := Color("2f5143")
const BOLD = preload("res://common/fonts/historiando/BarlowCondensed-Bold.ttf")
const BODY = preload("res://common/fonts/historiando/BarlowCondensed-Medium.ttf")
const DISPLAY = preload("res://common/fonts/historiando/HistoriandoMosaico-Regular.ttf")
const ComicButton = preload("res://scenes/ui/comic_button.gd")
const BRAND_TEXTURES := {
	"res://assets/ui/historiando/brand_symbol.svg": preload("res://assets/ui/historiando/brand_symbol.svg"),
	"res://assets/ui/historiando/brand_group_28.svg": preload("res://assets/ui/historiando/brand_group_28.svg"),
	"res://assets/ui/historiando/brand_wordmark.svg": preload("res://assets/ui/historiando/brand_wordmark.svg"),
}

static func label(parent: Node, words: String, box: Rect2, font_size: int = 26, color: Color = PAPER, font: Font = BODY) -> Label:
	var item := Label.new()
	item.text = words
	item.position = box.position
	item.size = box.size
	item.add_theme_font_override("font", font)
	item.add_theme_font_size_override("font_size", font_size)
	item.add_theme_color_override("font_color", color)
	item.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(item)
	return item

static func button(parent: Node, words: String, box: Rect2, action: Callable, color: Color = GOLD, small: bool = false) -> Button:
	var item := ComicButton.new()
	item.text = words
	item.position = box.position
	item.size = box.size
	item.fill = color
	item.compact = small
	parent.add_child(item)
	item.pressed.connect(action)
	return item

static func rect(parent: Node, box: Rect2, color: Color) -> ColorRect:
	var item := ColorRect.new()
	item.position = box.position
	item.size = box.size
	item.color = color
	item.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(item)
	return item

static func texture(parent: Node, path: String, box: Rect2) -> TextureRect:
	var item := TextureRect.new()
	item.texture = BRAND_TEXTURES[path] if path in BRAND_TEXTURES else load(path)
	item.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	item.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	item.position = box.position
	item.size = box.size
	item.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	item.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(item)
	return item

static func brand(parent: Node, box: Rect2, symbol: bool = false) -> TextureRect:
	var item := texture(parent,"res://assets/ui/historiando/brand_symbol.svg" if symbol else "res://assets/ui/historiando/brand_group_28.svg",box)
	item.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	return item
