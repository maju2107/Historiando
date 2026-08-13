extends Panel

@onready var icone: TextureRect = $icone
@export var item : ItemData :
	set(valor):
		item = valor
		if is_node_ready() and item:
			update_ui()


func _ready() -> void:
	update_ui()

func update_ui() -> void:
	if not item:
		icone.texture = null
		return
		
	icone.texture = item.icone
	icone.show()
	tooltip_text = item.item_nome 
	
	
func _get_drag_data(_at_position: Vector2) -> Variant:
	if not item : # se nao tiver um item não retorna nada 
		return 
		
	var preview = duplicate() # se tiver, duplica o panel 
	var centraliza = Control.new()
	centraliza.add_child(preview)
	preview.position -= Vector2(25,25)
	preview.self_modulate = Color.TRANSPARENT
	centraliza.modulate = Color(centraliza.modulate, 0.5)
	
	set_drag_preview(centraliza) # define essa cópia como a imagem que aparece enquanto você arrasta
	icone.hide()
	return self
	
func _can_drop_data(_at_position: Vector2, _data: Variant) -> bool:
	return true
		
		
func _drop_data(_at_position: Vector2, data: Variant) -> void:
	var trocaLugar = item
	item = data.item
	data.item = trocaLugar
	icone.show()
	data.icone.show()
	update_ui()
	data.update_ui()
