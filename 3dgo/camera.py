from panda3d.core import Vec2
import math
class Camera():
    def __init__(self, base, grid_size):
        self.base = base  # Store reference to ShowBase instance
        self.camera = base.camera  # Use Panda3D's camera
        self.mouseWatcherNode = base.mouseWatcherNode  # Get mouse input
        # Las coordenadas son en (x,y,z)
        # Variables de la cámara en coordenadas esféricas
        self.center = ((grid_size - 1) / 2, (grid_size - 1) / 2, (grid_size - 1) / 2) # Nos posicionamos en el centro de la  grilla a generar.
        self.radius = 30     # Radio de la esfera inicial
        self.theta = -math.pi/2    # Ángulo horizontal (en radianes) 
        self.phi = math.pi/2 # Ángulo vertical (en radianes)
        # Variables para el control de la cámara
        self.spacebar_held = False
        self.last_mouse_pos = None
        # Start task for continuous rotation update
        self.base.taskMgr.add(self.update_camera_rotation, "update_camera_rotation")
        # Set initial camera position
        self.update_camera_position()
        
    #########  Movimientos de cámara
    def start_rotation(self):
        #Activa la rotación de la cámara al presionar la barra
        self.spacebar_held = True
        self.last_mouse_pos = None  # Reinicia la posición del mouse

    def stop_rotation(self):
        #Detiene la rotación de la cámara al soltar la barra
        self.spacebar_held = False

    def zoom_in(self):
        if  self.radius > 2:  # Evita que el radio sea menor que 2
            self.radius -= 1  # Reducimos el radio de la bola, por lo tanto nos acercamos
            self.update_camera_position()

    def zoom_out(self):
        if  self.radius < 100:  # limite para el zoom
            self.radius += 1   # Aumentamos el radio de la bola, por lo tanto nos alejamos
            self.update_camera_position()
            
    def rotate_left(self):
        """Rotate camera left"""
        self.theta += math.radians(5)  # Rotate left by 5 degrees
        self.update_camera_position()

    def rotate_right(self):
        """Rotate camera right"""
        self.theta -= math.radians(5)  # Rotate right by 5 degrees
        self.update_camera_position()

    def rotate_up(self):
        """Rotate camera up"""
        if self.phi < math.radians(170):  # Prevent flipping
            self.phi += math.radians(5)
        self.update_camera_position()

    def rotate_down(self):
        """Rotate camera down"""
        if self.phi > math.radians(10):  # Prevent flipping
            self.phi -= math.radians(5)
        self.update_camera_position()

    def update_camera_rotation(self, task):
        """Update camera rotation when spacebar is held."""
        if self.spacebar_held and self.mouseWatcherNode.hasMouse():
            mouse_pos = Vec2(self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY())

            if self.last_mouse_pos:
                delta = mouse_pos - self.last_mouse_pos

                self.theta -= delta.x * 3  # Horizontal movement
                self.phi += delta.y * 3  # Vertical movement

                # Restrict vertical angle to avoid flipping
                self.phi = max(math.radians(10), min(math.radians(170), self.phi))

                self.update_camera_position()

            self.last_mouse_pos = mouse_pos  # Save last mouse position

        return task.cont

    def update_camera_position(self):
        """Calcula la posición de la cámara en coordenadas esféricas."""
        x = self.center[0] + self.radius * math.sin(self.phi) * math.cos(self.theta)
        y = self.center[1] + self.radius * math.sin(self.phi) * math.sin(self.theta)
        z = self.center[2] + self.radius * math.cos(self.phi)

        self.camera.setPos(x, y, z)
        self.camera.lookAt(*self.center)  # Camera always look to the center