extends CharacterBody3D

@export var npc_name: String = "NPC"
@export var timeline_name: String = ""

func interagir():

	print("Conversando com ", npc_name)

	# Quando instalarmos o Dialogic:
	# Dialogic.start(timeline_name)
