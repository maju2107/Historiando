extends Area3D

func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		if body.has_method("respawn_player"):
			body.respawn_player.call_deferred()
	elif body.is_in_group("enemy"):
		if body.has_method("reset_to_spawn"):
			body.reset_to_spawn.call_deferred()
		elif body.has_method("respawn_player"):
			body.respawn_player.call_deferred()
