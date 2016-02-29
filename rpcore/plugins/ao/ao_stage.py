"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from panda3d.core import LVecBase2i
from rpcore.render_stage import RenderStage

class AOStage(RenderStage):

    required_pipes = ["GBuffer"]
    required_inputs = ["Noise4x4"]

    @property
    def produced_pipes(self):
        return {"AmbientOcclusion": self.target_upscale.color_tex}

    def create(self):
        self.target = self.make_target2("Sample")
        self.target.size = -2
        self.target.add_color_attachment(alpha=True)
        self.target.prepare_buffer()
        self.target.quad.set_instance_count(4)

        self.target_merge = self.make_target2("Merge")
        self.target_merge.size = -2
        self.target_merge.add_color_attachment(alpha=True)
        self.target_merge.prepare_buffer()

        self.target_blur_v = self.make_target2("BlurV")
        self.target_blur_v.size = -2
        self.target_blur_v.add_color_attachment(alpha=True)
        self.target_blur_v.prepare_buffer()

        self.target_blur_h = self.make_target2("BlurH")
        self.target_blur_h.size = -2
        self.target_blur_h.add_color_attachment(alpha=True)
        self.target_blur_h.prepare_buffer()

        self.target_upscale = self.make_target2("Upscale")
        self.target_upscale.add_color_attachment(alpha=True)
        self.target_upscale.prepare_buffer()

        self.target_upscale.set_shader_input("SourceTex", self.target_blur_h.color_tex)
        self.target_blur_v.set_shader_input("SourceTex", self.target_merge.color_tex)
        self.target_blur_h.set_shader_input("SourceTex", self.target_blur_v.color_tex)

        self.target_blur_v.set_shader_input("blur_direction", LVecBase2i(0, 1))
        self.target_blur_h.set_shader_input("blur_direction", LVecBase2i(1, 0))

        self.target_merge.set_shader_input("SourceTex", self.target.color_tex)

    def set_shaders(self):
        self.target.shader = self.load_plugin_shader(
            "$$shader/sample_halfres_interleaved.vert.glsl", "ao_sample.frag.glsl")
        self.target_upscale.shader = self.load_plugin_shader(
            "$$shader/bilateral_upscale.frag.glsl")
        self.target_merge.shader = self.load_plugin_shader(
            "$$shader/merge_interleaved_target.frag.glsl")

        blur_shader = self.load_plugin_shader(
            "$$shader/bilateral_halfres_blur.frag.glsl")
        self.target_blur_v.shader = blur_shader
        self.target_blur_h.shader = blur_shader