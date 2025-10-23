extends CanvasLayer

@onready var anim := $AnimationPlayer
@onready var tela := $ColorRect

func transicionar_para(cena: String):
	anim.play("fade_out")
	await anim.animation_finished
	get_tree().change_scene_to_file(cena)
	anim.play("fade_in")
	await anim.animation_finished
