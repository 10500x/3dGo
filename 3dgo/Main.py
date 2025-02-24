from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile
from camera import Camera
from grid import Grid
loadPrcFile("config\conf.prc")

class Main(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse() # deactivate the mouse for movement.
        self.grid_size = 5 # Grid size, always gridsize-1 
        self.spacing = 1  # Space between lines

        self.camera_control = Camera(self, self.grid_size) #invocar a la camara
        self.grid = Grid(self.grid_size, self.spacing, self.render, self.loader)

        # Bind keys for camera control
        self.accept("space", self.camera_control.start_rotation)  # Press space to rotate
        self.accept("space-up", self.camera_control.stop_rotation)  # Release space to stop

        self.accept("wheel_up", self.camera_control.zoom_in)  # Scroll up to zoom in
        self.accept("wheel_down", self.camera_control.zoom_out)  # Scroll down to zoom out

        # Bind arrow keys for movement, fixed angle.
        self.accept("arrow_left", self.camera_control.rotate_left) 
        self.accept("arrow_right", self.camera_control.rotate_right)
        self.accept("arrow_up", self.camera_control.rotate_up)
        self.accept("arrow_down", self.camera_control.rotate_down)

game = Main()

game.run()