
import struct

from panda3d.core import PTAInt, Texture, Shader

from .Util.DebugObject import DebugObject
from .Util.Image import Image
from .RenderTarget import RenderTarget

from ..Native import GPUCommand

class GPUCommandQueue(DebugObject):

    """ This class offers an interface to the gpu, allowing commands to be
    pushed to a queue which then get executed on the gpu """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GPUCommandQueue")
        self._pipeline = pipeline
        self._commands_per_frame = 30
        self._pta_num_commands = PTAInt.empty_array(1)
        self._create_data_storage()
        self._create_command_target()
        self._commands = []

    def clear_queue(self):
        """ Clears all commands currently being in the queue """
        raise NotImplementedError()

    def process_queue(self):
        """ Processes the n first commands of the queue """
        self._data_texture.clear_image()
        commands = self._commands[:self._commands_per_frame]
        self._commands = self._commands[self._commands_per_frame:]
        self._pta_num_commands[0] = len(commands)
        pointer = self._data_texture.get_texture().modify_ram_image()
        
        # Pack the data into the buffer
        for idx, command in enumerate(commands):
            command.enforce_width(32)
            command.write_to(pointer, idx)

    def add_command(self, command):
        """ Adds a new command """
        assert isinstance(command, GPUCommand)
        self._commands.append(command)

    def reload_shaders(self):
        """ Reloads the command shader """
        shader = Shader.load(Shader.SL_GLSL,
                             "Shader/DefaultPostProcess.vertex.glsl",
                             "Shader/ProcessCommandQueue.fragment.glsl")
        self._command_target.set_shader(shader)

    def register_input(self, key, val):
        """ Registers an new shader input to the command target """
        self._command_target.set_shader_input(key, val)

    def _create_data_storage(self):
        """ Creates the buffer used to transfer commands """
        command_buffer_size = self._commands_per_frame * 32
        self.debug("Allocating command buffer of size", command_buffer_size)
        self._data_texture = Image.create_buffer("CommandQueue",
            command_buffer_size, Texture.T_float, Texture.F_r32)
        self._data_texture.set_clear_color(0)

    def _create_command_target(self):
        """ Creates the target which processes the commands """
        self._command_target = RenderTarget("CommandTarget")
        self._command_target.set_size(1, 1)
        self._command_target.prepare_offscreen_buffer()
        self._command_target.set_shader_input("CommandQueue", self._data_texture.get_texture())
        self._command_target.set_shader_input("commandCount", self._pta_num_commands)