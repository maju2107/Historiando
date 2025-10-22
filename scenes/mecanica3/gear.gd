extends Area3D

const  ROTATION_SPEED := 40.0

var start_pos := position.y
var end_pos:= position.y + 0.5

func _ready():
	var gear_tween := create_tween().set_loops().set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
	gear_tween.tween_property(self, "position:y", end_pos, 1.0).from(start_pos)
	gear_tween.tween_property(self, "position:y", start_pos, 1.0).from(end_pos)

func _process(delta):
	rotate_y(deg_to_rad(ROTATION_SPEED * delta))


func _on_body_entered(body: Node3D) -> void:
	if body.name == "player":
		queue_free()
