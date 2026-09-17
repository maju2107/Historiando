shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;

uniform vec3 platform_size = vec3(4.8, 0.36, 4.8);
uniform vec4 edge_color : source_color = vec4(1.0, 0.34, 0.055, 1.0);
uniform float glow_strength : hint_range(0.0, 8.0) = 3.0;
uniform float solid_amount : hint_range(0.0, 1.0) = 1.0;
uniform float warning_amount : hint_range(0.0, 1.0) = 0.0;
uniform float permanent = 0.0;
varying vec3 local_position;

void vertex() {
	local_position = VERTEX;
}

void fragment() {
	vec3 distance_to_face = max(platform_size * 0.5 - abs(local_position), vec3(0.0));
	// The second nearest face gives all twelve box edges, including the corners.
	float edge_distance = min(max(distance_to_face.x, distance_to_face.y),
		min(max(distance_to_face.x, distance_to_face.z), max(distance_to_face.y, distance_to_face.z)));
	float aa = max(fwidth(edge_distance), 0.002);
	float rim = 1.0 - smoothstep(0.055 - aa, 0.055 + aa, edge_distance);
	float halo = (1.0 - smoothstep(0.055, 0.18, edge_distance)) * 0.30;
	float corners = 1.0 - smoothstep(0.05, 0.19, max(distance_to_face.x, max(distance_to_face.y, distance_to_face.z)));
	float pulse = 1.0 + warning_amount * (0.3 + 0.3 * sin(TIME * 12.0));
	vec3 orange = mix(edge_color.rgb, vec3(1.0, 0.60, 0.13), permanent * 0.25);
	float outline = max(rim, halo);
	ALBEDO = mix(vec3(0.10, 0.16, 0.22), orange, outline);
	EMISSION = orange * (rim + corners * 0.30 + halo) * glow_strength * mix(0.08, 1.0, solid_amount) * pulse;
	float face_alpha = mix(0.018, 0.14, solid_amount);
	float edge_alpha = mix(0.24, 0.96, solid_amount);
	ALPHA = mix(face_alpha, edge_alpha, outline);
}
