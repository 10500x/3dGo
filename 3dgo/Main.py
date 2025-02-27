from panda3d.core import NodePath, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue, CollisionRay, TextNode
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectEntry, DirectButton, DGG
from camera import Camera
from panda3d.core import loadPrcFile
loadPrcFile("config\conf.prc")
class GridDemo(ShowBase):
    def __init__(self, size):
        ShowBase.__init__(self)
        self.size = size # Store grid size
        self.setBackgroundColor(0.0,0.75,0.75)
        #Collision system this shit it's right from the panda3d documentation, no idea how it works, it just does
        self.cTrav = CollisionTraverser()
        self.pickerQueue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode("mouseRay")
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)  # Attached to camera
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.pickerNode.setFromCollideMask(1)
        self.cTrav.addCollider(self.pickerNP, self.pickerQueue)
        #Collision system
        
        self.disableMouse() #Disable camera default movement
        self.camera_control = Camera(self, size) #Call Camera from camera.py for camera movement 
        #Binds
        self.accept("space", self.camera_control.start_rotation)  # set space for camera rotation
        self.accept("space-up", self.camera_control.stop_rotation)# set space-up, that is when space it's not pressed to the stop rotate funtion
        self.accept("wheel_up", self.camera_control.zoom_in)      # set the mouse wheel to zoom in and out.
        self.accept("wheel_down", self.camera_control.zoom_out)   #
        self.accept("mouse1", self.check_click)          #set mouse1, left click to the funtion check_click (the one that spawns a ball)
        self.accept("mouse3", self.change_camera_center) #set mouse3, right click to the funtion that changes the center when click on a collision sphere
        self.accept("r", self.center_center)             #set r to the funtion that reset the camera to the center
        self.accept("arrow_left", self.camera_control.rotate_left) # Bind arrow keys for movement, fixed angle.
        self.accept("arrow_right", self.camera_control.rotate_right)
        self.accept("arrow_up", self.camera_control.rotate_up)
        self.accept("arrow_down", self.camera_control.rotate_down)
    

        ########### WIP
        #self.accept("w",self.show_one_horizontal_plane) 
        #self.accept("s") 
        #self.accept("a") 
        #self.accept("d") 
        #self.accept("t") #
        # Binds

    
        #self.Vertex = []
        self.Edges = []
        self.balls = {}  # Dictionary to track balls: (x, y, z) -> {'node': NodePath, 'color': int}
        self.current_model_index = 0  # 0 = black, 1 = white
        self.turn= 1 #set the turn counter to 1.
        

        # (0,0,0) is represented by using a black ball
        model000 = self.loader.loadModel("smiley")
        model000.setPos(0,0,0)
        model000.setTexture(self.loader.loadTexture("textures/black.png"), 1)
        model000.reparentTo(self.render)
        model000.setScale(0.11)
        #(0,0,0)

    #######Grid generation
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    vertex_node = NodePath(f"vertex_{x}_{y}_{z}")
                    vertex_node.setPos(x, y, z)
                    vertex_node.reparentTo(self.render)
                    #cs= CollisionBox(0, 0.1, 0.1,0.1) #Uses boxes instead of spheres, it's just worst for performance, sad.
                    cs = CollisionSphere(0, 0, 0, 0.1)
                    cnodePath = vertex_node.attachNewNode(CollisionNode(f'cnode_{x}_{y}_{z}'))
                    cnodePath.node().addSolid(cs)
                    cnodePath.node().setIntoCollideMask(1)
                    cnodePath.setColor(0.5, 0.5, 0.5, 1)
                    cnodePath.show()
                    if x + 1 < size:
                        self.Edges.append(((x, y, z), (x + 1, y, z)))
                    if y + 1 < size:
                        self.Edges.append(((x, y, z), (x, y + 1, z)))
                    if z + 1 < size:
                        self.Edges.append(((x, y, z), (x, y, z + 1)))



    ##############GUI
        self.setup_gui()
        self.textObject = OnscreenText(text="Turn:  "+str(self.turn)+"", pos=(-1, 0.90), scale=0.07)#First turn text
        self.textObject2 = OnscreenText(text="Press space and move the mouse to rotate", pos=(0, 0.90), scale=0.07)
        self.textObject2 = OnscreenText(text="Left click to play\nRight click to change the center\nR to reset camera", pos=(-0.95, 0.8), scale=0.07)
    def setup_gui(self):
        """Set up GUI elements for coordinate input."""
        # Create a text label for instructions
        self.textObject3 = OnscreenText(text="Enter x,y,z", pos=(-0.99, -0.90, 0), scale=0.07)
        # Bind a click event to set focus on the entry
        
        # Create an entry field for coordinate input
        self.coord_entry = DirectEntry(
            text="" , 
            scale=.05,
            command=self.process_coordinates,
            initialText="",
            numLines=1,
            focus=0,
            pos=(-0.8, 0, -0.9),  # Position below the turn text
            frameColor=(0, 0, 0, 0.5),  # Semi-transparent black frame
            text_fg=(1, 1, 1, 1),  # White text
            width=10
        )
        self.coord_entry.bind(DGG.ENTER, self.process_coordinates)

        # Create a button to submit coordinates
        self.submit_button = DirectButton(
            text="Submit Move",
            scale=0.05,
            command=self.process_coordinates,
            pos=(-0, 0, -0.9),  # Position next to the entry field
            frameColor=(0, 1, 0, 0.5),  # Semi-transparent green frame
            text_fg=(1, 1, 1, 1)  # White text
        )
    
    def process_coordinates(self, input_text=None):
        """Process the coordinates entered by the player and make a move."""
        text = self.coord_entry.get() if input_text is None else input_text
        try:
            # Parse the input (e.g., "0,0,0" into x, y, z)
            coords = [int(x.strip()) for x in text.split(',')]
            if len(coords) != 3:
                print("Invalid input: Please enter three numbers separated by commas (e.g., 0,0,0)")
                return
            x, y, z = coords

            # Validate coordinates are within grid bounds
            if not (0 <= x < self.size and 0 <= y < self.size and 0 <= z < self.size):
                print(f"Coordinates {x},{y},{z} are outside the grid bounds ({self.size}x{self.size}x{self.size})")
                return

            pos_tuple = (x, y, z)

            # Check if position is already occupied
            if pos_tuple in self.balls:
                print(f"Position {pos_tuple} already occupied")
                return

            # Allow the move and spawn the piece
            self.spawn_model(pos_tuple)
            self.turn += 1  # Increment turn
            print(f"Turn incremented to: {self.turn}")

            # Update the turn text
            self.turn_text.setText(f"Turn: {self.turn}\nPress space and move the mouse to rotate\nLeft click to play\nRight click to change the center\nR to reset camera")

            # Clear focus after submission
            self.coord_entry["focus"] = 0
            print("Entry field focus cleared after submission")

        except ValueError:
            print("Invalid input: Please enter numeric coordinates (e.g., 0,0,0)")
        except Exception as e:
            print(f"Error processing coordinates: {e}")


    def show_one_horizontal_plane(self): #wip
        print(self.balls)
        for x in range (0,self.size):
            for y in range (0,self.size):
                vertex_node = NodePath(f"vertex_{x}_{y}_{0}")
                cnodePath = vertex_node.attachNewNode(CollisionNode(f'cnode_{x}_{y}_{0}'))
                cnodePath.show(False)
                
    #def show_one_vertcal_plane(): #wip
    #    asd
    #def show_every_plane():
    #    asd
    
    #Funtion that when click on a collision sphere checks for its liberties, by calling the funtion get_adjacent_positions
    def has_liberty(self, pos):
        """Check if the position has at least one empty adjacent spot."""
        adj_positions = self.get_adjacent_positions(pos)
        for adj_pos in adj_positions:
            if adj_pos not in self.balls:
                return True
        return False
    #Funtion that when click on a collision sphere checks for it's adjacent positons
    def get_adjacent_positions(self, pos):
        """Return list of adjacent positions."""
        x, y, z = pos
        adj = [
            (x + 1, y, z), (x - 1, y, z),
            (x, y + 1, z), (x, y - 1, z),
            (x, y, z + 1), (x, y, z - 1)
        ]
        return [(ax, ay, az) for ax, ay, az in adj if 0 <= ax < self.size and 0 <= ay < self.size and 0 <= az < self.size]

    def get_group(self, pos, color, visited=None):
        """Find all connected balls of the same color using DFS, tracking visited positions."""
        if visited is None:
            visited = set()
        
        if pos not in self.balls or self.balls[pos]['color'] != color or pos in visited:
            return set()
        
        group = set()
        to_check = [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current not in self.balls or self.balls[current]['color'] != color:
                continue
            visited.add(current)
            group.add(current)
            for adj_pos in self.get_adjacent_positions(current):
                if adj_pos not in visited and adj_pos in self.balls and self.balls[adj_pos]['color'] == color:
                    to_check.append(adj_pos)
        #print(f"Group for {pos} (color {color}): {group}") #debug
        return group

    def group_has_liberty(self, group):
        """Check if a group of balls has at least one liberty (empty adjacent position)."""
        visited = set()
        for pos in group:
            if pos in visited:
                continue
            for adj_pos in self.get_adjacent_positions(pos):
                #print(f"Checking liberty for {pos}: adjacent position {adj_pos}")#debug
                if adj_pos not in self.balls:  # Only count empty positions as liberties
                    #print(f"Group {group} has liberty at {adj_pos}")#debug
                    return True #Found a liberty.
                # Ensure we don’t count positions within the group as liberties
                if adj_pos in group:
                    #print(f"Skipping {adj_pos} as it’s part of the group")#debug
                    continue #No liberty, keep searching
            visited.add(pos)
        #print(f"Group {group} has no liberties")#debug
        return False

    def remove_group(self, group):
        """Despawn all balls in the group."""
        for pos in group:
            if pos in self.balls:
                self.balls[pos]['node'].removeNode()
                del self.balls[pos]
                #print(f"Despawned ball at {pos}") #degub

    #Funtion that positions the camera to the center of the grid (the default position) by using Camera.py after pressing R
    def center_center(self):
        self.camera_control.center = ((self.size - 1) / 2, (self.size - 1) / 2, (self.size - 1) / 2)
        self.camera_control.update_camera_position()

    #Funtion that changes the camera center. by using Camera.py
    def change_camera_center(self):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())

            self.cTrav.traverse(self.render)
            if self.pickerQueue.getNumEntries() > 0:
                self.pickerQueue.sortEntries()
                hit = self.pickerQueue.getEntry(0)
                vertex_node = hit.getIntoNodePath().getParent()
                pos = vertex_node.getPos(self.render)
                # Update the camera center to the clicked position, by giving camera_control.center the positon of the node we just right clicked.
                self.camera_control.center = pos
                # Update the camera position to maintain the current radius, theta, and phi around the new center
                self.camera_control.update_camera_position()
        
    def check_click(self):
        if not self.mouseWatcherNode.hasMouse():
            return

        mpos = self.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())

        self.cTrav.traverse(self.render)
        if self.pickerQueue.getNumEntries() > 0:
            self.pickerQueue.sortEntries()
            hit = self.pickerQueue.getEntry(0)
            vertex_node = hit.getIntoNodePath().getParent()
            pos = vertex_node.getPos(self.render)
            pos_tuple = (int(round(pos.x)), int(round(pos.y)), int(round(pos.z)))

            #print(f"Clicked position (raw): {pos}")            #Debug
            #print(f"Clicked position (rounded): {pos_tuple}")  #Debug

            # Check if position is within grid bounds (basic validation)
            if not (0 <= pos_tuple[0] < self.size and 0 <= pos_tuple[1] < self.size and 0 <= pos_tuple[2] < self.size):
                print(f"Position {pos_tuple} is outside the grid bounds ({self.size}x{self.size}x{self.size})")
                return

            # Check if position is already occupied
            if pos_tuple in self.balls:
                print(f"Position {pos_tuple} already occupied")
                return
            #If the collisionsphere has no ball and, has at least one liberty, spawns a ball and passes the turn.
            self.spawn_model(pos_tuple) # Spawn the ball
            self.textObject.destroy() #Destroy the first turn text
            self.turn+=1 #add 1 to the turn counter as if the ball spawns means a turn has passed
            self.textObject=OnscreenText(text="Turn:  "+str(self.turn)+"", pos=(-1, 0.90), scale=0.07) #creates the turn number text after the turn has played
     
    def spawn_model(self, pos):
        model = self.loader.loadModel("models\sphere.bam")
        texture_file = "textures/black.png" if self.current_model_index == 0 else "textures/white.png"
        model.setTexture(self.loader.loadTexture(texture_file), 1)
        model.setScale(0.5)
        model.setPos(pos[0], pos[1], pos[2])
        model.reparentTo(self.render)

        # Store the ball
        pos_tuple = (int(round(pos[0])), int(round(pos[1])), int(round(pos[2])))
        self.balls[pos_tuple] = {'node': model, 'color': self.current_model_index}
        #print(f"Spawned {'black' if self.current_model_index == 0 else 'white'} ball at {pos_tuple}")debug

        # Switch color
        self.current_model_index = (self.current_model_index + 1) % 2

        # Check all groups for liberties and capture any without liberties
        self.check_all_groups_for_captures()

    def check_all_groups_for_captures(self):
        """Check all groups on the board for liberties and capture any without liberties."""
        #print("Checking all groups for captures...")debug
        visited = set()
        positions = list(self.balls.keys())
        
        for pos in positions:
            if pos in visited:
                continue
            
            color = self.balls[pos]['color']
            group = self.get_group(pos, color, visited.copy())
            if group and not self.group_has_liberty(group):
                #print(f"Capturing group with no liberties: {group}") #debug
                self.remove_group(group)
            visited.update(group)

app = GridDemo(5) #Set the size of the board
app.run()