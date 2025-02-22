from direct.showbase.ShowBase import ShowBase
from panda3d.core import PointLight
from panda3d.core import DirectionalLight
from panda3d.core import loadPrcFile
from panda3d.core import Vec2
import math
loadPrcFile("config\conf.prc")
#para la modificación del conf.prc
#Ahí estan todos los comandos posibles que hay para el conf.prc
#https://docs.panda3d.org/1.10/python/programming/configuration/index




class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.disableMouse()  # Desactivar control de cámara por defecto
        # Las coordenadas son en (x,z,y) donde X es de izquierda a derecha, Z arriba y abajo, Y cerca y lejos o atras y adelante.
        # Variables de la cámara en coordenadas esféricas
        self.center = (0,0,0) # Nos posicionamos en el centro.
        self.radius = 20     # Radio de la esfera inicial
        self.theta = 0       # Ángulo horizontal (en radianes)
        self.phi = math.pi / 4  # Ángulo vertical (en radianes)


        #Definimos el sol

        dlight = DirectionalLight('dlight')
        dlight.setColor((1, 1, 1, 1))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(0, 0, 0)
        render.setLight(dlnp)



        #Punto de luz celeste (de espaldas)
        plight = PointLight('plight')
        plight.setColor((2, 5, 7, 1))
        plnp = render.attachNewNode(plight)
        plnp.setPos(0, 5, 0)
        plight.attenuation = (1, 0, 0)
        render.setLight(plnp)

        
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

    def load_models(self): 
        #definimos load_models, donde le asignamos a una variable un modelo a traves del atributo .self
        #esto es así ya que le estamos dicendo por ejemplo en box, que a sí mismo se le asigne loadModel("models/box") es decir
        #que se le asigne el modelo que elegimos
        #por cada ves que querramos darle un atributo al modelo hay que refernciar a su variable, como se ve abajo:
        # box.pos lo mueve de posición, box.scale le cambia la escala y así o eso entiendo por ahora.

        """Carga los modelos 3D en la escena."""
        box = self.loader.loadModel("models/box")
        box.setPos(-3, 0, 0) #Posición de la caja
        box.reparentTo(self.render)
        
        panda = self.loader.loadModel("models/panda")
        panda.setPos(3, 0, 0)
        panda.setScale(0.2, 0.2, 0.2)
        panda.reparentTo(self.render)

        env = self.loader.loadModel("models/gopiece.bam")
        env.reparentTo(self.render)
        env.setPos(0, 0,0)
    #########  Movimientos de cámara
    def start_rotation(self):
        #Activa la rotación de la cámara al presionar la barra
        self.spacebar_held = True
        self.last_mouse_pos = None  # Reinicia la posición del mouse

    def stop_rotation(self):
        #Detiene la rotación de la cámara al soltar la barra
        self.spacebar_held = False

    def zoom_in(self):
        self.radius -= 1            #Aumentamos en 1 el radio
        self.update_camera_position()#Llamamos a la funcion que actualiza donde está la cámara


    def zoom_out(self):
        self.radius += 1
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


# Ejecutar el juego
game = MyGame()

game.run()