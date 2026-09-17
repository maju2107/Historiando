shader_type spatial;
render_mode unshaded, cull_disabled, depth_prepass_alpha;

uniform vec4 water_color : source_color = vec4(0.4727843, 0.7143529, 0.8282353, 1.0);
uniform vec4 light_color : source_color = vec4(0.7003922, 0.8792157, 0.9647059, 1.0);
uniform vec4 foam_color : source_color = vec4(0.945098, 0.9803922, 1.0, 1.0);
uniform float flow_speed = 1.35;
uniform float fade_bottom = 0.0;
uniform float phase = 0.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0)), f.x), f.y);
}
void vertex() {
	float sway = sin(UV.y * 10.0 - TIME * 5.0 + UV.x * 8.0 + phase);
	VERTEX.z += sway * 0.045 * sin(UV.y * 3.14159);
	VERTEX.x += sin(UV.y * 13.0 - TIME * 3.0 + phase) * 0.025 * sin(UV.y * 3.14159);
}
void fragment() {
	float time = TIME * flow_speed + phase;
	float stripes = noise(vec2(UV.x * 15.0, UV.y * 2.5 - time));
	float sheets = noise(vec2(UV.x * 6.0 + sin(UV.y * 7.0 - time) * 0.2, UV.y * 4.0 - time * 1.6));
	float streak = smoothstep(0.59, 0.70, stripes + sheets * 0.16);
	float side = 1.0 - smoothstep(0.012, 0.065, min(UV.x, 1.0 - UV.x));
	float crest = 1.0 - smoothstep(0.01, 0.13, UV.y);
	float foot = smoothstep(0.68, 1.0, UV.y + (sheets - 0.5) * 0.18) * (1.0 - fade_bottom);
	vec3 color = mix(water_color.rgb, light_color.rgb, smoothstep(0.25, 0.67, sheets));
	ALBEDO = mix(color, foam_color.rgb, max(streak * 0.86, max(side * 0.82, max(crest * 0.75, foot))));
	float edge = smoothstep(0.0, 0.014, min(UV.x, 1.0 - UV.x));
	ALPHA = edge * mix(0.94, 1.0, streak) * (1.0 - smoothstep(0.76, 1.0, UV.y) * fade_bottom);
}
