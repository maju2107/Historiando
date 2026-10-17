extends SceneTree
## Real island/player/Area3D integration, including the visible fragments HUD.

var _failures := 0
var _island: Node3D
var _player: CharacterBody3D

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	call_deferred("_run")

func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)

func _settle() -> void:
	for frame in 5:
		await physics_frame
	await process_frame

func _load_island() -> void:
	change_scene_to_file("res://_testes/cenario_ilha/CenarioIlha.tscn")
	await scene_changed
	_island = current_scene
	_player = _island.get_node("Player")
	_player.set_physics_process(false)
	var course: Node3D = _island.get_node("ParkourFlutuante")
	course.cycle_enabled = false
	course.set_physics_process(false)
	await _settle()

func _run() -> void:
	await _load_island()
	var pickups := _island.get_node("Topazios").get_children()
	_check(pickups.size() == 31, "Expected thirty-one trail and parkour topaz pickups")
	_check(_player.gears == 0, "The spawn must not collect anything automatically")
	var hud: Control = _player.gear_container.comic_hud
	_check(hud != null and hud.collectibles == 0, "Fragments HUD should start at zero")
	_check(hud.fragment_mission.visible and hud.fragment_goal == pickups.size(), "The side mission must show the island fragment goal")
	_check(not hud.get("notification").visible, "No discovery popup should appear before collecting a fragment")
	var space := _island.get_world_3d().direct_space_state
	var capsule := CapsuleShape3D.new()
	capsule.radius = .32
	capsule.height = 1.30
	var shared_mesh: Mesh
	for pickup: Area3D in pickups:
		pickup.set_process(false)
		_check(pickup.collision_layer == 0, "Collectible must not block player movement")
		var meshes := pickup.find_children("*", "MeshInstance3D", true, false)
		_check(meshes.size() == 1, "Collectible should have one visible mesh")
		if shared_mesh == null:
			shared_mesh = meshes[0].mesh
		_check(meshes[0].mesh == shared_mesh, "Instances should share their mesh and textures")
		var ray := PhysicsRayQueryParameters3D.create(pickup.global_position + Vector3.UP * .1, pickup.global_position - Vector3.UP * 1.6, 1)
		ray.exclude = [_player.get_rid()]
		var hit := space.intersect_ray(ray)
		_check(not hit.is_empty(), "Pickup has no reachable support below: " + pickup.name)
		if not hit.is_empty():
			var clearance: float = pickup.global_position.y - hit.position.y
			_check(clearance > .55 and clearance < 1.10, "Unexpected height over surface: " + pickup.name)
		var query := PhysicsShapeQueryParameters3D.new()
		query.shape = capsule
		query.transform = Transform3D(Basis.IDENTITY, pickup.global_position - Vector3.UP * .10)
		query.collision_mask = 1
		query.exclude = [_player.get_rid()]
		_check(space.intersect_shape(query).is_empty(), "Vegetation or another body blocks access to pickup: " + pickup.name)
	print("TOPAZIO_PLACEMENT_AND_SHARED_RESOURCES_OK")

	var first: Area3D = pickups[0]
	var visual: Node3D = first.get_node("Visual")
	var before: Transform3D = visual.transform
	first._process(.35)
	_check(not visual.basis.is_equal_approx(before.basis), "Crystal must rotate")
	_check(not is_equal_approx(visual.position.y, before.origin.y), "Crystal must bob vertically")
	_check(absf(visual.position.y) <= first.float_amplitude + .001, "Float must stay within its amplitude")
	var nonplayer := Node3D.new()
	first._on_body_entered(nonplayer)
	nonplayer.free()
	_check(_player.gears == 0 and not first.is_queued_for_deletion(), "Only the player may collect topaz")
	first.set_process(true)
	paused = true
	before = visual.transform
	for frame in 5:
		await process_frame
	_check(visual.transform.is_equal_approx(before), "Animation should pause with gameplay")
	paused = false
	first.set_process(false)
	print("TOPAZIO_ANIMATION_PAUSE_AND_FILTER_OK")

	# Physics overlap drives body_entered; no direct calls to collect_gear here.
	_player.global_position = Vector3(100, 30, 100)
	await _settle()
	var expected := 0
	for pickup: Area3D in pickups:
		var collectible_name := pickup.name
		_player.global_position = pickup.global_position - Vector3.UP * .65
		_player.velocity = Vector3.ZERO
		await _settle()
		expected += 1
		_check(_player.gears == expected, "Physics pickup did not award exactly one fragment: " + collectible_name)
		_check(hud.collectibles == expected, "HUD did not track collected fragments")
		_check(hud.fragment_count.text.begins_with("Fragmentos  %02d / %02d" % [expected,pickups.size()]), "Visible side mission count did not update")
		if expected == 1:
			_check(hud.get("notification").visible and "NOVA DESCOBERTA" in hud.get("notification").text, "First fragment must show the discovery popup")
			hud.notice_timer.stop()
			hud.get("notification").hide()
			_player.gear_container.update_gear(1)
			_check(not hud.get("notification").visible, "Refreshing the first fragment count must not repeat discovery")
		elif expected < pickups.size():
			_check(not hud.get("notification").visible, "Later fragments must update the mission without another discovery popup")
		else:
			_check(hud.get("notification").visible and hud.get("notification").text == "TODOS OS FRAGMENTOS REUNIDOS!", "The final fragment must still show mission completion")
		_check(not is_instance_valid(pickup), "Collected topaz should disappear")
		await _settle()
		_check(_player.gears == expected, "Remaining inside the pickup awarded another fragment")
		_player.global_position = Vector3(100, 30, 100)
		await _settle()
	_check(_island.get_node("Topazios").get_child_count() == 0, "Collected instances remained in the scene")
	print("TOPAZIO_REAL_PLAYER_OVERLAP_HUD_AND_SINGLE_COLLECTION_OK count=", expected)

	await _load_island()
	_check(_player.gears == 0, "Scene restart must reset the counter")
	_check(_island.get_node("Topazios").get_child_count() == 31, "Scene restart must restore pickups")
	print("TOPAZIO_SCENE_RESTART_OK")
	print("TOPAZIO_COLLECTIBLES ", "PASS" if _failures == 0 else "FAIL", " failures=", _failures)
	_island.queue_free()
	await process_frame
	quit(0 if _failures == 0 else 1)
