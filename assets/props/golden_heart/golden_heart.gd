@tool
extends Area3D
## Original, reusable puffed heart mesh; gold/ink matches Historiando's palette.
signal collected(player: CharacterBody3D)
@export var float_phase := 0.0
static var shared_mesh: ArrayMesh
var taken := false
var visual: Node3D
var _clock := 0.0

func _ready() -> void:
	collision_layer = 0
	collision_mask = 1
	monitorable = false
	add_to_group("golden_hearts")
	visual = Node3D.new()
	visual.name = "GoldenHeartVisual"
	add_child(visual)
	if shared_mesh == null: shared_mesh = _make_mesh()
	var mesh := MeshInstance3D.new()
	mesh.mesh = shared_mesh
	var gold := StandardMaterial3D.new()
	gold.albedo_color = Color("efad31")
	gold.metallic = .48
	gold.roughness = .27
	gold.emission_enabled = true
	gold.emission = Color("dda63b")
	gold.emission_energy_multiplier = .18
	mesh.material_override = gold
	visual.add_child(mesh)
	var outline := MeshInstance3D.new()
	outline.mesh = shared_mesh
	outline.scale = Vector3.ONE*1.045
	var ink := StandardMaterial3D.new()
	ink.albedo_color = Color("422518")
	ink.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ink.cull_mode = BaseMaterial3D.CULL_FRONT
	outline.material_override = ink
	visual.add_child(outline)
	var shape := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = .65
	shape.shape = sphere
	add_child(shape)
	body_entered.connect(_try_collect)
	set_physics_process(not Engine.is_editor_hint())

static func _point(radius: float,angle: float,side: float) -> Vector3:
	var x := .53*pow(sin(angle),3)
	var y := .031*(13*cos(angle)-5*cos(2*angle)-2*cos(3*angle)-cos(4*angle))
	return Vector3(x*radius,y*radius,side*.22*sqrt(maxf(0,1-radius*radius)))

static func _make_mesh() -> ArrayMesh:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings := [0.0,.2,.4,.6,.78,.92,1.0]
	for side in [-1.0,1.0]:
		for ring in rings.size()-1:
			for section in 64:
				var a := TAU*section/64
				var b := TAU*(section+1)/64
				var p := [_point(rings[ring],a,side),_point(rings[ring+1],a,side),_point(rings[ring+1],b,side),_point(rings[ring],b,side)]
				var indices := [0,1,2] if ring == 0 else [0,1,2,0,2,3]
				if side < 0: indices = [0,2,1] if ring == 0 else [0,2,1,0,3,2]
				for index in indices:
					var vertex: Vector3 = p[index]
					surface.set_normal(Vector3(vertex.x/.53,vertex.y/.53,vertex.z*8).normalized())
					surface.add_vertex(vertex)
	surface.index()
	return surface.commit()

func _process(delta: float) -> void:
	if Engine.is_editor_hint() or taken: return
	_clock += delta
	visual.position.y = sin(_clock*2.0+float_phase)*.11
	visual.rotation.y = _clock*.9+float_phase

func _physics_process(_delta: float) -> void:
	if taken: return
	# Collect on overlap even when health is already full.
	for body in get_overlapping_bodies(): _try_collect(body)

func _try_collect(body: Node3D) -> void:
	if taken or not body.is_in_group("player") or not body.has_method("restore_life"): return
	if body.get("is_dead") == true: return
	var restored: bool = body.restore_life(1)
	taken = true
	set_deferred("monitoring",false)
	collected.emit(body)
	if body.gear_container and body.gear_container.comic_hud:
		body.gear_container.comic_hud.notify("+1 VIDA · CORAÇÃO DOURADO!" if restored else "CORAÇÃO DOURADO · VIDAS CHEIAS")
	var tween := create_tween().set_parallel(true)
	tween.tween_property(visual,"position:y",.65,.3)
	tween.tween_property(visual,"scale",Vector3.ONE*.05,.3)
	tween.chain().tween_callback(queue_free)
