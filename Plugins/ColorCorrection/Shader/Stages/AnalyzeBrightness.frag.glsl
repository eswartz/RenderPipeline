#version 440

#pragma include "Includes/Configuration.inc.glsl"

out vec4 result;

uniform layout(rgba16f) imageBuffer ExposureStorage;
uniform sampler2D DownscaledTex;

uniform float frameDelta;

void main() {

    // Manually do the last downscale step
    ivec2 texsize = textureSize(DownscaledTex, 0).xy;
    float avg_luminance = 0.0;
    for (int x = 0; x < texsize.x; ++x) {
        for (int y = 0; y < texsize.y; ++y) {
            avg_luminance += texelFetch(DownscaledTex, ivec2(x, y), 0).x;
        }
    }
    avg_luminance /= float(texsize.x * texsize.y);


    // Transition between the last and current value smoothly
    float cur_luminance = imageLoad(ExposureStorage, 0).x;
    float adaption_rate = GET_SETTING(ColorCorrection, brightness_adaption_rate);

    if (cur_luminance > avg_luminance) {
        adaption_rate = GET_SETTING(ColorCorrection, darkness_adaption_rate);
    }

    float adjustment = saturate(frameDelta * adaption_rate);
    float new_luminance = mix(cur_luminance, avg_luminance, adjustment);

    imageStore(ExposureStorage, 0, vec4(new_luminance));
    result = vec4(new_luminance, 0, 0, 1);
}