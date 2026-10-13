shader_type spatial;
render_mode unshaded, cull_disabled, depth_prepass_alpha;

uniform vec3 platform_size = vec3(4.8, 0.36, 4.8);
uniform vec4 edge_color : source_color = vec4(0.87, 0.65, 0.23, 1.0);
uniform float glow_strength : hint_range(0.0, 8.0) = 1.5;
uniform float solid_amount : hint_range(0.0, 1.0) = 1.0;
uniform float warning_amount : hint_range(0.0, 1.0) = 0.0;
uniform float time_remaining : hint_range(0.0, 1.0) = 1.0;
uniform float permanent = 0.0;
uniform float checkpoint = 0.0;
varying vec3 local_position;
varying vec3 local_normal;

void vertex() {
    local_position = VERTEX;
    local_normal = NORMAL;
}

void fragment() {
    vec2 inset = platform_size.xz * 0.5 - abs(local_position.xz);
    float border_distance = min(inset.x, inset.y);
    float aa = max(fwidth(border_distance), 0.008);
    float top = step(0.5, local_normal.y);
    float top_rim = 1.0 - smoothstep(0.075 - aa, 0.075 + aa, border_distance);
    float side = 1.0 - abs(local_normal.y);
    float side_distance = min(platform_size.y * 0.5 - abs(local_position.y), max(inset.x, inset.y));
    float side_rim = 1.0 - smoothstep(0.025, 0.045, side_distance);
    float rim = top_rim * top + side_rim * side;
    float inner_line = 1.0 - smoothstep(0.012, 0.025 + aa, abs(border_distance - 0.24));
    float corners = (1.0 - smoothstep(0.35, 0.55, inset.x)) * (1.0 - smoothstep(0.35, 0.55, inset.y));
    // Etched diagonal lines give the landing deck a surface and scale.
    float etch = 1.0 - smoothstep(0.012, 0.025, abs(fract((local_position.x + local_position.z) * 1.2) - 0.5));
    float side_band = 1.0 - smoothstep(0.025, 0.055, abs(local_position.y + platform_size.y * 0.10));
    float dash = step(0.35, fract((local_position.x + local_position.z) * 2.0));
    float pulse = 0.55 + 0.45 * sin(TIME * 14.0);
    vec3 accent = mix(edge_color.rgb, vec3(1.0, 0.26, 0.09), warning_amount);
    vec3 deck = mix(vec3(0.12, 0.085, 0.16), vec3(0.07, 0.20, 0.17), checkpoint);
    float ripple = pow(max(0.0, 1.0 - abs(fract(length(local_position.xz) * 0.65 - TIME * 0.13) - 0.5) * 2.0), 18.0) * top;
    deck += etch * 0.025 * top + ripple * edge_color.rgb * 0.035;
    float line = max(rim, max(inner_line * top * 0.4, corners * top));
    line = max(line, side_band * side * 0.20);
    // The front edge drains towards the next jump; safe decks keep a full bar.
    float front = step(local_position.z, -platform_size.z * 0.5 + 0.10) * top;
    float filled = step(local_position.x / platform_size.x + 0.5, max(time_remaining, permanent));
    line *= mix(1.0, mix(0.12, 1.0, filled), front);
    ALBEDO = mix(deck, accent, line * 0.55);
    ROUGHNESS = 0.68;
    METALLIC = 0.25;
    EMISSION = accent * (line + ripple * 0.045) * glow_strength * mix(0.10, 1.0, solid_amount) * (1.0 + warning_amount * pulse);
    // The active deck remains magical glass. A ghost only retains dashed edges.
    float active_alpha = mix(mix(0.18, 0.72, top), 0.94, max(rim, corners * top));
    ALPHA = mix(max(rim * mix(0.07, 0.32, dash), inner_line * top * 0.06), active_alpha, solid_amount);
}
