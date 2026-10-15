shader_type spatial;
uniform sampler2D eye_texture : source_color, filter_linear_mipmap;
uniform vec4 eye_tint : source_color = vec4(1.0);
uniform float blink : hint_range(0.0,1.0) = 0.0;
uniform vec4 lid_tint : source_color = vec4(0.91,0.61,0.42,1.0);
uniform vec4 lash_tint : source_color = vec4(0.23,0.10,0.08,1.0);
varying vec2 eye_position;
void vertex() {
	// Keep the eyeball and its silhouette intact. Eyelids cover the iris instead
	// of flattening the whole eye (which exposed a slit through the face).
	// UV2 carries bind-pose coordinates, independent of head animation/skinning.
	eye_position = UV2;
}
void fragment() {
	vec3 eye_color = texture(eye_texture, UV).rgb * eye_tint.rgb;
	float x = eye_position.x * 2.0 - 1.0;
	float seam = 0.08 + 0.14*x*x;
	float upper = mix(1.04,seam,blink);
	float cover = max(smoothstep(upper-0.012,upper+0.012,eye_position.y),smoothstep(0.96,1.0,blink));
	cover *= smoothstep(0.0,0.04,blink);
	float lash = (1.0-smoothstep(0.012,0.035,abs(eye_position.y-upper))) * smoothstep(0.08,0.25,blink);
	ALBEDO = mix(mix(eye_color,lid_tint.rgb,cover),lash_tint.rgb,lash);
	ROUGHNESS = mix(0.32,0.85,cover);
}
