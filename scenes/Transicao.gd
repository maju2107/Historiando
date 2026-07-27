extends CanvasLayer

@onready var anim := $AnimationPlayer
@onready var tela := $ColorRect
var em_transicao := false

func transicionar_para(cena: String) -> void:
	if em_transicao:
		return
	if not ResourceLoader.exists(cena):
		push_error("Cena não encontrada: %s" % cena)
		return

	em_transicao = true
	anim.play("fade_out")
	await anim.animation_finished
	var erro := get_tree().change_scene_to_file(cena)
	if erro != OK:
		push_error("Falha ao carregar a cena %s (erro %d)." % [cena, erro])
	anim.play("fade_in")
	await anim.animation_finished
	em_transicao = false
