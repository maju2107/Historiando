shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;
uniform float phase = 0.0;
uniform sampler2D emblem : source_color, filter_linear_mipmap;
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float a = atan(p.y,p.x);
	float curl = smoothstep(-0.2,0.2,sin(a*3.0+r*13.0-phase));
	vec3 ink = vec3(0.102,0.0,0.173);
	vec3 gold = vec3(0.87,0.65,0.23);
	vec3 paper = vec3(1.0,0.92,0.74);
	vec3 color = mix(gold,paper,curl*0.65);
	color = mix(ink,color,smoothstep(0.0,0.24,r));
	vec4 logo = texture(emblem,UV);
	color = mix(color,logo.rgb,logo.a*0.88);
	ALBEDO = color;
	EMISSION = color*0.28;
	ALPHA = 1.0-smoothstep(0.91,0.99,r);
}
