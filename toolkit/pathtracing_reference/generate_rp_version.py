"""

Renders the sphere using the render pipeline

"""

import sys
from panda3d.core import load_prc_file_data
from direct.showbase.ShowBase import ShowBase

class Application(ShowBase):

    def __init__(self):
        sys.path.insert(0, "../../")
        load_prc_file_data("", "win-size 512 512")
        # load_prc_file_data("", "win-size 1024 1024")

        from rpcore import RenderPipeline, PointLight

        self.render_pipeline = RenderPipeline()
        self.render_pipeline.mount_mgr.config_dir = "config/"
        self.render_pipeline.create(self)

        sphere = loader.loadModel("sphere.bam")
        sphere.ls()
        sphere.reparent_to(render)

        self.disableMouse()
        self.camLens.setFov(40)
        self.camLens.setNearFar(0.03, 15.0)
        self.camera.set_pos(0, -3.5, 0)
        self.camera.look_at(0, -2.5, 0)

        self.render2d.hide()
        self.aspect2d.hide()

        light = PointLight()
        light.pos = 10, -10, 10
        light.radius = 1e20
        light.color = (1, 1, 1)
        light.lumens = 90
        self.render_pipeline.add_light(light)

        for mat in sphere.find_all_materials():
            mat.roughness = 0.05
            mat.base_color = (1, 1, 1, 1)
            mat.refractive_index = 1.51
            print(mat)

        for i in range(10):
            self.taskMgr.step()

        self.win.save_screenshot("scene-rp.png")

        base.accept("r", self.reload)

    def reload(self):
        print("Reloading")
        self.render_pipeline.reload_shaders()
        self.taskMgr.step()
        self.taskMgr.step()
        self.win.save_screenshot("scene-rp.png")

Application().run()
