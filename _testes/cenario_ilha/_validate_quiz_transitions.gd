extends SceneTree
const Bubble = preload("res://_testes/cenario_ilha/parkour/quiz_bubble.gd")
const Pair = preload("res://_testes/cenario_ilha/parkour/answer_pair.gd")
const Sign = preload("res://_testes/cenario_ilha/parkour/answer_sign.gd")
var failures := 0

func _initialize() -> void:
	root.hide()
	call_deferred("_run")

func check(value: bool,message: String) -> void:
	if not value:
		failures += 1
		push_error(message)

func _run() -> void:
	for reduced in [false,true]:
		var bubble := Bubble.new()
		bubble.reduced_motion = reduced
		root.add_child(bubble)
		var pair := Pair.new()
		pair.reduced_motion = reduced
		root.add_child(pair)
		for index in 2:
			var sign := Sign.new()
			sign.words = "Era do Gelo" if index == 0 else "Era dos Dinossauros"
			pair.add_child(sign)
		pair.hide()
		bubble.present(0,"O Pleistoceno faz parte de qual era?")
		pair.present()
		check(bubble.modulate.a == 0 and pair.get_child(0).opacity == 0,"Entrance must begin transparently without a one-frame flash")
		await create_timer(.08 if reduced else .23).timeout
		check(bubble.modulate.a > 0 and bubble.modulate.a < 1,"Question must pass through intermediate opacity")
		check(pair.get_child(0).opacity > 0 and pair.get_child(0).opacity < 1,"Answer plate must pass through intermediate opacity")
		var alpha: float = bubble.modulate.a
		var plate_alpha: float = pair.get_child(0).opacity
		var lift: float = pair.get_child(0).lift
		paused = true
		for frame in 10: await process_frame
		check(bubble.modulate.a == alpha and pair.get_child(0).opacity == plate_alpha and pair.get_child(0).lift == lift,"Pause must freeze presentation tweens")
		paused = false
		bubble.present(0,"O Pleistoceno faz parte de qual era?")
		pair.present()
		check(bubble.modulate.a == alpha and pair.get_child(0).opacity == plate_alpha,"Checkpoint-to-question landing must not restart the fade")
		bubble._layout()
		check(bubble.modulate.a == alpha,"Relayout must preserve the current fade")
		if reduced:
			check(is_zero_approx(bubble._slide) and is_zero_approx(lift),"Reduced motion must use opacity without spatial movement")
		else:
			check(pair.get_child(0).opacity > pair.get_child(1).opacity,"Answers should enter with a subtle left-to-right stagger")
		await create_timer(.7).timeout
		check(is_equal_approx(bubble.modulate.a,1) and is_equal_approx(pair.get_child(0).opacity,1),"Entrance must finish at full opacity")
		bubble.dismiss()
		pair.dismiss()
		check(bubble.visible and pair.visible,"Dismissal must fade rather than instantly hide")
		await create_timer(.06 if reduced else .12).timeout
		alpha = bubble.modulate.a
		plate_alpha = pair.get_child(0).opacity
		check(alpha > 0 and alpha < 1 and plate_alpha > 0 and plate_alpha < 1,"Dismissal must have visible intermediate opacity")
		# Reopen before the outgoing callback: an old hide must never win later.
		bubble.present(0,"O Pleistoceno faz parte de qual era?")
		pair.present()
		check(bubble.modulate.a == alpha and pair.get_child(0).opacity == plate_alpha,"An interrupted fade must reverse from its current opacity")
		await create_timer(.7).timeout
		check(bubble.visible and pair.visible and bubble.showing and pair.showing,"An obsolete dismiss callback hid a reopened question")
		bubble.dismiss()
		pair.dismiss()
		await create_timer(.4).timeout
		check(not bubble.visible and not pair.visible,"Dismissal must eventually hide both presentation nodes")
		check(is_zero_approx(bubble.modulate.a) and is_zero_approx(pair.get_child(0).opacity),"No residual opacity may remain after dismissal")
		bubble.queue_free()
		pair.queue_free()
		await process_frame
		print("QUIZ_TRANSITIONS_MODE_OK reduced=",reduced)
	FileAccess.open("res://art/island_intro/quiz_transition_validation.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"entry_and_exit_opacity":true,"pause":true,"interrupted_fades":true,"repeated_landing":true,"reduced_motion":true},"\t"))
	print("QUIZ_TRANSITIONS ","PASS" if failures == 0 else "FAIL"," failures=",failures)
	quit(0 if failures == 0 else 1)
