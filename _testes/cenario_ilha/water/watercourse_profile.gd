@tool
extends RefCounted
## Shared island-local coordinates for the river, the carved ground and interaction.
## x = upstream z, y = downstream z, z = water level, w = nominal half width.
const REACHES: Array[Vector4] = [
	Vector4(-6.20, -3.40, 11.86, 1.15),
	Vector4(-0.35, 4.15, 7.86, 1.30),
	Vector4(4.85, 27.35, 3.86, 1.25),
]
const DEPTH := 0.32
const BANK_WIDTH := 0.95
const GROUND_ABOVE_WATER := 0.14
const GROUND_TOLERANCE := 0.02
const END_BLEND := 0.95


static func center_x(z: float) -> float:
	return 3.0 + 0.20 * sin(z * 0.48) + 0.12 * sin(z * 0.91)


static func half_width(z: float, reach: int) -> float:
	var width := REACHES[reach].w + 0.10 * sin(z * 1.37)
	if reach == 0:
		width += 0.58 * exp(-pow((z + 5.20) / 0.90, 2.0))
	elif reach == 1:
		width += 0.65 * exp(-pow((z - 0.55) / 1.20, 2.0))
	else:
		width += 0.90 * exp(-pow((z - 6.10) / 1.60, 2.0))
		width += 0.45 * exp(-pow((z - 22.5) / 2.80, 2.0))
	return width


static func reach_at(point: Vector3) -> int:
	for i in REACHES.size():
		var reach := REACHES[i]
		if point.z >= reach.x and point.z <= reach.y:
			if absf(point.x - center_x(point.z)) < half_width(point.z, i):
				return i
	return -1


static func intersects_carve_bounds(low: Vector3, high: Vector3) -> bool:
	if high.x < -0.5 or low.x > 6.5:
		return false
	for i in REACHES.size():
		var reach := REACHES[i]
		if high.z >= reach.x - END_BLEND and low.z <= reach.y + END_BLEND:
			if high.y > reach.z - DEPTH and low.y <= reach.z + GROUND_ABOVE_WATER + GROUND_TOLERANCE:
				return true
	return false


static func carve(point: Vector3) -> Vector3:
	if point.x < -0.5 or point.x > 6.5:
		return point
	for i in REACHES.size():
		var reach := REACHES[i]
		var bed := reach.z - DEPTH
		# Only the thin top layer of this shelf can be excavated. Never pull a
		# higher platform or the wall behind a waterfall down to a lower shelf.
		if point.y <= bed or point.y > reach.z + GROUND_ABOVE_WATER + GROUND_TOLERANCE:
			continue
		if point.z < reach.x - END_BLEND or point.z > reach.y + END_BLEND:
			continue
		var width := half_width(clampf(point.z, reach.x, reach.y), i)
		var distance := absf(point.x - center_x(point.z))
		var bank := 1.0 - smoothstep(width - 0.18, width + BANK_WIDTH, distance)
		var ends := smoothstep(reach.x - END_BLEND, reach.x, point.z)
		ends *= 1.0 - smoothstep(reach.y + 0.55, reach.y + END_BLEND, point.z)
		point.y = lerpf(point.y, bed, bank * ends)
		break
	return point
