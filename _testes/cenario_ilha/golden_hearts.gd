extends Node3D
const Heart = preload("res://assets/props/golden_heart/GoldenHeart.tscn")
## Three exploration refills plus two in the parkour. Search only clear, flat ground.
@export var island_stops: Array[Vector2] = [Vector2(-6,18),Vector2(-12,7),Vector2(10,8)]
var placed := 0
var placement_report: Array[Dictionary] = []
var _obstacle_bounds: Array[AABB] = []
const CLEARANCE := .75 # Contains the spinning heart, its full bob and a visible air gap.

func _ready() -> void:
	await get_tree().physics_frame
	await get_tree().physics_frame
	_cache_obstacles()
	for stop in island_stops:
		var found := false
		for offset in _search_offsets():
			var hit := _terrain_floor(stop+offset)
			if hit.is_empty(): continue
			var at: Vector3 = hit.position+Vector3.UP
			if _has_standing_room(hit.position) and placement_is_clear(at):
				_spawn(at,"island")
				found = true
				break
		if not found: push_warning("No unobstructed heart location near %s; unsafe placement skipped." % stop)
	# Two spaced refills, rather than a heart at every checkpoint.
	var course: Node3D = get_parent().get_node("ParkourFlutuante")
	for index in [7,15]:
		var platform: Node3D = course.get_platforms()[index]
		for corner in [Vector2(-1.9,-1.8),Vector2(1.9,-1.8),Vector2(-1.9,1.8),Vector2(1.9,1.8)]:
			var at: Vector3 = platform.surface_position()+platform.global_basis.x*corner.x+platform.global_basis.z*corner.y+Vector3.UP
			if placement_is_clear(at):
				_spawn(at,"checkpoint")
				break

func _cache_obstacles() -> void:
	_obstacle_bounds.clear()
	# Mesh bounds also reject noncolliding plants and the empty interiors of
	# concave tree/rock colliders; a floor ray alone cannot see those cases.
	var pending: Array[Node] = [get_parent().get_node("Terrain"),get_parent().get_node("Vegetation")]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		if node is MeshInstance3D and node.mesh and node.is_visible_in_tree():
			_obstacle_bounds.append(node.global_transform*node.get_aabb())
		for child in node.get_children(true): pending.append(child)

func _terrain_floor(at: Vector2) -> Dictionary:
	var exclusions: Array[RID] = []
	for attempt in 24:
		var hit := get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(at.x,14,at.y),Vector3(at.x,-12,at.y),1,exclusions))
		if hit.is_empty(): return {}
		if hit.collider is TerrainChunk:
			return hit if hit.normal.y > .8 else {}
		exclusions.append(hit.rid)
	return {}

func _has_standing_room(floor: Vector3) -> bool:
	for offset in [Vector2(.85,0),Vector2(-.85,0),Vector2(0,.85),Vector2(0,-.85)]:
		var hit := _terrain_floor(Vector2(floor.x,floor.z)+offset)
		if hit.is_empty() or absf(hit.position.y-floor.y) > .18: return false
	return true

func placement_is_clear(at: Vector3) -> bool:
	var swept := AABB(at-Vector3.ONE*CLEARANCE,Vector3.ONE*CLEARANCE*2)
	for obstacle in _obstacle_bounds:
		if obstacle.grow(.1).intersects(swept): return false
	var query := PhysicsShapeQueryParameters3D.new()
	var shape := SphereShape3D.new()
	shape.radius = CLEARANCE
	query.shape = shape
	query.transform.origin = at
	query.collision_mask = 1
	query.exclude = [get_parent().get_node("Player").get_rid()]
	return get_world_3d().direct_space_state.intersect_shape(query,1).is_empty()

func _search_offsets() -> Array[Vector2]:
	var offsets: Array[Vector2] = [Vector2.ZERO]
	for radius in [1.5,3.0,4.5,6.0]:
		for sector in 12: offsets.append(Vector2.from_angle(TAU*sector/12)*radius)
	return offsets

func _spawn(at: Vector3,kind: String) -> void:
	var heart := Heart.instantiate()
	heart.name = "GoldenHeart%02d" % (placed+1)
	heart.float_phase = placed*.83
	add_child(heart)
	heart.global_position = at
	placement_report.append({"name":heart.name,"kind":kind,"position":[at.x,at.y,at.z],"clearance":CLEARANCE})
	placed += 1
