shader_type spatial;
uniform sampler2D eye_texture : source_color, filter_linear_mipmap;
uniform vec4 eye_tint : source_color = vec4(1.0);
uniform float blink : hint_range(0.0,1.0) = 0.0;
uniform vec3 eye_up = vec3(0.0,1.0,0.0);
uniform float eye_height = 0.08;
void vertex() {
	float x = UV2.x*2.0-1.0;
	float seam = 0.08+0.14*x*x;
	float upper = mix(1.04,seam,blink);
	// Upper lashes follow the top lid. The eyebrows and lower lashes stay put.
	float upper_lash = smoothstep(0.45,0.65,UV2.y)*(1.0-smoothstep(1.06,1.18,UV2.y));
	VERTEX -= eye_up * eye_height * max(UV2.y-upper,0.0) * upper_lash;
}
void fragment() {
	ALBEDO = texture(eye_texture,UV).rgb*eye_tint.rgb;
	ROUGHNESS = 0.85;
}
