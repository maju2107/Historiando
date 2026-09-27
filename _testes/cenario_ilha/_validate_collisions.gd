extends SceneTree

var failures := 0

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool, message: String) -> void:
	if not condition:
		failures += 1
		push_error(message)

func _run() -> void:
	var vegetation: Node3D = load("res://_testes/cenario_ilha/PleistoceneVegetation.tscn").instantiate()
	root.add_child(vegetation)
	var trees := vegetation.find_children("Arvore*", "Node3D", true, false)
	check(not trees.is_empty(), "No trees found")
	for tree in trees:
		check(not tree.find_children("*", "CollisionShape3D", true, false).is_empty(), "Tree without collision: " + str(tree.name))
	for detail in vegetation.find_children("Detalhe*", "Node3D", true, false):
		check(detail.find_children("*", "CollisionShape3D", true, false).is_empty(), "Small vegetation must remain passable")
	print("TREE_COLLISIONS checked=", trees.size())
	vegetation.free()
	var player = load("res://_testes/parkour/Player.tscn").instantiate()
	root.add_child(player)
	player.set_physics_process(false)
	var wall := StaticBody3D.new()
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(20, 20, 0.5)
	collision.shape = shape
	wall.add_child(collision)
	root.add_child(wall)
	wall.position = Vector3(0, 0, 2)
	for preset in [0, 1]:
		player.control_preset = preset
		player.position = Vector3.ZERO
		player.camera_pivo.rotation = Vector3.ZERO
		for frame in 5:
			await physics_frame
		check(player.camera.global_position.z < 1.75, "Camera entered wall in preset %d" % preset)
		wall.position.z = 20
		for frame in 5:
			await physics_frame
		check(absf(player.camera_pivo.get_hit_length() - 3.5) < 0.01, "Camera did not restore distance")
		Input.action_press("ui_up")
		player._physics_process(1.0 / 60)
		check(Vector2(player.velocity.x, player.velocity.z).length() > 6.9, "Movement did not start")
		Input.action_release("ui_up")
		player._physics_process(1.0 / 60)
		check(Vector2(player.velocity.x, player.velocity.z).is_zero_approx(), "Movement persisted after release in air")
		wall.position.z = 2
	player.free()
	wall.free()
	print("COLLISIONS_AND_RELEASE ", "PASS" if failures == 0 else "FAIL")
	quit(0 if failures == 0 else 1)
