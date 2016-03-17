/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#version 430

#define USE_MAIN_SCENE_DATA
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/noise.inc.glsl"
#pragma include "includes/transforms.inc.glsl"

uniform sampler2D DownscaledDepth;

out vec3 result;

#define USE_LINEAR_DEPTH 0

const int num_steps = 64;
const float hit_tolerance_ws = 0.00003;

bool point_between_planes(float z, float z_a, float z_b) {
    return z + hit_tolerance_ws >= min(z_a, z_b) - 0.0001 && z - hit_tolerance_ws <= max(z_a, z_b);
    // return z - hit_tolerance_ws <= max(z_a, z_b);
}


void main()
{
    vec2 texcoord = get_half_texcoord();

    // TODO: Using the real normal provides *way* worse coherency
    // vec3 normal_vs = get_view_normal(texcoord);
    vec3 normal_vs = get_view_normal_approx(texcoord);


    vec3 ray_start_vs = get_view_pos_at(texcoord);
    float pixeldist = texture(DownscaledDepth, texcoord).x;

    // Skip skybox
    if (pixeldist > 1000) {
        result = vec3(0);
        return;
    }

    // Get ray start
    vec3 view_dir = normalize(ray_start_vs);
    vec3 ray_dir = normalize(reflect(view_dir, normal_vs));
    float RxV = dot(ray_dir, view_dir);
    float max_ray_len = 10.0 * pixeldist;

    // Clip ray to near plane
    float ray_len = ((ray_start_vs.z + ray_dir.z * max_ray_len) > CAMERA_NEAR) ?
                        (CAMERA_NEAR - ray_start_vs.z) / ray_dir.z :
                        max_ray_len;
    // ray_len = max_ray_len;

    // Convert start and end pos from view to screen space
    vec3 ray_start_screen = view_to_screen(ray_start_vs);
    vec3 ray_end_screen = view_to_screen(ray_start_vs + ray_len * ray_dir);

    vec3 ray_dir_screen = ray_end_screen - ray_start_screen;

    // Make sure the ray does not leave the screen
    float scale_max_x = min(1, 0.99 * (1.0 - ray_start_screen.x) / max(1e-5, ray_dir_screen.x));
    float scale_max_y = min(1, 0.99 * (1.0 - ray_start_screen.y) / max(1e-5, ray_dir_screen.y));
    float scale_min_x = min(1, 0.99 * ray_start_screen.x / max(1e-5, -ray_dir_screen.x));
    float scale_min_y = min(1, 0.99 * ray_start_screen.y / max(1e-5, -ray_dir_screen.y));
    ray_dir_screen *= min(scale_max_x, scale_max_y);
    ray_dir_screen *= min(scale_min_x, scale_min_y);

    ray_end_screen = ray_start_screen + ray_dir_screen;

    // Linearize depth so we can interpolate it
    #if USE_LINEAR_DEPTH
        ray_start_screen.z = get_linear_z_from_z(ray_start_screen.z);
        ray_end_screen.z = get_linear_z_from_z(ray_end_screen.z);
    #endif

    vec3 ray_pos = ray_start_screen;
    vec3 ray_step = (ray_end_screen - ray_start_screen) / num_steps;
    ray_pos += 15 * ray_step * float(num_steps) / 512.0;

    vec2 intersection = vec2(-1);

    float jitter = rand(texcoord + MainSceneData.temporal_index);
    // jitter *= 0;
    ray_pos += jitter * ray_step;

    int i;
    for (i = 1; i < num_steps; ++i) {
        ray_pos += ray_step;

        // Current coordinate is in the mid of two samples, not at the end, so
        // substract half of a step
        vec2 curr_coord = ray_pos.xy - 0.5 * ray_step.xy;

        // Check for intersection
        #if USE_LINEAR_DEPTH
            float depth_sample = textureLod(DownscaledDepth, curr_coord, 0).x;
        #else
            float depth_sample = textureLod(GBuffer.Depth, curr_coord, 0).x;
        #endif



        if (point_between_planes(depth_sample, ray_pos.z, ray_pos.z - ray_step.z)) {
            intersection = curr_coord;
            break;
        }
    }

    // Check if we hit something
    if (min(intersection.x, intersection.y) < 0.0) {
        // result = vec3(0.2, 0, 0, 0);
        result = vec3(0);
        return;
    }

    // Out of screen, can early out
    if (out_of_screen(intersection)) {
        // result = vec3(0, 1, 0, 0);
        result = vec3(0);
        return;
    }

    float fade = saturate(RxV) * (1 - (i / float(num_steps - 1)));

    if (fade < 1e-3) {
        intersection = vec2(0);
        fade = 0;
    }
    result = vec3(intersection, fade);
}