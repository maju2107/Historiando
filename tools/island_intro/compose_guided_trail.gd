extends SceneTree
## Author editable placements onto real terrain; never runs during gameplay.
const WAYPOINTS := [
	Vector3(-8.8,4,14.9),Vector3(-10.8,4,13.9),Vector3(-12.3,4,12.8),
	Vector3(-13,5.25,10.8),Vector3(-13,5.25,9.2),Vector3(-13,6.5,6.7),
	Vector3(-13,6.5,4.7),Vector3(-12.6,7.75,2),Vector3(-11.5,8,-.6),
	Vector3(-9.2,8,1),Vector3(-6.2,8,1),Vector3(-3.2,8,1),
	Vector3(0,8,2.2),Vector3(3.3,7.54,2.2),Vector3(6.3,8,1),
	Vector3(8.2,9.27,.4),Vector3(10.3,9.27,-1.4),Vector3(10.5,10.51,-4),
	Vector3(10.1,11.75,-7.5),Vector3(7.7,12.6,-10.8),Vector3(5,13.25,-10.8),
	Vector3(4.5,13.25,-12.8),Vector3(.5,13.25,-12.8),Vector3(.5,13.25,-9),Vector3(.85,13.25,-8)
]

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func _run() -> void:
	var island: Node3D = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	var player: CharacterBody3D = island.get_node("Player")
	player.set_physics_process(false)
	island.get_node("ParkourFlutuante").set_physics_process(false)
	await physics_frame
	await physics_frame
	var space := island.get_world_3d().direct_space_state
	var capsule := CapsuleShape3D.new()
	capsule.radius = .32; capsule.height = 1.3
	var positions: Array[Vector3] = []
	for target: Vector3 in WAYPOINTS:
		var found := false
		for ring in 5:
			for step in (1 if ring == 0 else 12):
				var angle: float = step*TAU/12
				var candidate := target+Vector3(cos(angle),0,sin(angle))*ring*.25
				var ray := PhysicsRayQueryParameters3D.create(candidate+Vector3.UP*.5,candidate-Vector3.UP*.5,1)
				ray.exclude = [player.get_rid()]
				var hit := space.intersect_ray(ray)
				if hit.is_empty() or not hit.collider is TerrainChunk: continue
				if absf(hit.position.y-target.y)>.25: continue
				var query := PhysicsShapeQueryParameters3D.new()
				query.shape = capsule
				query.transform = Transform3D(Basis.IDENTITY,hit.position+Vector3.UP*.75)
				query.collision_mask = 1; query.exclude = [player.get_rid()]
				if not space.intersect_shape(query).is_empty(): continue
				positions.append(hit.position+Vector3.UP*.85)
				print("GUIDE_POINT ",positions.size()," ",positions.back())
				found = true
				break
			if found: break
		if not found:
			push_error("No clear ground for guide crystal at " + str(target))
			quit(1)
			return
	var text := '[gd_scene load_steps=2 format=3]\n\n[ext_resource type="PackedScene" path="res://assets/props/topazio_imperial/TopazioCollectible.tscn" id="1_topazio"]\n\n[node name="Topazios" type="Node3D"]\n'
	for index in positions.size():
		var point := positions[index]
		text += '\n[node name="Trilha%02d" parent="." instance=ExtResource("1_topazio")]\nposition = Vector3(%.6f, %.6f, %.6f)\nfloat_phase = %.2f\n' % [index+1,point.x,point.y,point.z,fposmod(index*.9,TAU)]
	var course: Node3D = island.get_node("ParkourFlutuante")
	for index in [0,3,7,11,14,20]:
		var point: Vector3 = course.get_platforms()[index].surface_position()+Vector3.UP*.85
		text += '\n[node name="TopazioPlataforma%02d" parent="." instance=ExtResource("1_topazio")]\nposition = Vector3(%.6f, %.6f, %.6f)\nfloat_phase = %.2f\n' % [index+1,point.x,point.y,point.z,fposmod(index*.9,TAU)]
	FileAccess.open("res://_testes/cenario_ilha/TopaziosIlha.tscn",FileAccess.WRITE).store_string(text)
	print("GUIDED_TRAIL_SAVED ground=",positions.size()," parkour=6")
	island.queue_free()
	await process_frame
	quit()
