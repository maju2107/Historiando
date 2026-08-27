extends SceneTree


func _initialize() -> void:
	var vegetation := load("res://_testes/cenario_ilha/PleistoceneVegetation.tscn") as PackedScene
	assert(vegetation != null, "Nao foi possivel carregar a vegetacao.")
	var vegetation_root := vegetation.instantiate()
	var meshes := _count_type(vegetation_root, "MeshInstance3D")
	var instances := vegetation_root.get_child_count(true)
	print("VEGETATION_OK nodes=%d meshes=%d" % [instances, meshes])
	vegetation_root.free()

	var island := load("res://_testes/cenario_ilha/CenarioIlha.tscn") as PackedScene
	assert(island != null, "Nao foi possivel carregar CenarioIlha.")
	var island_root := island.instantiate()
	assert(island_root.get_node_or_null("Vegetation") != null, "A instancia de vegetacao nao esta na ilha.")
	print("ISLAND_OK nodes=%d" % island_root.get_child_count(true))
	island_root.free()
	quit()


func _count_type(root_node: Node, type_name: String) -> int:
	var total := 0
	var pending: Array[Node] = [root_node]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		if node.get_class() == type_name:
			total += 1
		for child: Node in node.get_children():
			pending.append(child)
	return total
