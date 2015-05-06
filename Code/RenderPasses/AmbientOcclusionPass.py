
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class AmbientOcclusionPass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "AmbientOcclusionPass"

    def getRequiredInputs(self):
        return {
            "frameIndex": "Variables.frameIndex",
            "mainRender": "Variables.mainRender",
            "mainCam": "Variables.mainCam",
            "noiseTexture": "Variables.noise4x4",
            "viewSpaceNormals": "ViewSpacePass.normals",
            "viewSpacePosition": "ViewSpacePass.position"
        }

    def setSize(self, size):
        self.size = size

    def create(self):
        self.target = RenderTarget("AmbientOcclusion")
        self.target.setSize(self.size.x, self.size.y)
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ComputeOcclusion.fragment")
        self.target.setShader(shader)

    def getOutputs(self):
        return {
            "AmbientOcclusionPass.computeResult": lambda: self.target.getColorTexture(),
        }

    def setShaderInput(self, name, value):
        self.target.setShaderInput(name, value)