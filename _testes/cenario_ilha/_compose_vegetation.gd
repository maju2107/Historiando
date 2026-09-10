extends SceneTree

# Executar manualmente com --headless --script para recompor a cena editavel.
const BASE := "res://assets/models/"
var island: Node3D
var vegetation: Node3D
var rng := RandomNumberGenerator.new()
var frames := 0
var occupied: Array[Vector3] = []

func _initialize() -> void:
	rng.seed = 481516
	island = load("res://_testes/cenario_ilha/CenarioIlha.tscn").instantiate()
	root.add_child(island)
	island.get_node("Vegetation").free()
	island.get_node("Player").free()
	vegetation = Node3D.new()
	vegetation.name = "PleistoceneVegetation"
	island.add_child(vegetation)
	for label in ["CampoAberto", "MataDeGaleria", "FlorestaDeAltitude", "EstratoBaixo", "EstratoRibeirinho", "FloresDoCampo", "Fungos", "Afloramentos", "Santuario"]:
		var group := Node3D.new()
		group.name = label
		vegetation.add_child(group)
		group.owner = vegetation

func ground(x: float, z: float) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(Vector3(x, 40, z), Vector3(x, -2, z), 1)
	var hit := island.get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty() or not hit.collider is TerrainChunk or hit.normal.y < 0.9:
		return {}
	return hit

func bounds(node: Node3D) -> AABB:
	var result := AABB()
	var first := true
	for child in node.find_children("*", "MeshInstance3D", true, false):
		var box: AABB = node.global_transform.affine_inverse() * child.global_transform * child.get_aabb()
		result = box if first else result.merge(box)
		first = false
	return result

func place(asset: String, group: String, point: Vector3, height: float, label: String) -> void:
	var pivot := Node3D.new()
	pivot.name = label
	vegetation.get_node(group).add_child(pivot)
	pivot.owner = vegetation
	pivot.position = point
	pivot.rotation.y = rng.randf_range(0, TAU)
	var source: Node3D = load(BASE + asset + ".fbx").instantiate()
	pivot.add_child(source)
	var meshes := source.find_children("*", "MeshInstance3D", true, false)
	var selected: MeshInstance3D = meshes[0]
	if asset.ends_with("HairyTree"):
		selected = source.find_child("Tree_030", true, false)
	var model := MeshInstance3D.new()
	model.name = "Modelo"
	model.mesh = selected.mesh
	var source_basis := selected.global_basis
	pivot.add_child(model)
	model.owner = vegetation
	model.basis = pivot.global_basis.inverse() * source_basis
	source.free()
	var material := StandardMaterial3D.new()
	material.albedo_texture = load(BASE + "creative_trio/" + ("CT_Rocks_Palette.png" if asset.begins_with("Rocks/") else "CT_Pallete.png"))
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	material.roughness = 0.9
	model.material_override = material
	var box: AABB = model.transform * model.get_aabb()
	var factor := height / maxf(box.size.y, 0.01)
	model.scale *= factor
	model.position -= Vector3(box.get_center().x, box.position.y, box.get_center().z) * factor

func _physics_process(_delta: float) -> bool:
	frames += 1
	if frames != 5:
		return false
	var peak := ground(3, -10)
	assert(not peak.is_empty())
	place("Trees/OrangeTrees/SpecialTree", "Santuario", peak.position, 9.5, "ArvoreEspecial")
	occupied.append(peak.position)
	var green := ["BigTree", "MediumTree", "SmallTree", "TallTree", "ExtraSmallTree", "WeirdePineTree"]
	var count := 0
	for attempt in 1800:
		if count >= 65:
			break
		var x := rng.randf_range(-25, 25)
		var z := rng.randf_range(-26, 25)
		var hit := ground(x, z)
		if hit.is_empty():
			continue
		var p: Vector3 = hit.position
		# Keep water, spawn, summit clearing and the authored parkour steps open.
		if absf(x - 3) < 3.7 or Vector2(x + 7, z - 22).length() < 4 or str(hit.collider.name).contains("Degrau") or str(hit.collider.name).contains("Sacada"):
			continue
		var clear := true
		for other in occupied:
			if Vector2(x - other.x, z - other.z).length() < 4.4:
				clear = false
		if not clear:
			continue
		var orange := p.y >= 11.8 or (p.y >= 7.9 and z < -3 and rng.randf() < 0.45)
		var asset: String = "Trees/OrangeTrees/" + ("HairyTree" if rng.randf() < 0.65 else "MushroomTree") if orange else "Trees/GreenTrees/" + green[count % green.size()]
		var group := "FlorestaDeAltitude" if orange else "MataDeGaleria" if absf(x - 3) < 8 else "CampoAberto"
		place(asset, group, p, rng.randf_range(3.3, 5.5) if orange else rng.randf_range(2.8, 4.8), "Arvore_%02d" % count)
		occupied.append(p)
		count += 1
	for index in 360:
		var x := rng.randf_range(-25, 25)
		var z := rng.randf_range(-26, 25)
		var hit := ground(x, z)
		if hit.is_empty() or absf(x - 3) < 2.9 or str(hit.collider.name).contains("Degrau") or Vector2(x + 7, z - 22).length() < 2.8:
			continue
		var p: Vector3 = hit.position
		if Vector2(x - 3, z + 10).length() < 3:
			continue
		var asset: String = "Plants02/Plant_" + ["003", "005", "007", "010", "013"][index % 5]
		var group := "EstratoRibeirinho" if absf(x - 3) < 6 else "EstratoBaixo"
		var height := rng.randf_range(0.35, 0.85)
		if index % 6 == 0:
			asset = "Rocks/" + ["rock_s", "rock_m", "low-lying_rock_s"][index % 3]
			group = "Afloramentos"
			height = rng.randf_range(0.45, 1.1)
		elif p.y > 11 and index % 3 == 0:
			asset = "Mushrooms/Mushroom"
			group = "Fungos"
			height = 0.4
		place(asset, group, p, height, "Detalhe_%03d" % index)
	var light := OmniLight3D.new()
	light.name = "LuzDourada"
	vegetation.get_node("Santuario").add_child(light)
	light.owner = vegetation
	light.position = peak.position + Vector3(0, 3, 0)
	light.light_color = Color(1, 0.65, 0.25)
	light.light_energy = 2.0
	light.omni_range = 9.0
	var particles := CPUParticles3D.new()
	particles.name = "EsporosDourados"
	vegetation.get_node("Santuario").add_child(particles)
	particles.owner = vegetation
	particles.position = peak.position + Vector3(0, 2.5, 0)
	particles.amount = 40
	particles.lifetime = 6
	particles.preprocess = 6
	particles.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	particles.emission_sphere_radius = 3.5
	particles.direction = Vector3.UP
	particles.gravity = Vector3(0, 0.08, 0)
	particles.initial_velocity_min = 0.12
	particles.initial_velocity_max = 0.35
	var mesh := SphereMesh.new()
	mesh.radius = 0.035
	mesh.height = 0.07
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color(1, 0.8, 0.35)
	mesh.material = material
	particles.mesh = mesh
	var packed := PackedScene.new()
	assert(packed.pack(vegetation) == OK)
	assert(ResourceSaver.save(packed, "res://_testes/cenario_ilha/PleistoceneVegetation.tscn") == OK)
	print("BAKED trees=", count + 1, " summit=", peak.position)
	quit()
	return false

