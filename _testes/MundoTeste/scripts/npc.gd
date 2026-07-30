extends CharacterBody3D

@export var npc_name: String = "NPC"
@export var timeline_name: String = ""

@export var speed := 2.0

@onready var ponto_a: Marker3D = $"../../ponto_A"
@onready var ponto_b: Marker3D = $"../../ponto_B"

var destino

func _ready():
	destino = ponto_b

func _physics_process(delta):

	var direcao = destino.global_position - global_position

	if direcao.length() < 0.2:

		if destino == ponto_a:
			destino = ponto_b
		else:
			destino = ponto_a

	velocity = direcao.normalized() * speed
	
	move_and_slide()
