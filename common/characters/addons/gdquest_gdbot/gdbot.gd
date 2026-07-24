extends Node3D

@export_file("*.dtl") var timeline_path := "res://dialogo/linha_do_tempo/timeline.dtl"

@onready var interaction_area: Area3D = $InteractionArea
@onready var interaction_prompt: Label3D = $InteractionPrompt
@onready var dialogue_bubble_anchor: Marker3D = $DialogueBubbleAnchor

var player_nearby: CharacterBody3D
var dialogue_active := false
var player_could_move := true


func _ready() -> void:
	interaction_prompt.hide()
	interaction_area.body_entered.connect(_on_body_entered)
	interaction_area.body_exited.connect(_on_body_exited)

	if not Dialogic.timeline_ended.is_connected(_on_timeline_ended):
		Dialogic.timeline_ended.connect(_on_timeline_ended)


func _unhandled_input(event: InputEvent) -> void:
	if (
		player_nearby
		and not dialogue_active
		and event.is_action_pressed("interagir")
	):
		get_viewport().set_input_as_handled()
		_start_dialogue()


func _on_body_entered(body: Node3D) -> void:
	if body is CharacterBody3D and body.is_in_group("player"):
		player_nearby = body
		_update_prompt()


func _on_body_exited(body: Node3D) -> void:
	if body == player_nearby:
		player_nearby = null
		_update_prompt()


func _start_dialogue() -> void:
	if Dialogic.current_timeline != null:
		return

	dialogue_active = true
	interaction_prompt.hide()

	if "can_move" in player_nearby:
		player_could_move = player_nearby.can_move
		player_nearby.can_move = false
		player_nearby.velocity = Vector3.ZERO

	var layout: Node = Dialogic.start(timeline_path)
	if layout and layout.has_method("register_character"):
		var player_anchor: Node = player_nearby.get_node_or_null("DialogueBubbleAnchor")
		if player_anchor == null:
			player_anchor = player_nearby

		layout.register_character(
			load("res://dialogo/personagens/player.dch"),
			player_anchor
		)
		layout.register_character(
			load("res://dialogo/personagens/personagem_secundario.dch"),
			dialogue_bubble_anchor
		)
	else:
		push_warning("O estilo atual do Dialogic não aceita balões ligados a personagens.")


func _on_timeline_ended() -> void:
	if not dialogue_active:
		return

	dialogue_active = false
	if is_instance_valid(player_nearby) and "can_move" in player_nearby:
		player_nearby.can_move = player_could_move
	_update_prompt()


func _update_prompt() -> void:
	interaction_prompt.visible = is_instance_valid(player_nearby) and not dialogue_active
