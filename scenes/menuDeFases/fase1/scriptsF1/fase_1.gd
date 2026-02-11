extends Node2D

func _on_area_2d_body_entered(body: Node2D) -> void:
	Transicao.transicionar_para("res://scenes/menuDeFases/MenuDeFases.tscn")
	FaseCore.fase1_concluida = true
