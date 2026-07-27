extends Node2D

func _on_area_2d_body_entered(body: Node2D) -> void:
	if not body is CharacterBody2D:
		return

	FaseCore.concluir_fase(2)
	Transicao.transicionar_para("res://scenes/menuDeFases/MenuDeFases.tscn")
