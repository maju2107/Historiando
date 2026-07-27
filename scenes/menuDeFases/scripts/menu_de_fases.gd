extends Node2D

@onready var fase_1: Button = %Fase1
@onready var fase_2: Button = %Fase2
@onready var fase_3: Button = %Fase3

@onready var fase_1_bloqueada: ColorRect = $fase1_bloqueada
@onready var fase_2_bloqueada: ColorRect = $fase2_bloqueada
@onready var fase_3_bloqueada: ColorRect = $fase3_bloqueada

@onready var cadeado: Sprite2D = $cadeado
@onready var cadeado_2: Sprite2D = $cadeado2

func _ready() -> void:
	fase_1.grab_focus()

	var fase_2_desbloqueada: bool = FaseCore.fase1_concluida
	var fase_3_desbloqueada: bool = FaseCore.fase2_concluida

	# A primeira fase sempre fica disponível. As seguintes dependem da anterior.
	fase_1_bloqueada.visible = not FaseCore.fase1_concluida
	fase_2_bloqueada.visible = not FaseCore.fase2_concluida
	fase_3_bloqueada.visible = not FaseCore.fase3_concluida
	cadeado.visible = not fase_2_desbloqueada
	cadeado_2.visible = not fase_3_desbloqueada
	fase_1.disabled = false
	fase_2.disabled = not fase_2_desbloqueada
	fase_3.disabled = not fase_3_desbloqueada

func _on_fase_1_pressed() -> void:
	Transicao.transicionar_para("res://scenes/menuDeFases/fase1/fase_1.tscn")


func _on_fase_2_pressed() -> void:
	if FaseCore.fase1_concluida:
		Transicao.transicionar_para("res://scenes/menuDeFases/fase2/fase_2.tscn")
		

func _on_fase_3_pressed() -> void:
	if FaseCore.fase2_concluida:
		Transicao.transicionar_para("res://scenes/menuDeFases/fase3/fase_3.tscn")


func _on_voltar_mp_pressed() -> void:
	Transicao.transicionar_para("res://scenes/telaInicial/TelaInicial.tscn")
