extends Panel


@onready var icone: TextureRect = $icone


@export var item: ItemData:
	set(valor):
		item = valor
		
		if is_node_ready():
			update_ui()


func _ready() -> void:
	update_ui()


func update_ui() -> void:
	if not item:
		icone.texture = null
		icone.hide()
		tooltip_text = ""
		return
	
	icone.texture = item.icone
	icone.show()
	tooltip_text = item.item_nome


# =========================================================
# PEGAR ITEM DO SLOT
# =========================================================

func _get_drag_data(_at_position: Vector2) -> Variant:
	if not item:
		return
	
	var preview = duplicate()
	
	var centraliza := Control.new()
	centraliza.add_child(preview)
	
	preview.position -= Vector2(25, 25)
	preview.self_modulate = Color.TRANSPARENT
	
	centraliza.modulate = Color(centraliza.modulate, 0.5)
	
	set_drag_preview(centraliza)
	
	icone.hide()
	
	return self


# =========================================================
# RECEBER ITEM DE OUTRO SLOT
# =========================================================

func _can_drop_data(_at_position: Vector2, _data: Variant) -> bool:
	return true


func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if not data:
		return
	
	var trocaLugar: ItemData = item
	
	item = data.item
	data.item = trocaLugar
	
	update_ui()
	data.update_ui()
