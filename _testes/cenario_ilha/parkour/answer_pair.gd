extends Node3D
## Keep the physical choice immediate while its two labels ease in/out together.
var showing := false
var reduced_motion := false
var _transition: Tween

func present() -> void:
	if showing: return
	showing = true
	if _transition and _transition.is_valid(): _transition.kill()
	if not visible:
		for plate in get_children():
			plate.opacity = 0.0
			plate.lift = 0.0 if reduced_motion else -.14
	show()
	_transition = create_tween().set_parallel(true)
	for index in get_child_count():
		var plate := get_child(index)
		var delay := 0.0 if reduced_motion else .12+index*.07
		var seconds := .16 if reduced_motion else .42
		_transition.tween_property(plate,"opacity",1.0,seconds).set_delay(delay).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		_transition.tween_property(plate,"lift",0.0,seconds).set_delay(delay).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)

func dismiss() -> void:
	if not showing: return
	showing = false
	if _transition and _transition.is_valid(): _transition.kill()
	_transition = create_tween().set_parallel(true)
	for plate in get_children():
		var seconds := .14 if reduced_motion else .28
		_transition.tween_property(plate,"opacity",0.0,seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		_transition.tween_property(plate,"lift",0.0 if reduced_motion else .09,seconds).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_transition.chain().tween_callback(hide)
