extends ColorRect

var ja_iniciou := false

func iniciar_jogo():
	if ja_iniciou:
		return
	ja_iniciou = true
	Transicao.transicionar_para("res://scenes/telaInicial/TelaInicial.tscn")
	

func _on_comecar_pressed() -> void:
		iniciar_jogo()
		
		
func _input(event):
	
	# teclado (pressionar qualquer tecla)
	if event is InputEventKey and event.pressed and not event.echo:
		iniciar_jogo()
		

	#if event.is_action_pressed("iniciar_jogo"): (usar quando implementar o input map (join stick))
		#iniciar_jogo()
