shader_type spatial;
render_mode unshaded, cull_disabled;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform sampler2D depth_texture : hint_depth_texture, repeat_disable, filter_nearest;
uniform vec4 shallow_color : source_color = vec4(0.5372549, 0.8117647, 0.9411765, 1.0);
uniform vec4 deep_color : source_color = vec4(0.3098039, 0.6156863, 0.8509804, 1.0);
uniform vec4 foam_color : source_color = vec4(0.945098, 0.9803922, 1.0, 1.0);
uniform float flow_speed : hint_range(0.0, 3.0) = 0.7;
uniform float refraction_strength : hint_range(0.0, 0.03) = 0.006;
uniform float foam_width : hint_range(0.01, 0.3) = 0.11;
uniform float ripple_clock = 0.0;
// Island-local x, z, birth time, water elevation. Old slots start with time -100.
uniform vec4 ripples[24];
uniform vec4 interactor = vec4(0.0, 0.0, 0.0, 0.0);
uniform vec2 impact_position = vec2(0.0);
uniform float impact_strength = 0.0;
varying vec3 river_position;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
		mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0)), u.x), u.y);
}

vec3 view_position(vec2 uv, mat4 inverse_projection) {
	float depth = textureLod(depth_texture, uv, 0.0).r;
	vec3 ndc = vec3(uv * 2.0 - 1.0, depth);
	#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
		ndc.z = depth * 2.0 - 1.0;
	#endif
	vec4 position = inverse_projection * vec4(ndc, 1.0);
	return position.xyz / position.w;
}

void vertex() {
	river_position = VERTEX;
	// The shoreline stays seated in the bank while the center gently breathes.
	VERTEX.y += sin(VERTEX.z * 3.2 - TIME * 2.0) * sin(UV.x * 3.14159) * 0.012;
}

void fragment() {
	vec2 p = river_position.xz;
	vec2 flow = vec2(0.10, -flow_speed) * TIME;
	float n = noise(p * 2.5 + flow);
	float broad = noise(p * 0.85 + flow * 0.6);
	vec2 distortion = vec2(n - 0.5, noise(p * 2.0 + flow + 18.2) - 0.5);
	float ripple_foam = 0.0;
	for (int i = 0; i < 24; i++) {
		float age = ripple_clock - ripples[i].z;
		if (age >= 0.0 && age < 2.2 && abs(ripples[i].w - river_position.y) < 0.2) {
			vec2 delta = p - ripples[i].xy;
			float distance_to_ring = length(delta);
			float radius = 0.18 + age * 1.05;
			float wobble = sin(atan(delta.y, delta.x) * 7.0 + age * 2.0) * 0.025;
			float band = abs(distance_to_ring - radius + wobble);
			float fade = (1.0 - smoothstep(0.30, 2.2, age)) * smoothstep(0.0, 0.08, age);
			float ring = (1.0 - smoothstep(0.028, 0.075, band)) * fade;
			ripple_foam = max(ripple_foam, ring);
			distortion += delta / max(distance_to_ring, 0.001) * sin((distance_to_ring - radius) * 25.0) * exp(-band * 12.0) * fade * 0.5;
		}
	}
	float thickness = max(0.0, -view_position(SCREEN_UV, INV_PROJECTION_MATRIX).z + VERTEX.z);
	vec2 refracted_uv = clamp(SCREEN_UV + distortion * refraction_strength * smoothstep(0.0, 0.25, thickness), vec2(0.001), vec2(0.999));
	// Reject a distorted sample in front of the water (the player's dry upper body).
	if (-view_position(refracted_uv, INV_PROJECTION_MATRIX).z < -VERTEX.z) {
		refracted_uv = SCREEN_UV;
	}
	vec3 background = textureLod(screen_texture, refracted_uv, 0.0).rgb;
	vec3 water = mix(shallow_color.rgb, deep_color.rgb, smoothstep(0.05, 1.4, thickness));
	water *= 0.91 + broad * 0.18;
	// Tint the refracted bed too: bright orange terrain must not turn blue water pink.
	vec3 color = mix(clamp(background, vec3(0.0), vec3(1.0)) * water, water, 0.72);
	float edge_distance = min(UV.x, 1.0 - UV.x);
	float shore = 1.0 - smoothstep(0.008, 0.038 + n * 0.022, edge_distance);
	float intersection = 1.0 - smoothstep(foam_width * 0.18, foam_width * (0.65 + n), thickness);
	float contact = (1.0 - smoothstep(0.27, 0.40, length(p - interactor.xz))) * interactor.w;
	contact *= 1.0 - smoothstep(0.1, 0.25, abs(interactor.y - river_position.y));
	float impact_distance = length((p - impact_position) * vec2(0.74, 1.0));
	float impact_core = (1.0 - smoothstep(0.35, 1.15, impact_distance + (n - 0.5) * 0.45));
	float impact_rings = (1.0 - smoothstep(0.05, 0.13, abs(sin(impact_distance * 8.5 - TIME * 4.0)))) * (1.0 - smoothstep(0.6, 1.85, impact_distance));
	float impact_foam = max(impact_core, impact_rings * 0.7) * impact_strength;
	float glints = smoothstep(0.77, 0.83, n) * smoothstep(0.45, 0.65, broad) * 0.4;
	float foam = clamp(max(max(shore, intersection), max(ripple_foam, max(contact, impact_foam))) + glints, 0.0, 1.0);
	ALBEDO = mix(color, foam_color.rgb, foam * 0.96);
	ALPHA = 1.0;
}
