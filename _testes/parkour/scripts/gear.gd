extends Area3D

const  ROTATION_SPEED := 40.0

func _process(delta: float) -> void:
	rotate_y(deg_to_rad(ROTATION_SPEED * delta))

func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("player") and body.has_method("collect_gear"):
		body.collect_gear()
		queue_free()
