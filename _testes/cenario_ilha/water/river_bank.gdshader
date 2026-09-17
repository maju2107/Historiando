shader_type spatial;
render_mode diffuse_burley;

uniform sampler2D ground_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 ground_color : source_color = vec4(1.0);
uniform bool has_ground_texture = false;
// #E99268, sampled from the soil in the terrain blocks' original colormap.
uniform vec4 bed_color : source_color = vec4(0.9137255, 0.572549, 0.4078431, 1.0);

void fragment() {
	vec3 ground = ground_color.rgb;
	if (has_ground_texture) {
		ground *= texture(ground_texture, UV).rgb;
	}
	// The sculpt amount is stored per vertex; a soft transition hides triangle borders.
	ALBEDO = mix(ground, bed_color.rgb, smoothstep(0.02, 0.75, COLOR.r));
	ROUGHNESS = 0.94;
}
