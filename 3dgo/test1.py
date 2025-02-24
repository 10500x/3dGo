from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4
from panda3d.core import loadPrcFile
from panda3d.core import Vec2, Vec3
from panda3d.core import LineSegs, NodePath, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue
import math

class Board(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        #Light initialization
        self.setup_lighting()
        #Shader initialization (not necessary)
        #render.setShaderAuto()
        #self.render.setShaderAuto()

        self.grid_size = 5 # Grid size, always gridsize-1 
        self.spacing = 1  # Space between lines
        self.create_grid(self.grid_size,self.spacing)

        # 🌎 Ambient Light (Softens Shadows, Makes Everything Visible)
        ambient_light = AmbientLight("ambient")
        ambient_light.setColor(Vec4(0.5, 0.5, 0.5, 1))  # Soft white light
        ambient_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_np)

        # ☀️ Directional Light (Like Sunlight, Creates Shadows)
        directional_light = DirectionalLight("directional")
        directional_light.setColor(Vec4(1, 1, 1, 1))  # White strong light
        dir_light_np = self.render.attachNewNode(directional_light)
        dir_light_np.setHpr(45, -60, 0)  # Angled downwards (like sunlight)

        self.render.setLight(dir_light_np)

        self.disableMouse()  # Desactivar control de cámara por defecto
        # Las coordenadas son en (x,y,z)
        # Variables de la cámara en coordenadas esféricas
        self.center = (self.grid_size/2, self.grid_size/2, self.grid_size/4) # Nos posicionamos en el centro de la  grilla a generar.
        self.radius = 20     # Radio de la esfera inicial
        self.theta = 0       # Ángulo horizontal (en radianes)
        self.phi = math.pi / 4  # Ángulo vertical (en radianes)

        # Variables para el control de la cámara
        self.spacebar_held = False
        self.last_mouse_pos = None

        # Cargar modelos
        self.load_models() #llamamos a load_models para que cargue los modelos que tenemos

        # Eventos del teclado
        self.accept("space", self.start_rotation)  #Le decimos que al tocar la tecla "space" llame a la función start_rotation
        self.accept("space-up", self.stop_rotation) #Cuando se deja de presiona "space" se llama a stop_rotation
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)
        # Agregar la tarea de actualizar la cámara
        self.taskMgr.add(self.update_camera_rotation, "camera_rotation_task")

    def setup_lighting(self):
        """Adds ambient and directional lighting."""
  
    def create_grid(self,size,spacing):
        # Create a node for the grid
        grid_node = LineSegs("grid")
        grid_node.setThickness(1)  # Adjust thickness of lines

        # Store intersection points
        intersections = []

        # Generate horizontal and vertical lines
        for h in range (0,size+1):
            for i in range(0,size+1):
                x = i * spacing
                y = i * spacing

                # Horizontal line
                grid_node.moveTo(0, x, h/2)
                grid_node.drawTo(size * spacing, x, h/2)

                # Vertical line
                grid_node.moveTo(y, 0, h/2)
                grid_node.drawTo(y, size * spacing, h/2)

                # Add intersection points
                for j in range(size+1):
                    intersections.append((j * spacing, i * spacing, h/2))

        # Convert to node
        grid_np = NodePath(grid_node.create())
        grid_np.reparentTo(self.render)

        # Place spheres at intersections
        for pos in intersections:
            self.create_vertex_object(pos)






    def create_vertex_object(self, position):
        """Creates a small sphere at a given position."""
        sphere = self.loader.loadModel("smiley")  # Using a built-in model for example
        sphere.setScale(0.025)  # Make it small
        sphere.setPos(*position)
        sphere.reparentTo(self.render)
        sphere.setTexture(self.loader.loadTexture("textures/black.png"), 1)
 

    def load_models(self): # Go pieces models initialization, textures and such.
        #White piece and black piece load and attributes
        white = self.loader.loadModel("models/gopiece.bam") #Asing the model gopiece to the object white
        white.setTexture(self.loader.loadTexture("textures/white.png"), 1)  # Apply texture (texture,alpha)
        white.reparentTo(self.render)       # It's shown
        white.setPos(0, 0,0)                # Set position (only for now)
        white.setScale(0.49,0.49,0.49)      # Set scale this is like this because black stones are slighlty larger than white ones.
        #white.setShaderAuto()   #shadow

        black = self.loader.loadModel("models/gopiece.bam")
        black.setTexture(self.loader.loadTexture("textures/black.png"), 1)  
        black.reparentTo(self.render)
        black.setPos(1, 0,0)
        black.setScale(0.5,0.5,0.5)
        #black.setShaderAuto() #shadow

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
    ##########


    def update_camera_rotation(self, task):
        """Actualiza la cámara si la barra espaciadora está presionada."""
        if self.spacebar_held and self.mouseWatcherNode.hasMouse():
            mouse_pos = Vec2(self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY())

            if self.last_mouse_pos:
                delta = mouse_pos - self.last_mouse_pos

                # Ajustar los ángulos en base al movimiento del mouse
                self.theta -= delta.x * 3  # Movimiento horizontal
                self.phi += delta.y * 3  # Movimiento vertical

                # Restringir el ángulo vertical entre 10° y 170° para evitar invertir la cámara
                self.phi = max(math.radians(10), min(math.radians(170), self.phi))

                self.update_camera_position()

            self.last_mouse_pos = mouse_pos  # Guardar la última posición del mouse

        return task.cont

    def update_camera_position(self):
        """Calcula la posición de la cámara en coordenadas esféricas."""
        x = self.center[0] + self.radius * math.sin(self.phi) * math.cos(self.theta)
        y = self.center[1] + self.radius * math.sin(self.phi) * math.sin(self.theta)
        z = self.center[2] + self.radius * math.cos(self.phi)

        self.camera.setPos(x, y, z)
        self.camera.lookAt(self.center)  # Hacer que la cámara siempre mire al centro


class Point(): 
    '''
    This class represents a Point in Go Board 
    Atributes: 
    - coordinates : posicion in the Go Board
    - status : empty, black or white
    - canvas : canvas that represents the board where the point is
    - stoneID : the circle drawn in the canvas when the point is not empty
    - neighbors : set of neighbors, initialized empty but assigned manualy, 3,4, 5 or 6, for corner, edge, lateral or central points respectively
    '''
    def __init__(self, coordinates):
        self.coordinates = coordinates 
        self.status = 'empty'
        self.canvas = None     
        self.stoneID = None         
        self.neighbors = set()    

    def find_conected(self,conected): 
        '''
        returns the set of all the points of the same color that are conected with the point.
        '''
        if self.status != 'empty':
            conected.add(self)

            for n in self.neighbors-conected:
                if self.status == n.status:
                    n.find_conected(conected)
        return conected

    
    def death_decision(self, test = False): 
        '''
        decides whether a point should die, (True = the point should die). If test = True
        the function does not change the point status nor delete the stone, if test = False
        the function deletes permanently all the conectd component of the point and changes the stastus of them. 
        '''
        conected = set()
        conected = self.find_conected(conected)
        b = False
        if len(conected) != 0: 
            b = True
            for m in conected:
                for q in m.neighbors:
                    b = b and (q.status != 'empty')
            if (b and not(test)):
                for m in conected:
                    canvas = m.canvas
                    m.status = 'empty'
                    canvas.delete(m.stoneID)
        return b

# Ejecutar el juego
game = Board()

game.run()