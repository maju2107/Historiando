@tool
extends RefCounted
## Subdivides only triangles near the stream, preserving the source UVs elsewhere.
## The same resulting mesh is used by rendering and the terrain collision.
const Profile = preload("res://_testes/cenario_ilha/water/watercourse_profile.gd")
const BankShader = preload("res://_testes/cenario_ilha/water/river_bank.gdshader")
const MAX_EDGE_SQUARED := 0.20

var _inverse: Transform3D
var _normal_to_island: Basis
var _normal_from_island: Basis
var _surface: SurfaceTool


func build(source: Mesh, island_transform: Transform3D) -> ArrayMesh:
	_inverse = island_transform.affine_inverse()
	_normal_to_island = island_transform.basis.inverse().transposed()
	_normal_from_island = island_transform.basis.transposed()
	var result := ArrayMesh.new()
	for surface_index in source.get_surface_count():
		var arrays := source.surface_get_arrays(surface_index)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		if indices.is_empty():
			for i in vertices.size():
				indices.append(i)
		_surface = SurfaceTool.new()
		_surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		var source_material := source.surface_get_material(surface_index) as BaseMaterial3D
		var material := ShaderMaterial.new()
		material.shader = BankShader
		if source_material:
			material.set_shader_parameter("ground_color", source_material.albedo_color)
			if source_material.albedo_texture:
				material.set_shader_parameter("ground_texture", source_material.albedo_texture)
				material.set_shader_parameter("has_ground_texture", true)
		_surface.set_material(material)
		for i in range(0, indices.size(), 3):
			var triangle: Array[Dictionary] = []
			for j in 3:
				var index := indices[i + j]
				triangle.append({"p": island_transform * vertices[index], "n": normals[index], "uv": uvs[index] if not uvs.is_empty() else Vector2.ZERO})
			_split(triangle[0], triangle[1], triangle[2], 0)
		_surface.index()
		_surface.commit(result)
	return result


func _split(a: Dictionary, b: Dictionary, c: Dictionary, depth: int) -> void:
	var low: Vector3 = a.p.min(b.p).min(c.p)
	var high: Vector3 = a.p.max(b.p).max(c.p)
	var near_channel := Profile.intersects_carve_bounds(low, high)
	if near_channel and depth < 19:
		var ab: float = a.p.distance_squared_to(b.p)
		var bc: float = b.p.distance_squared_to(c.p)
		var ca: float = c.p.distance_squared_to(a.p)
		if maxf(ab, maxf(bc, ca)) > MAX_EDGE_SQUARED:
			if ab >= bc and ab >= ca:
				var m := _midpoint(a, b)
				_split(a, m, c, depth + 1)
				_split(m, b, c, depth + 1)
			elif bc >= ca:
				var m := _midpoint(b, c)
				_split(a, b, m, depth + 1)
				_split(a, m, c, depth + 1)
			else:
				var m := _midpoint(c, a)
				_split(a, b, m, depth + 1)
				_split(m, b, c, depth + 1)
			return
	var changed_a := Profile.carve(a.p)
	var changed_b := Profile.carve(b.p)
	var changed_c := Profile.carve(c.p)
	for entry: Dictionary in [{"v": a, "p": changed_a}, {"v": b, "p": changed_b}, {"v": c, "p": changed_c}]:
		_surface.set_normal(_carved_normal(entry.v, entry.p))
		_surface.set_uv(entry.v.uv)
		_surface.set_color(Color(clampf((entry.v.p.y - entry.p.y) / 0.22, 0.0, 1.0), 0, 0, 1))
		_surface.add_vertex(_inverse * entry.p)


func _midpoint(a: Dictionary, b: Dictionary) -> Dictionary:
	return {"p": (a.p + b.p) * 0.5, "n": (a.n + b.n).normalized(), "uv": (a.uv + b.uv) * 0.5}


func _carved_normal(vertex: Dictionary, carved: Vector3) -> Vector3:
	if carved.is_equal_approx(vertex.p):
		return vertex.n
	# Preserve authored normals outside the cut; derive the bank slope from the
	# same deformation function rather than smoothing every face of the block.
	var normal: Vector3 = (_normal_to_island * vertex.n).normalized()
	var tangent := normal.cross(Vector3.UP).normalized()
	if tangent.is_zero_approx():
		tangent = Vector3.RIGHT
	var bitangent := normal.cross(tangent)
	var dt := Profile.carve(vertex.p + tangent * 0.01) - Profile.carve(vertex.p - tangent * 0.01)
	var db := Profile.carve(vertex.p + bitangent * 0.01) - Profile.carve(vertex.p - bitangent * 0.01)
	var deformed_normal := dt.cross(db)
	if deformed_normal.length_squared() < 0.000000000001:
		return vertex.n
	return (_normal_from_island * deformed_normal.normalized()).normalized()
