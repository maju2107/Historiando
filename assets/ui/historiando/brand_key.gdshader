shader_type canvas_item;
// Keep the supplied board intact. Remove its flat purple only at render time.
varying vec4 vertex_tint;
void vertex() {
	vertex_tint = COLOR;
}
void fragment() {
	vec4 sample_color = texture(TEXTURE, UV);
	float alpha = smoothstep(0.035, 0.14, distance(sample_color.rgb, vec3(0.10196, 0.0, 0.17255)));
	COLOR = vec4(sample_color.rgb, alpha) * vertex_tint;
}
