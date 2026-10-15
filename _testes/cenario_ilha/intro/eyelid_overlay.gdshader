shader_type canvas_item;
uniform float openness : hint_range(0.0,1.0) = 0.0;
void fragment() {
	float x = abs(UV.x - 0.5) * 2.0;
	float opening = mix(-0.02,0.72,openness) - (1.0-openness)*0.12*x*x;
	float lid = smoothstep(opening - 0.008, opening + 0.008, abs(UV.y - 0.5));
	COLOR = vec4(0.015, 0.008, 0.02, lid);
}
