extends SceneTree
## Actual controller and physics coverage for safe landings, fall damage and void recovery.
var _failures := 0
var _island: Node3D
var _player: CharacterBody3D
var _course: Node3D

func _initialize() -> void:
	set_meta("skip_island_intro",true)
	set_meta("skip_parkour_quiz",true) # Dedicated controller/fall isolation.
	call_deferred("_run")

func _check(condition: bool,message: String) -> void:
	if not condition:
		_failures += 1
		push_error(message)

func _settle(frames: int = 15) -> void:
	for frame in frames: await physics_frame
	await process_frame

func _place(point: Vector3,velocity: Vector3 = Vector3.ZERO) -> void:
	_player.global_position = point
	_player.velocity = velocity
	_player._tracking_fall = false
	_player._fall_peak = point.y

func _reset_lives() -> void:
	await create_timer(1.1).timeout
	_player.health = 3
	_player._update_life_hud()

func _check_return(expected: Vector3,message: String) -> void:
	_check(_player.global_position.distance_to(expected)<.15,message)
	_check(not _player.is_dead,"A nonfatal fall killed the player")
	_check(_player.health==2,"A damaging fall must cost exactly one life")
	_check(not _player._tracking_fall,"Recovery retained the old fall height")

func _walk_off(index: int,direction: Vector3) -> void:
	var platform: Node3D = _course.get_platforms()[index]
	_place(platform.surface_position()+Vector3.UP*.08)
	await _settle()
	_check(_course._supporting_platform_index()==index,"Player did not stand on the real platform")
	_player.camera_pivo.rotation = Vector3(deg_to_rad(-18),0,0)
	for pair in [["ui_left",direction.x<0],["ui_right",direction.x>0],["ui_up",direction.z<0],["ui_down",direction.z>0]]:
		if pair[1]: Input.action_press(pair[0])
	for frame in 240:
		await physics_frame
		await process_frame
		if _player.health<3: break
		if _player.is_on_floor() and _terrain_support(): break
	for action in ["ui_left","ui_right","ui_up","ui_down"]: Input.action_release(action)
	print("WALK_OFF ",index," position=",_player.position," health=",_player.health," floor=",_player.is_on_floor())

func _terrain_support() -> bool:
	for i in _player.get_slide_collision_count():
		var collision := _player.get_slide_collision(i)
		if collision.get_collider() is TerrainChunk and collision.get_normal().y>.7:
			return true
	return false

func _run() -> void:
	change_scene_to_file("res://_testes/cenario_ilha/CenarioIlha.tscn")
	await scene_changed
	_island = current_scene
	_player = _island.get_node("Player")
	_course = _island.get_node("ParkourFlutuante")
	_course.cycle_enabled = false
	_player.control_preset = 0
	await _settle()
	_check(_island.get_node_or_null("DeathZone")==null,"Island should not depend on death-zone volumes")
	for target: Vector3 in [Vector3(15,8.1,9),Vector3(-13,6.6,4.5),Vector3(9,4.1,24)]:
		_place(target,Vector3.DOWN*2)
		await _settle()
		_check(_player.health==3 and _player.is_on_floor(),"Descending ordinary island levels caused damage")
		_check(Vector2(_player.position.x,_player.position.z).distance_to(Vector2(target.x,target.z))<.15,"Exploration teleported player")
	print("ISLAND_TERRAIN_DESCENT_WITHOUT_RESPAWN_OK")
	for index in [0,1]:
		await _walk_off(index,Vector3(-1,0,-1) if index==0 else Vector3(0,0,1))
		_check(_player.health==3 and _player.can_move and _player.is_on_floor(),"Early platform fall should be safe")
		_check(_course._supporting_platform_index()<0,"Early fall did not land on island terrain")
	print("FIRST_TWO_PLATFORMS_SAFE_FALL_OK")
	await _walk_off(7,Vector3(0,0,-1))
	var checkpoint: Vector3 = _player.player_start_position
	_check(_course._checkpoint_index==7,"Latest checkpoint was not activated")
	_check_return(checkpoint,"High platform fall did not return to latest checkpoint")
	print("HIGH_PLATFORM_LANDING_RECOVERY_OK")
	await create_timer(.55).timeout
	_place(checkpoint+Vector3.UP*12,Vector3.DOWN*80)
	await _settle(18)
	_check_return(checkpoint,"Invulnerability prevented recovery or charged a second life")
	print("IMMUNE_FALL_RECOVERY_OK")
	await _reset_lives()
	for target: Vector3 in [Vector3(15,8.1,9),Vector3(-13,6.6,4.5),Vector3(9,4.1,24)]:
		_place(target,Vector3.DOWN*2)
		await _settle()
		_check(_player.health==3 and _player.is_on_floor(),"Checkpoint history interfered with exploration")
	print("EXPLORATION_AFTER_CHECKPOINT_OK")
	# Test the threshold on a separate real floor and include upward motion to an apex.
	var floor_body := StaticBody3D.new()
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(20,1,20)
	collision.shape = shape
	floor_body.add_child(collision)
	_island.add_child(floor_body)
	floor_body.position = Vector3(100,-.5,100)
	await _settle(3)
	for sample in [[7.8,false],[8.2,true]]:
		await _reset_lives()
		_place(Vector3(100,sample[0],100))
		await _settle(100)
		_check(_player.health==(2 if sample[1] else 3),"Fall damage height boundary is incorrect")
		if sample[1]: _check_return(checkpoint,"Damaging landing did not use saved checkpoint")
	await _reset_lives()
	_place(Vector3(100,7,100),Vector3.UP*6)
	await _settle(160)
	_check_return(checkpoint,"Fall height did not include airborne apex")
	print("FALL_HEIGHT_BOUNDARY_AND_APEX_OK")
	await _reset_lives()
	_place(Vector3(1000,-9,1000),Vector3.DOWN*100)
	await _settle()
	_check_return(checkpoint,"Void height fallback failed outside the island")
	print("OUT_OF_WORLD_RECOVERY_OK")
	await _reset_lives()
	_place(_course.get_platforms().back().surface_position()+Vector3.UP*.08)
	await _settle()
	_check(_course._completed,"Final landing did not complete route")
	checkpoint = _player.player_start_position
	_place(Vector3(100,12,100),Vector3.DOWN*40)
	await _settle(50)
	_check_return(checkpoint,"Fall after completion did not recover")
	_check(_course._get_hud().objective.text.contains("concluída"),"Recovery lost completed objective")
	print("FINISH_RECOVERY_OK")
	var manager := root.get_node("BotaoGlobal")
	for attempt in 2:
		await _reset_lives()
		_player.health = 1
		_place(Vector3(1000,-9,1000),Vector3.DOWN)
		await _settle(3)
		_check(_player.is_dead and _player.health==0,"Last fall did not exhaust lives")
		_check(paused and manager.game_over,"Last life did not open game over")
		if not is_instance_valid(manager.pause_screen):
			_check(false,"Missing retry screen")
			quit(1)
			return
		manager.pause_screen.restart_requested.emit()
		await scene_changed
		_island = current_scene
		_player = _island.get_node("Player")
		_course = _island.get_node("ParkourFlutuante")
		await _settle()
		_check(not paused and not manager.game_over,"Retry left scene paused")
		_check(_player.health==3 and _player.can_move and not _player.is_dead,"Retry did not restore player")
	print("GAME_OVER_AND_REPEATED_RETRY_OK")
	await _reset_lives()
	manager.name = "RespawnValidationManager"
	_player.health = 1
	_place(Vector3(1000,-9,1000),Vector3.DOWN)
	await _settle()
	_check(not paused and not _player.is_dead and _player.can_move,"Missing UI froze player")
	_check(_player.health==3 and _player.is_physics_processing(),"Missing UI did not restore player")
	await create_timer(1.1).timeout
	_check(not _player.is_invulnerable,"Missing UI left permanent immunity")
	manager.name = "BotaoGlobal"
	print("MISSING_RETRY_UI_RECOVERY_OK")
	print("RESPAWN ","PASS" if _failures==0 else "FAIL"," failures=",_failures)
	quit(0 if _failures==0 else 1)
