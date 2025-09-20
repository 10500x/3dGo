from panda3d.core import NodePath, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue, CollisionRay, TextNode, DirectionalLight, AmbientLight
from panda3d.core import AntialiasAttrib 
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectEntry, DGG, DirectOptionMenu, DirectButton
from panda3d.core import ClockObject
from panda3d.core import Material
from camera import Camera
import hashlib
globalClock = ClockObject.getGlobalClock()
from panda3d.core import loadPrcFile, Point3, LineSegs, WindowProperties
# Load configuration file
loadPrcFile("config/conf.prc")

class GridDemo(ShowBase):
    def __init__(self, size):
        super().__init__()
        self.render.setAntialias(AntialiasAttrib.MLine) #Antialias just for the grid
        self.custom_font = self.loader.loadFont("fonts/Montserrat-Regular.ttf")
        self.initial_size = size
        self.size = "0,0,0" #Initialize the default size value as 0,0,0, same to every cord.
        self.x_size =1
        self.y_size =1
        self.z_size =1
        self.extra_gui_elements = {}
        self.background_color=(0.5, 0.5, 0.5)#default background color
        self.setBackgroundColor(self.background_color) #Background color
        self.ball_model = self.loader.loadModel("models/sphere.bam")    #Preload of model and texture for stones
        self.black_texture = self.loader.loadTexture("textures/black.png")
        self.white_texture = self.loader.loadTexture("textures/white.png")
        self.camera_control = Camera(self, self.initial_size)
        self.black_points = 0   #Set both player points to zero, komi is added later
        self.white_points = 0   #
        self.black_captures = 0 
        self.white_captures = 0
        self.komi =0.5 #default komi as 0.5, 6.5 It's just too much.
        self.pass_count = 0  
        self.game_ended = False
        self.match_history=[] #Set of the position of the balls at any given turn, might be unefficient but I have no idea how to do it if not by this, this is for proper rewind and forward the match
        self.vertices = []      #Set of vertices, same as collision spheres but no the same object.
        self.edges = []         #Set of edges
        self.nodes = []         #Set of nodes, collision spheres particularly.
        self.line_nodes = []    # Initialize line_nodes here, before generate_grid
        self.balls = {}         #Set of balls, that is  {"pos":(x,y,z) "color": 0,1} where 0 or 1 represent black or white acordingly
        self.current_color = 0  #Set the current color, as 0 = black, 1 = white, as is the first turn, black plays.
        self.turn = 1           #Set the turn 
        self.last_plane_action=None
        self.current_plane = -1 #Set the current plane to the last one, so when the show one plane it's called it shows the first one.
        self.layer_count=0 #Set the layer count to 1 so the first one to be deleted it's the outer most.
        self.setup_collision_system()
        self.disableMouse() #Disable mouse default keys
        self.bind_inputs()  #Initialize the hotkeys
        self.help_show=0 #Initialize both extra gui to be disable by default that is not shown.
        self.extra_show=0
        self.grid_color=(1,1,1)#Initialize the color for the grid, white color (panda uses rgb but map it from 1-255 into 0-1)
         # Timer-related attributes

        #Model material
        self.myMaterial = Material()
        self.myMaterial.setShininess(16) # Make this material shiny
        self.myMaterial.setSpecular((0.25, 0.25, 0.25, 1)) # Make this material blue
        #self.myMaterial.setDiffuse((0.25, 0.25, 0.25, 1))
        #### LIGHT
        #D light
        dlight = DirectionalLight('dlight')
        dlight.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, -45)
        self.render.setLight(dlnp)
        # A light
        alight = AmbientLight('alight')
        alight.setColor((0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        #LIGHT 


         ######## WIP
        self.model_scale=0.30 #Set the default size of the model to 0.35
        ###### WIP
        self.timer_running = False
        self.black_time = 0  # Time in seconds for black player
        self.white_time = 0  # Time in seconds for white player
        self.active_timer = None  # 'black' or 'white'
        self.timer_mode = "No Timer"  # Default mode
        self.main_time = 0  # Default 5 minutes in seconds
        self.increment = 0  # Default incremental time in seconds
        self.byo_periods = 5  # Default Byo-yomi periods
        self.byo_time = 30  # Default Byo-yomi period time in seconds
        self.black_byo_periods_left = self.byo_periods
        self.white_byo_periods_left = self.byo_periods
        self.black_time = self.main_time  # Black's remaining main time
        self.white_time = self.main_time  # White's remaining main time
        self.black_byo_yomi_time = self.byo_time  # Black's current byo-yomi period time
        self.white_byo_yomi_time = self.byo_time  # White's current byo-yomi period time
        self.black_byo_yomi_periods = self.byo_periods  # Black's remaining byo-yomi periods
        self.white_byo_yomi_periods = self.byo_periods  # White's remaining byo-yomi periods
        self.timer_running = False
        self.timer_task = None    
        

        self.setup_gui()
        self.game_over_text = OnscreenText(
            text="To start, select a grid size and press enter.",
            pos=(0, 0), scale=0.1, fg=(0, 0, 0, 1), align=TextNode.ACenter,font= self.custom_font
        )
    
    def save_game(self):
        if (self.turn==1):
            return
        with open("./save/savegame.txt","w") as f:
            f.write(str(self.match_history[self.turn-2]))
            f.close
            
    def load_game(self):
        with open("./save/*.txt","r") as f:
            loaded=f.read()
            print (loaded)
    
    def setup_collision_system(self):
        self.cTrav = CollisionTraverser()  # Collision traverser for raycasting
        self.pickerQueue = CollisionHandlerQueue()  # Queue to store collision results
        self.pickerNode = CollisionNode("mouseRay")  # Node for the ray
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)  # Attach ray to camera
        self.pickerRay = CollisionRay()  # Ray for detecting collisions
        self.pickerNode.addSolid(self.pickerRay)  # Add ray to the node
        self.pickerNode.setFromCollideMask(1)  # Set collision mask to detect only objects with mask 1
        self.cTrav.addCollider(self.pickerNP, self.pickerQueue)  # Add collider to traverser

    def bind_inputs(self):
        #Bind keyboard and mouse inputs for game controls
        # Camera controls
        self.accept("space", self.camera_control.start_rotation)
        self.accept("space-up", self.camera_control.stop_rotation)
        self.accept("wheel_up", self.camera_control.zoom_in)
        self.accept("wheel_down", self.camera_control.zoom_out)
        self.accept("arrow_left", self.camera_control.rotate_left)
        self.accept("arrow_right", self.camera_control.rotate_right)
        self.accept("arrow_up", self.camera_control.rotate_up)
        self.accept("arrow_down", self.camera_control.rotate_down)
        self.accept("s", self.cut_layer)
        #UI and game controls
        self.accept("a", self.points)
        self.accept("x", self.gui_help)
        self.accept("c", self.gui_extra)
        self.accept("d", self.rewind_turn) # Bind "d" ket to the rewind button
        self.accept("z", self.pass_turn)  # Bind 'z' key to pass
        self.accept("mouse1", self.check_click)  # Left click to place pieces
        self.accept("mouse3", self.camera_control.start_rotation)
        self.accept("mouse3-up", self.camera_control.stop_rotation)
        self.accept("r", self.call_reset_camera)  # Reset camera to grid center
        self.accept("q", self.plane_down)  # Show next horizontal plane 0 for going down, 1 to up.
        self.accept("e", self.plane_up)  # Show past horizontal plane
        self.accept("w", self.show_everything)  # Show all planes


    def call_reset_camera(self):
        self.reset_camera(self.size)
    def place_initial_ball(self): #place a black ball to represent the 0,0,0
        initial_ball = self.loader.loadModel("smiley")
        initial_ball.setPos(0, 0, 0)
        initial_ball.setTexture(self.loader.loadTexture("textures/blue.png"), 1)
        initial_ball.setScale(0.05)
        initial_ball.reparentTo(self.render)

    def pass_turn(self):
        if self.game_ended:

            return
        self.pass_count += 1
        self.current_color = ((self.current_color + 1)%2)
        self.turn += 1
        self.turn_text.setText(f"Turn: {self.turn}")
        if(self.timer_mode=="Byo yomi"):
            # Reset byo-yomi time for the player who just passed
            if self.current_color == 0:  # White just passed, reset Black's byo-yomi
                self.black_byo_yomi_time = self.byo_time
                self.black_byo_yomi_periods = self.byo_periods
            else:  # Black just passed, reset White's byo-yomi
                self.white_byo_yomi_time = self.byo_time
                self.white_byo_yomi_periods = self.byo_periods

        self.start_timer()  # Restart timer for the next player
        self.check_game_end()
        

    def check_game_end(self):
        if self.pass_count >= 2:
            self.end_game()


    def points(self):
        self.black_points = self.black_captures + self.calculate_territory(0)
        self.white_points = self.white_captures + self.calculate_territory(1) + self.komi  # Komi of 6.5
        self.text_points.setText(text=f"Black points: {self.black_points}\nWhite points: {self.white_points}")
        self.text_captures.setText(text=f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")
                  
    def end_game(self):
        self.game_ended = True
        self.pause_timer()
        self.show_everything()
        self.points()
        winner = "Black" if self.black_points > self.white_points else "White" if self.white_points > self.black_points else "Draw"
        self.game_over_text = OnscreenText(
            text=f"Game Over! {winner} wins!",
            pos=(0, 0), scale=0.1, fg=(0, 1, 0, 1), align=TextNode.ACenter,font= self.custom_font
        )
    def reset_game(self):
        self.game_ended = False
        self.pass_count = 0
        self.white_points=0
        self.black_points=0
        self.layer_count =0
        self.pause_timer()
        self.show_everything()


    

    def calculate_territory(self, color):
        territory = 0
        visited = set()
        for x in range(self.x_size):
            for y in range(self.y_size):
                for z in range(self.z_size):
                    pos = (x, y, z)
                    if pos not in self.balls and pos not in visited:# flood-fill to check if surrounded by one color
                        region = self.get_region(pos, visited)
                        is_territory = True
                        for reg_pos in region:
                            adj_positions = self.get_adjacent_positions(reg_pos)
                            for adj in adj_positions:
                                if adj in self.balls and self.balls[adj]['color'] != color:
                                    is_territory = False
                                    break
                            if not is_territory:
                                break
                        if is_territory:
                            territory += len(region)
        return territory
    
    def get_region(self, pos, visited):#Flood-fill to find a connected empty region.
        if pos in self.balls or pos in visited or not (0 <= pos[0] < self.x_size and 0 <= pos[1] < self.y_size and 0 <= pos[2] < self.z_size):
            return set()
        region = set()
        to_check = [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current in self.balls:
                continue
            visited.add(current)
            region.add(current)
            to_check.extend([adj for adj in self.get_adjacent_positions(current) 
                            if adj not in self.balls and adj not in visited])
        return region

    def generate_grid(self, size):
         try:
            size = [int(x.strip()) for x in size_str.split(',')]
            if len(size) == 1:
                x_size = y_size = z_size = size[0]
            elif len(size) == 2:
                x_size, y_size = size
                z_size = 1
            else:
                x_size, y_size, z_size = size
        # Clear existing balls
        for ball_data in list(self.balls.values()):
            ball_data['node'].removeNode()
        self.balls.clear()

        # Clear existing nodes
        for node in self.nodes:
            if not node.is_empty():
                collision_node = node.find("**/+CollisionNode")
                if collision_node:
                    collision_node.removeNode()
                node.removeNode()

        # Clear existing line nodes
        for line_node in self.line_nodes:
            line_node.removeNode()
        self.line_nodes = []

        self.nodes = []
        self.edges = []
        self.vertices = []
        
        # Generate vertices and collision nodes
        for x in range(self.x_size):
            for y in range(self.y_size):
                for z in range(self.z_size):
                    vertex_node = NodePath(f"vertex_{x},{y},{z}")
                    vertex_node.setPos(x, y, z)
                    vertex_node.reparentTo(self.render)
                    collision_sphere = CollisionSphere(0, 0, 0, 0.25)
                    collision_node = vertex_node.attachNewNode(CollisionNode(f'cnode_{x}{y}{z}'))
                    collision_node.node().addSolid(collision_sphere)
                    collision_node.node().setIntoCollideMask(1)
                    collision_node.setColor(0.5, 0.5, 0.5, 1)
                    #collision_node.show() #only for debug purpose, show the collison_nodes. Bad performance althougt I like how it looks. 
                    if x + 1 < self.x_size:
                        self.edges.append(((x, y, z), (x + 1, y, z)))
                    if y + 1 < self.y_size:
                        self.edges.append(((x, y, z), (x, y + 1, z)))
                    if z + 1 < self.z_size:
                        self.edges.append(((x, y, z), (x, y, z + 1)))
                    self.vertices.append((x, y, z))
                    self.nodes.append(vertex_node)
        for z in range(self.z_size):
            # Create a single LineSegs object for this z layer
            lines = LineSegs()
            lines.setThickness(1)  # Set line thickness
            lines.setColor(1, 1, 1, 1)  # Set color to white

            # Draw horizontal lines (along x-axis) for each y
            for y in range(self.y_size):
                lines.moveTo(0, y, z)
                lines.drawTo(self.x_size - 1, y, z)

            # Draw vertical lines (along y-axis) for each x
            for x in range(self.x_size):
                lines.moveTo(x, 0, z)
                lines.drawTo(x, self.y_size - 1, z)

            # Create a NodePath for the lines and add to render
            line_node = self.render.attachNewNode(lines.create())
            self.line_nodes.append(line_node)
        self.game_over_text.destroy()  
        self.reset_camera(self.size)
        self.place_initial_ball
        self.custom_grid_color(self.grid_color)
        
        
        
    def custom_background_color(self, event=None):
        if self.extra_show == 1 and "background_entry" in self.extra_gui_elements:
            text = self.extra_gui_elements["background_entry"].get()
        else:
            if isinstance(event, tuple) and len(event) == 3:
                text = ','.join(str(int(c * 255)) for c in event)
            else:
                text = ','.join(str(int(c * 255)) for c in self.background_color)

        try:
            color = [int(x.strip()) for x in text.split(',')]
            if len(color) != 3:
          
                return
            r, g, b = color
            
            r, g, b = r / 255.0, g / 255.0, b / 255.0
            if not all(0 <= c <= 1 for c in (r, g, b)):
               
                return
            self.setBackgroundColor(r, g, b)
            self.background_color = (r, g, b)  # Update stored color
        except ValueError:
            return
       
        except Exception as e:
            return
           
    def custom_grid_color(self, event=None):
        # Use color_entry text only if GUI is active and entry exists
        if self.extra_show == 1 and "color_entry" in self.extra_gui_elements:
            text = self.extra_gui_elements["color_entry"].get()
        else:
            # Fallback to event or self.grid_color
            if isinstance(event, tuple) and len(event) == 3:
                text = ','.join(str(int(c * 255)) for c in event)
            else:
                text = ','.join(str(int(c * 255)) for c in self.grid_color)

        try:
            color = [int(x.strip()) for x in text.split(',')]
            if len(color) != 3:
                return
            r, g, b = color
            
            r, g, b = r / 255.0, g / 255.0, b / 255.0
            if not all(0 <= c <= 1 for c in (r, g, b)):
                return

            for line_node in self.line_nodes:
                line_node.removeNode()
            self.line_nodes = []

            self.grid_color = (r, g, b)

            for z in range(self.z_size):  
                lines = LineSegs()
                lines.setThickness(1)
                lines.setColor(r, g, b, 1)
                for y in range(self.y_size):  
                    lines.moveTo(0, y, z)
                    lines.drawTo(self.x_size - 1, y, z)  
                for x in range(self.x_size):  
                    lines.moveTo(x, 0, z)
                    lines.drawTo(x, self.y_size - 1, z)  
                line_node = self.render.attachNewNode(lines.create())
                self.line_nodes.append(line_node)

        except ValueError:
            return
        except Exception as e:
            return
       
        
        
    def set_grid_size(self, input_text=None): #set the grid size to the user input
        text = self.size_entry.get() if input_text is None else str(input_text)
        try:
            self.reset_game()
            self.size = text
            self.generate_grid(self.size)  # Regenerate grid with new size
            self.turn = 1  # Reset turn for new grid
            self.balls.clear()  # Clear existing balls (already in generate_grid, but ensure consistency)
            self.place_initial_ball()  # Place new initial ball
            if self.timer_mode != "No timer":
                self.reset_timers()
                self.pause_timer()
            else:
                return
            self.turn_text.setText(f"Turn: {self.turn}")
            self.size_entry["focus"] = 0  # Clear focus after submission
        except ValueError:
            return

    def gui_help(self):
        #props = self.win.getProperties()
        #win_width = props.getXSize()
        #win_height = props.getYSize()
        #aspect_ratio = win_width / win_height if win_height > 0 else 1.0
        if not self.custom_font.isValid():
            self.custom_font = None
        if self.help_show==0:
            self.hotkeys = OnscreenText(
                text="Press space and move the mouse to rotate\nLeft click to play\nRight click to change the center\nR to reset camera\nE to show one plane up\n"
                "Q to show one plane down\nW to show everything\nA to count points,\nZ to pass\nD to rewind\nS to shrink a layer)",
                pos=(-1.9, 0.2), scale=0.07, align=TextNode.ALeft,font= self.custom_font
            )
        else:
            self.hotkeys.destroy()
        self.help_show = 1 - self.help_show 

    def gui_extra(self):
        if self.extra_show == 0:
            
            # Define GUI elements in a list of tuples: (name, type, kwargs)
            gui_definitions = [
                #Grid Color
                ("color_label", OnscreenText, {"text": "Grid color, r,g,b", "pos": (1.9, -0.20), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font}),
                ("color_entry", DirectEntry, {"text": "", "scale": 0.05, "command": self.custom_grid_color, "initialText": "", "pos": (1, 0, -0.2), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1), "width": 6}),
                #("submit_button_color", DirectButton, {"text": "Set color", "scale": 0.05, "command": self.custom_grid_color, "pos": (0.7, 0, -0.2), "frameColor": (0, 1, 0, 0.5), "text_fg": (1, 1, 1, 1)}),
                #Background color
                ("background_label", OnscreenText, {"text": "Bg color, r,g,b", "pos": (1.9, -0.30), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font}),
                ("background_entry", DirectEntry, {"text": "", "scale": 0.05, "command": self.custom_background_color, "initialText": "", "pos": (1, 0, -0.3), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1), "width": 6}),
                #("submit_button_back_color", DirectButton, {"text": "Set color", "scale": 0.05, "command": self.custom_background_color, "pos": (0.7, 0, -0.3), "frameColor": (0, 1, 0, 0.5), "text_fg": (1, 1, 1, 1)}),
                #Komi
                ("komi_label", OnscreenText, {"text": "Komi", "pos": (1.9, -0.4), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font}),
                ("komi_entry", DirectEntry, {"text": "", "scale": 0.05, "command": self.set_komi, "initialText": "", "pos": (1, 0, -0.4), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1), "width": 3}),
                #Timer stuff
                ("timer_label", OnscreenText, {"text": "Time (s)", "pos": (1.9, -0.60), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font}),
                ("timer_mode_menu", DirectOptionMenu, {"scale": 0.05, "items": ["No timer", "Absolute", "Fischer", "Byo-yomi"], "command": self.set_timer_mode, "initialitem": 0, "pos": (1, 0, -0.5), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1)}),
                ("main_time_entry", DirectEntry, {"text": "", "scale": 0.05, "command": self.set_main_time, "initialText": "300", "pos": (1, 0, -0.6), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1), "width": 4}),
                ("main_time_label", OnscreenText, {"text": "Time Method", "pos": (1.9, -0.50), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font}),
                ("increment_entry", DirectEntry, {"text": "", "scale": 0.05, "command": self.set_increment, "initialText": "0", "pos": (1, 0, -0.7), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1), "width": 4}),
                ("increment_label", OnscreenText, {"text": "Increment (s)", "pos": (1.9, -0.70), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font}),
                ("byo_time_entry", DirectEntry, {"text": "", "scale": 0.05, "command": self.set_byo_time, "initialText": "30", "pos": (1, 0, -0.8), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1), "width": 4}),
                ("byo_time_label", OnscreenText, {"text": "Byo-yomi Time (s)", "pos": (1.9, -0.80), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font}),
                ("byo_periods_entry", DirectEntry, {"text": "", "scale": 0.05, "command": self.set_byo_periods, "initialText": "5", "pos": (1, 0, -0.9), "frameColor": (0, 0, 0, 0.5), "text_fg": (1, 1, 1, 1), "width": 4}),
                ("byo_periods_label", OnscreenText, {"text": "Byo-yomi Periods", "pos": (1.9, -0.9), "scale": 0.07, "align": TextNode.ARight, "font": self.custom_font})
            ]

            # Create all GUI elements and store them in the dictionary
            for name, element_type, kwargs in gui_definitions:
                self.extra_gui_elements[name] = element_type(**kwargs)

            # Additional bindings for DirectEntry elements
            for name in ["color_entry", "background_entry", "main_time_entry", "increment_entry", "byo_time_entry", "byo_periods_entry"]:
                if name in self.extra_gui_elements:
                    self.extra_gui_elements[name].bind(DGG.ENTER, lambda event, n=name: self.extra_gui_elements[n]["command"](self.extra_gui_elements[n].get()))
        else:
            # Destroy all GUI elements and clear the dictionary
            for element in self.extra_gui_elements.values():
                if element is not None:
                    element.destroy()
            self.extra_gui_elements.clear()

        self.extra_show = 1 - self.extra_show  # Toggle between 0 and 1

    def set_komi(self,text):
        try:
            self.komi = float(text)
        except ValueError:
            pass

    def setup_gui(self):#GUI
        if not self.custom_font.isValid():
            self.custom_font = None

        # Get window size and aspect ratio WIP
        #props = self.win.getProperties()
        #win_width = props.getXSize()
        #win_height = props.getYSize()
        #aspect_ratio = win_width / win_height if win_height > 0 else 1.0
        #self.aspect_scale = 1.0 / aspect_ratio  # Adjust positions for narrower screen

        # Display turn and instructions
        self.turn_text = OnscreenText(
            text=f"Turn: {self.turn}",
            pos=(-1.9, 0.7),
            scale=0.07,
            align=TextNode.ALeft,
            mayChange=True)
        
        self.text_points = OnscreenText(
            text=f"Black points: {self.black_points}\nWhite points: {self.white_points}",
            pos=(1.9, 0.90),
            scale=0.07,
            align=TextNode.ARight,
            font= self.custom_font,
            mayChange=True)
        
        self.text_captures = OnscreenText(
            text=f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}",
            pos=(1.9, 0.7),
            scale=0.07,
            align=TextNode.ARight,
            font= self.custom_font,
            mayChange=True)
        
        self.help = OnscreenText(
            text="Press X for help",
            pos=(-1.9, 0.80),
            scale=0.07,
            align=TextNode.ALeft,
            font= self.custom_font)
        
        self.save_game_gui = DirectButton(text=("Save game", "Saved", "Click to save", "disabled"), pos = (1.78,0,0.08),
                 scale=.05, command=self.save_game)
        self.load_game_gui = DirectButton(text=("Load game", "Loaded", "Click to load game", "disabled"), pos = (1.78,0,0),
                 scale=.05, command=self.load_game)


        self.extra = OnscreenText(text="Press C for timer and extra settings",
            pos=(-1.9, 0.90),
            scale=0.07,
            align=TextNode.ALeft,
            font= self.custom_font)
        
        self.coord_label = OnscreenText(  
            text="Blue ball = (0,0,0)",
            pos=(0, 0.9),
            scale=0.06,
            align=TextNode.ACenter,
            font= self.custom_font)

    ##### Instructions for coordinate input #####
        self.coord_label = OnscreenText(
            text="Enter x,y,z",
            pos=(-0.2,-0.90),
            scale=0.07,
            align=TextNode.ACenter,
            font= self.custom_font
        )
        self.coord_entry = DirectEntry( # Create entry field for coordinate input
            text="",
            scale=0.05,
            command=self.process_coordinates,
            initialText="",
            numLines=1, 
            focus=0,
            pos=(0, 0, -0.9),
            frameColor=(0, 0, 0, 0.5),
            text_fg=(1, 1, 1, 1), width=3
        )
        self.coord_entry.bind(DGG.ENTER, self.process_coordinates)
        # Create button to submit coordinates
       # self.submit_button_move = DirectButton( 
        #text="Submit move",
        #scale=0.05,
       # command=self.process_coordinates,
       # pos=(0.4,0, -0.9),
       ## frameColor=(0, 1, 0, 0.5),
       # text_fg=(1, 1, 1, 1)
       # )
    ##### Instructions for coordinate input #####    

    ##### Instructions for grid size input #####
        self.size_label = OnscreenText(
            text="Enter the grid size", pos=(-1.9, -0.9), scale=0.07, align=TextNode.ALeft,font= self.custom_font
        )

        self.size_entry = DirectEntry( # Create entry field for grid size input
            text="", scale=0.05, command=self.set_grid_size,
            initialText="", numLines=1, focus=0,
            pos=(-1.24, 0, -0.9), frameColor=(0, 0, 0, 0.5),
            text_fg=(1, 1, 1, 1), width=7
        )
        
    ##### Instructions for grid size input #####
        self.timer_text = OnscreenText(text="Black: 0:00\nWhite: 0:00", pos=(-1.9, 0.6), scale=0.07, align=TextNode.ALeft, font=self.custom_font)
        self.timer_settings_frame = None
        

    def set_timer_mode(self, mode):
        self.timer_mode = mode
        self.reset_timers()

    def set_main_time(self, text):
        try:
            self.main_time = int(text)
            self.reset_timers()
        except ValueError:
            pass

    def set_increment(self, text):
        try:
            self.increment = int(text)
        except ValueError:
            pass

    def set_byo_time(self, text):
        try:
            self.byo_time = int(text)
            self.reset_timers()
        except ValueError:
            pass

    def set_byo_periods(self, text):
        try:
            self.byo_periods = int(text)
            self.reset_timers()
        except ValueError:
            pass

    def reset_timers(self):
        if(self.timer_mode!="No timer"):
            self.black_time = self.main_time
            self.white_time = self.main_time
            self.black_byo_periods_left = self.byo_periods
            self.white_byo_periods_left = self.byo_periods
            self.timer_running = False
            self.active_timer = None
            self.update_timer_display()
        else:
            return

    def start_timer(self):
        if self.timer_task:
            self.taskMgr.remove(self.timer_task)
        self.timer_running = True
        self.timer_task = self.taskMgr.add(self.update_timer, "update_timer")

    def pause_timer(self):
        if self.timer_task:
            self.taskMgr.remove(self.timer_task)
        self.timer_running = False

    


    def get_board_hash(self):
        """Create a hash of the current board state for ko detection."""
        # Sort positions to ensure consistent hashing
        board_state = sorted((pos, self.balls[pos]['color']) for pos in self.balls)
        return hashlib.md5(str(board_state).encode()).hexdigest()


    def update_timer(self, task):
        if not self.timer_running or self.game_ended:
            return task.cont

        dt = globalClock.getDt()  # Time since last frame (in seconds)
        current_time = self.black_time if self.current_color == 0 else self.white_time
        current_byo_yomi_time = self.black_byo_yomi_time if self.current_color == 0 else self.white_byo_yomi_time
        current_byo_yomi_periods = self.black_byo_yomi_periods if self.current_color == 0 else self.white_byo_yomi_periods

        # Update main time or byo-yomi
        if current_time > 0:
            current_time -= dt
            if current_time < 0:
                current_time = 0
         
        else:
            current_byo_yomi_time -= dt
            if current_byo_yomi_time <= 0:
                current_byo_yomi_periods -= 1
        
                if current_byo_yomi_periods <= 0:
                    self.handle_timeout()
                    return task.done
                current_byo_yomi_time = self.byo_time  # Reset byo-yomi time for the next period

        # Update timer state
        if self.current_color == 0:
            self.black_time = current_time
            self.black_byo_yomi_time = current_byo_yomi_time
            self.black_byo_yomi_periods = current_byo_yomi_periods
        else:
            self.white_time = current_time
            self.white_byo_yomi_time = current_byo_yomi_time
            self.white_byo_yomi_periods = current_byo_yomi_periods

        # Update UI
        black_display = self.format_time(self.black_time, self.black_byo_yomi_time, self.black_byo_yomi_periods)
        white_display = self.format_time(self.white_time, self.white_byo_yomi_time, self.white_byo_yomi_periods)
        self.timer_text.setText(f"Black: {black_display}\nWhite: {white_display}")

        return task.cont
    
    def format_time(self, main_time, byo_yomi_time, byo_yomi_periods):
        # Display main time if available, otherwise show byo-yomi time
        if main_time > 0:
            minutes = int(main_time // 60)
            seconds = int(main_time % 60)
            return f"{minutes}:{seconds:02d}"
        else:
            seconds = int(byo_yomi_time)
            return f"{seconds} ({byo_yomi_periods})"

    def handle_timeout(self):
        winner = "Black" if self.current_color == 1 else "White"
        self.game_ended = True
        self.text_timer.setText(f"{winner} wins by timeout!")
        self.game_over_text = OnscreenText(
            text=f"Game Over! {winner} wins by timeout!",
            pos=(0, 0), scale=0.1, fg=(0.25, 1, 0, 1), align=TextNode.ACenter
        )


    def update_timer_display(self):
        if (self.timer_mode == "No timer"):
            self.timer_text.setText(f"Black:NT\nWhite:NT")
            return
        black_mins, black_secs = divmod(int(self.black_time), 60)
        white_mins, white_secs = divmod(int(self.white_time), 60)
        black_extra = f" ({self.black_byo_periods_left} periods)" if self.timer_mode == "Byo-yomi" else ""
        white_extra = f" ({self.white_byo_periods_left} periods)" if self.timer_mode == "Byo-yomi" else ""
        self.timer_text.setText(f"Black: {black_mins}:{black_secs:02d}{black_extra}\nWhite: {white_mins}:{white_secs:02d}{white_extra}")
        

    def process_coordinates(self, input_text=None):
        # If player chooses to use text move input.
        if input_text is not None and not isinstance(input_text, str):
            text = self.coord_entry.get()  # Fallback to entry field text
        else:
            text = self.coord_entry.get() if input_text is None else input_text

        try:
            coords = [int(x.strip()) for x in text.split(',')]
            if len(coords) != 3:
                return
            x, y, z = coords

            if not (0 <= x < self.x_size and 0 <= y < self.y_size and 0 <= z < self.z_size):
                return

            pos = (x, y, z)
            if pos in self.balls:
                return

            self.spawn_model(pos)
            self.coord_entry["focus"] = 0  # Clear focus after submission
        except ValueError:
            return
        except Exception as e:
            return

    def get_group(self, pos, color, visited=None, balls=None):
        if balls is None:
            balls = self.balls
        if visited is None:
            visited = set()
        if pos not in balls or balls[pos]['color'] != color or pos in visited:
            return set()
        
        group = set()
        to_check = [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current not in balls or balls[current]['color'] != color:
                continue
            visited.add(current)
            group.add(current)

            to_check.extend(self.get_adjacent_positions(current))
 
        return group


    def check_click(self):
        
        # Check if mouse is available
        if not self.mouseWatcherNode.hasMouse():
            return

        # Get mouse position
        mpos = self.mouseWatcherNode.getMouse()

        # Set up ray from camera lens
        self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
        size = [int(x.strip()) for x in self.size.split(',')]
        if len(size)!=3:
            return
        x,y,z = size
        # Traverse the scene for collisions
        self.cTrav.traverse(self.render)

        if self.pickerQueue.getNumEntries() > 0:
            self.pickerQueue.sortEntries()
            hit = self.pickerQueue.getEntry(0)
            vertex_node = hit.getIntoNodePath().getParent()
            pos = vertex_node.getPos(self.render)
            pos_tuple = (int(round(pos.x)), int(round(pos.y)), int(round(pos.z)))


            # Validate position within grid bounds
            if not (0 <= pos_tuple[0] < x and 0 <= pos_tuple[1] < y and 0 <= pos_tuple[2] < z):
                return

            # Check if position is already occupied
            if pos_tuple in self.balls:
                return

            # Spawn the model and update game state
            self.spawn_model(pos_tuple)




    def rewind_turn(self):
        if (not self.match_history):
    
            return
        if (len(self.match_history)==1): #As if we are at the first turn an for some reason we want to rewind, we don't have a previous state so we fabricate one
            self.match_history.pop()
            for pos in list(self.balls.keys()):
                self.balls[pos]['node'].removeNode()
            self.balls.clear()
            self.turn=1
            self.turn_text.setText(f"Turn: {self.turn}")
            self.current_color=0
            return 
        else:#Remove the last state (current state before rewind)
            self.match_history.pop() #destroy the last turn
            prev_state = self.match_history[-1] #as the last turn was deleted, choose the right now last turn becauses that's the one before the last turn before rewinding
        # Clear current balls from the scene
            for pos in list(self.balls.keys()):
                self.balls[pos]['node'].removeNode()
            self.balls.clear()

        # Restore previous balls
        for pos, ball_data in prev_state['balls'].items():
            model = self.ball_model.copyTo(self.render)
            texture = self.black_texture if ball_data['color'] == 0 else self.white_texture
            model.setTexture(texture, 1)
            model.setScale(0.49)
            model.setPos(pos[0], pos[1], pos[2])
            model.reparentTo(self.render)
            model.setMaterial(self.myMaterial)
            self.balls[pos] = {'node': model, 'color': ball_data['color']}

            # Restore other game state
        self.current_color = prev_state['current_color']
        self.turn = prev_state['turn']
        self.black_captures = prev_state['black_captures']
        self.white_captures = prev_state['white_captures']

        # Update UI
        self.turn_text.setText(f"Turn: {self.turn}")
        self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")
        self.text_points.setText(f"Black points: {self.black_points}\nWhite points: {self.white_points}")
        

    def spawn_model(self, pos):
        if self.game_ended:
            return

        pos_tuple = tuple(int(round(coord)) for coord in pos)
        if not self.is_legal_move(pos_tuple, self.current_color):
            return

        model = self.ball_model.copyTo(self.render)
        texture = self.black_texture if self.current_color == 0 else self.white_texture
        model.setTexture(texture, 1)
        model.setScale(0.49)
        model.setPos(pos[0], pos[1], pos[2])
        model.reparentTo(self.render)
        model.setMaterial(self.myMaterial)
        self.balls[pos_tuple] = {'node': model, 'color': self.current_color}

        # Apply increment if applicable
        if self.increment > 0:
            if self.current_color == 0:
                self.black_time += self.increment
            else:
                self.white_time += self.increment

        self.current_color = (self.current_color + 1) % 2
        self.turn += 1
        self.pass_count = 0  # Reset pass count on a move

        board_hash = self.get_board_hash()
        state = {
            'balls': {k: {'color': v['color']} for k, v in self.balls.items()},
            'current_color': self.current_color,
            'turn': self.turn,
            'black_captures': self.black_captures,
            'white_captures': self.white_captures,
            'board_hash': board_hash
        }
        self.match_history.append(state)
        
        # Safety check for any additional captures (e.g., edge cases)
        self.check_all_groups_for_captures()

        self.turn_text.setText(f"Turn: {self.turn}")
        if self.timer_mode != "No Timer":
            self.pause_timer()  # Pause current player's timer
            self.start_timer()  # Start next player's timer
        elif self.timer_mode == "Byo-yomi":
            if self.current_color == 0:  # White just moved, reset Black's byo-yomi
                self.black_byo_yomi_time = self.byo_time
                self.black_byo_yomi_periods = self.byo_periods
            else:  # Black just moved, reset White's byo-yomi
                self.white_byo_yomi_time = self.byo_time
                self.white_byo_yomi_periods = self.byo_periods

    def check_all_groups_for_captures(self):
        visited = set()
        captured_groups = []
        for pos in list(self.balls.keys()):
            if pos not in visited:
                color = self.balls[pos]['color']
                group = self.get_group(pos, color, visited.copy())
                has_lib = self.group_has_liberty(group)
                if group and not has_lib:  # Ensure group is not empty and has no liberties
                    captured_groups.append((group, color))
                visited.update(group)
        
        # Remove captured groups and update capture counts
        for group, color in captured_groups:
            self.remove_group(group, color)

        # Update UI to reflect the latest capture counts
        self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")

    def get_adjacent_positions(self, pos): #Return a list of adjacent positions within grid bounds
        size = [int(x.strip()) for x in self.size.split(',')]
        x_size,y_size,z_size = size
        x, y, z = pos
        adj = [
            (x + 1, y, z), (x - 1, y, z),
            (x, y + 1, z), (x, y - 1, z),
            (x, y, z + 1), (x, y, z - 1)
        ]
        return [(ax, ay, az) for ax, ay, az in adj if 0 <= ax < x_size and 0 <= ay < y_size and 0 <= az < z_size]

    def is_legal_move(self, pos, color):
        pos_tuple = tuple(int(round(coord)) for coord in pos)
        
        if pos_tuple in self.balls:
            return False

        # Simulate the move
        temp_balls = {k: v.copy() for k, v in self.balls.items()}
        temp_balls[pos_tuple] = {'color': color}
        
        # Simulate captures
        opponent_color = 1 - color
        captured_positions = set()
        visited = set()
        for adj_pos in self.get_adjacent_positions(pos_tuple):
            if (adj_pos in temp_balls and temp_balls[adj_pos]['color'] == opponent_color and 
                adj_pos not in visited):
                group = self.get_group(adj_pos, opponent_color, visited.copy(), temp_balls)
                has_lib = self.group_has_liberty(group, temp_balls)
                if group and not has_lib:
                    captured_positions.update(group)
                visited.update(group)

        # Update capture counts and remove stones from actual state
        if captured_positions:
            for captured_pos in captured_positions:
                if captured_pos in self.balls:
                    # Remove the stone from the actual board
                    self.balls[captured_pos]['node'].removeNode()
                    del self.balls[captured_pos]
            # Update capture counts based on opponent color
            if opponent_color == 0:  # Black stones captured by White
                self.white_captures += len(captured_positions)
            else:  # White stones captured by Black
                self.black_captures += len(captured_positions)
            self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")

        # Update temp_balls after removing captured stones
        for captured_pos in captured_positions:
            if captured_pos in temp_balls:
                del temp_balls[captured_pos]

        # Check for suicide
        player_color = color
        visited = set()
        player_groups = []
        for ball_pos in temp_balls:
            if (ball_pos not in visited and temp_balls[ball_pos]['color'] == player_color):
                group = self.get_group(ball_pos, player_color, visited.copy(), temp_balls)
                player_groups.append(group)
                visited.update(group)

        for group in player_groups:
            has_lib = self.group_has_liberty(group, temp_balls)
            if not has_lib:
                return False

        # Ko rule check
        # Temporarily add the new stone to self.balls for ko check
        self.balls[pos_tuple] = {'color': color}  # Temporarily add for hash
        board_hash = self.get_board_hash()
        del self.balls[pos_tuple]  # Remove it after hash
        if len(self.match_history) >= 2:
            prev_board_hash = self.match_history[-2].get('board_hash')
            if prev_board_hash == board_hash:
                # Revert captures if ko violation
                for captured_pos in captured_positions:
                    if captured_pos not in self.balls:
                        model = self.ball_model.copyTo(self.render)
                        texture = self.black_texture if opponent_color == 0 else self.white_texture
                        model.setTexture(texture, 1)
                        model.setScale(0.49)
                        model.setPos(*captured_pos)
                        model.reparentTo(self.render)
                        self.balls[captured_pos] = {'node': model, 'color': opponent_color}
                # Revert capture counts
                if opponent_color == 0:
                    self.white_captures -= len(captured_positions)
                else:
                    self.black_captures -= len(captured_positions)
                self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")
                return False

        return True




    def group_has_liberty(self, group, balls=None):
        if balls is None:
            balls = self.balls
        if not group:
            return False
        liberties = []
        for pos in group:
            adj_positions = self.get_adjacent_positions(pos)
            for adj in adj_positions:
                if adj not in balls and adj not in group:
                    liberties.append(adj)
        
        has_lib = bool(liberties)
        return has_lib

    def remove_group(self, group, color):
        removed_count = 0
        for pos in group:
            if pos in self.balls:
                node = self.balls[pos]['node']
                node.removeNode()  # Remove the visual node
                del self.balls[pos]  # Remove from self.balls
                removed_count += 1
            else:
                continue
        
        # Update capture counts based on the color of the group being removed
        if color == 0:  # Black stones were removed, so White captures them
            self.white_captures += removed_count
        else:  # White stones were removed, so Black captures them
            self.black_captures += removed_count
  
    def reset_camera(self, size):
        x, y, z = [int(x.strip()) for x in size.split(',')]
        center = Point3((x - 1) / 2, (y - 1) / 2, (z - 1) / 2)
        self.camera_control.center = center
        self.camera_control.update_camera_position()
        self.camera.lookAt(center)

    def change_camera_center(self):#Change the camera center to the clicked collision sphere.
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
            self.cTrav.traverse(self.render)
            if self.pickerQueue.getNumEntries() > 0:
                self.pickerQueue.sortEntries()
                hit = self.pickerQueue.getEntry(0)
                vertex_node = hit.getIntoNodePath().getParent()
                pos = vertex_node.getPos(self.render)
                self.camera_control.center = pos
                self.camera_control.update_camera_position()

    def show_nothing(self): #Idk why I've created this function but I'm not gonna deleted. 
        for node in self.nodes:
            node.setScale(0.0)
        for ball_data in self.balls.values():
            ball_data['node'].setScale(0.0)
        for line_node in self.line_nodes:
            line_node.hide()

    def show_everything(self):
        if (self.x_size == 1 or self.y_size == 1 or self.z_size == 1):
            return
        for node in self.nodes:
            node.setScale(1.0)
        for ball_data in self.balls.values():
            ball_data['node'].setScale(0.49)
        for line_node in self.line_nodes:
            line_node.show()
        
        if(self.last_plane_action==1): #If we pressed E, then it goes back to the one down, so the next time show's the same, so a player can go to the whole grid and back
            self.current_plane = (self.current_plane - 1) % self.z_size
        elif(self.last_plane_action==0): #Same as up comment but down
            self.current_plane = (self.current_plane + 1) % self.z_size 
        elif(self.last_plane_action==None): #If a player tries to show everything but it's already showing everything and such player has never used Q or E, we do nothing
            return

    def plane_up(self):
        if (self.last_plane_action==0): # When the player for some reason goes e,w,q,w,e,w,q like showing one plane then everything and such but it does it by alternating the keys
            self.show_one_floor(0, current_z=self.current_plane) # It shows badly but with this we ensure we show the last plane properly and the next time it's pressed, twice that its it shows
            # in this case the upper one or the lower one in the other case.
            self.last_plane_action=1
        self.show_one_floor(1, self.current_plane)
       # Camera.update_camera_plane_position(self,self.current_plane) WIP Iwant that when the player chosees to see a plane, the camera re centers.
        self.last_plane_action=1
        
    def plane_down(self):
        if (self.last_plane_action==1):
            self.show_one_floor(1, current_z=self.current_plane)
            self.show_one_floor(1, current_z=self.current_plane)
            self.last_plane_action=0
        self.show_one_floor(0, self.current_plane)
        #Camera.update_camera_plane_position(self,self.current_plane)
        self.last_plane_action=0

    def cut_layer(self):
            if (self.x_size < 3 or self.y_size <= 3 or self.z_size <= 3): #It's a non sense to cut layer if you are playing on a plane or a 2 wide geometry.
                return;
            biggestaxis = max(self.x_size,self.y_size,self.z_size) # Choose the biggest axis to be the control one
            if (self.layer_count<(biggestaxis/2)-1): # because the position start at 0, we have to shift -1 to every position.
                for i in range(0,self.layer_count+1): #As layer_count can't be greater than half-1 the size we set a for that goes from 0 the start position to layer_count +1 so it includes it
                    for node in self.nodes: # For nodes, if they satisfied the condition then set their scale to 0 so you can't click
                        name_parts = node.getName().split('_')
                        if len(name_parts) > 1:
                            coords = name_parts[1].split(',')
                            x, y, z = [int(coord) for coord in coords]
                            if (x <= i or y <= i or z <= i or x >= self.x_size-1-i or y >= self.y_size-1-i or z >= self.z_size-1-i): #If any coordinate it's the value we want to cut, cut it.
                                node.setScale(0.2)

                    for pos, ball_data in list(self.balls.items()): # Same on nodes for balls, set balls.scale to cero so you don't see them
                        x, y, z = pos
                        if (x <= i or y <= i or z <= i or x >= self.x_size-1-i or y >= self.y_size-1-i or z >= self.z_size-1-i):
                            ball_data['node'].setScale(0.2)
                self.layer_count+=1
            else:
                self.layer_count=0
                self.show_everything()
        
    def show_one_floor(self, Up_or_down, current_z):
        if Up_or_down == 0:
            if not(current_z is None):
                if not hasattr(self, 'current_plane'):
                    self.current_plane = 0
                else:
                    self.current_plane = (self.current_plane - 1) % self.z_size
                z = self.current_plane
            else:
                z = current_z
                if not (0 <= z < self.z_size):
                    return
        else:
            if not(current_z is None):
                if not hasattr(self, 'current_plane'):
                    self.current_plane = 0
                else:
                    self.current_plane = (self.current_plane + 1) % self.z_size
                z = self.current_plane
                
            else:
                z = current_z
                if not (0 <= z < self.z_size):
                    return

        for node in self.nodes:
            name_parts = node.getName().split('_')
            if len(name_parts) > 1:
                coords = name_parts[1].split(',')
                x, y, z_pos = [float(coord) for coord in coords]
                if int(z_pos) == z:
                    node.setScale(1)
                else:
                    node.setScale(0)

        for pos, ball_data in list(self.balls.items()):
            x, y, z_pos = pos
            if z_pos == z:
                ball_data['node'].setScale(0.49)
            else:
                ball_data['node'].setScale(0)

        # Show only the line grid for the current z-level
        for i, line_node in enumerate(self.line_nodes):
            if i == z:
                line_node.show()
            else:
                line_node.hide()     
app = GridDemo(0)  # Set the size of the board
app.run()

