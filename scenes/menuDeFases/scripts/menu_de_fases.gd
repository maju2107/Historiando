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

# FASE 1 CÓDIGO
	if FaseCore.fase1_concluida == true:
		fase_1_bloqueada.visible = false
		cadeado.visible = false
	if FaseCore.fase1_concluida == false:
		fase_1_bloqueada.visible = true
		cadeado.visible = true
		
# FASE 2 CÓDIGO
	if FaseCore.fase2_concluida == true:
		fase_2_bloqueada.visible = false
		cadeado_2.visible = false
	if FaseCore.fase2_concluida == false:
		fase_2_bloqueada.visible = true
		cadeado_2.visible = true
		
# FASE 3 CÓDIGO
	if FaseCore.fase3_concluida == true:
		fase_3_bloqueada.visible = false
	if FaseCore.fase3_concluida == false:
		fase_3_bloqueada.visible = true
		
		

func _on_fase_1_pressed() -> void:
	if FaseCore.fase1_concluida == false:
		Transicao.transicionar_para("res://_testes/parkour/mecanica_3.tscn")
	else:
		Transicao.transicionar_para("res://scenes/menuDeFases/fase1/fase_1.tscn")
		


func _on_fase_2_pressed() -> void:
	if FaseCore.fase1_concluida == false:
		null
	if FaseCore.fase1_concluida == true:
		Transicao.transicionar_para("res://scenes/menuDeFases/fase2/fase_2.tscn")
		

func _on_fase_3_pressed() -> void:
	if FaseCore.fase2_concluida == false:
		null
	if FaseCore.fase2_concluida == true:
		Transicao.transicionar_para("res://scenes/menuDeFases/fase3/fase_3.tscn")


func _on_voltar_mp_pressed() -> void:
	Transicao.transicionar_para("res://scenes/telaInicial/TelaInicial.tscn")
