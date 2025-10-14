extends Area2D

var dragging := false
var offset := Vector2.ZERO
var target_slot_name := "lacuna1"  # Nome da lacuna onde esse bloco deve encaixar

func _input(event):
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			dragging = true
			offset = global_position - get_global_mouse_position()
		else:
			dragging = false
			verificar_encaixe()

func _process(delta):
	if dragging:
		global_position = get_global_mouse_position() + offset

func verificar_encaixe():
	for area in get_overlapping_areas():
		if area.name == target_slot_name:
			global_position = area.global_position
			set_process_input(false)  # trava o bloco
			print("✅ Encaixe correto em %s!" % target_slot_name)
			return
	print("❌ Encaixe incorreto.")
