extends SceneTree


func _initialize() -> void:
	var folders := ["Trees01", "Trees02", "Plants01", "Plants02", "Rocks", "Flowers", "Mushrooms"]
	for folder: String in folders:
		var directory := DirAccess.open("res://assets/models/creative_trio/%s" % folder)
		if directory == null:
			continue
		var files := directory.get_files()
		files.sort()
		for file: String in files:
			if file.get_extension().to_lower() != "fbx":
				continue
			var path := "res://assets/models/creative_trio/%s/%s" % [folder, file]
			var packed := load(path) as PackedScene
			if packed == null:
				print("FAILED\t", path)
				continue
			var root := packed.instantiate()
			var bounds := _combined_bounds(root)
			print("%s\tsize=(%.3f,%.3f,%.3f)\tpos=(%.3f,%.3f,%.3f)\tcenter=(%.3f,%.3f,%.3f)" % [path, bounds.size.x, bounds.size.y, bounds.size.z, bounds.position.x, bounds.position.y, bounds.position.z, bounds.get_center().x, bounds.get_center().y, bounds.get_center().z])
			root.free()
	quit()


func _combined_bounds(root: Node) -> AABB:
	var result := AABB()
	var has_bounds := false
	var entries: Array[Dictionary] = [{"node": root, "transform": Transform3D.IDENTITY}]
	while not entries.is_empty():
		var entry: Dictionary = entries.pop_back()
		var node := entry.node as Node
		var transform := entry.transform as Transform3D
		if node is Node3D:
			transform *= (node as Node3D).transform
		if node is MeshInstance3D and (node as MeshInstance3D).mesh:
			var mesh_bounds := transform * (node as MeshInstance3D).get_aabb()
			result = result.merge(mesh_bounds) if has_bounds else mesh_bounds
			has_bounds = true
		for child: Node in node.get_children():
			entries.append({"node": child, "transform": transform})
	return result
