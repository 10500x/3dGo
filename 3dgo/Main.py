from panda3d.core import NodePath, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue, CollisionRay, TextNode
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectEntry, DirectButton, DGG
from camera import Camera
from panda3d.core import loadPrcFile, Point3
# Load configuration file
loadPrcFile("config/conf.prc")

class GridDemo(ShowBase):
    def __init__(self, size):
        super().__init__()
        self.initial_size = size  # Store the initial size for menu 
        self.size = 1  # Start with a 1x1x1 grid to show only the black ball
        self.setBackgroundColor(0.0, 0.75, 0.75)  # Set turquoise background
        self.ball_model = self.loader.loadModel("smiley")  # Preload model
        self.black_texture = self.loader.loadTexture("textures/black.png") #Preload textures
        self.white_texture = self.loader.loadTexture("textures/white.png")
        # Set up collision system for mouse picking
        self.setup_collision_system()

        # Disable default mouse control and initialize custom camera
        self.disableMouse()
        self.camera_control = Camera(self, self.initial_size)  # Use initial size for camera positioning

        # Bind keyboard and mouse inputs
        self.bind_inputs()

        # Initialize game state
        self.black_points=0 #set both players points to cero, the komi would be added(asked) later
        self.white_points=0
        self.vertices = []  # List of vertex positions (x, y, z)
        self.edges = []     # List of edges connecting vertices
        self.nodes = []     # List to store grid node paths
        self.balls = {}     # Dictionary to track placed balls: (x, y, z) -> {'node': NodePath, 'color': int}
        self.current_color = 0  # 0 = black, 1 = white
        self.turn = 1       # Start with turn 1
        self.current_plane = 0  # Track current plane for horizontal plane visibility

        # Place initial black ball at (0, 0, 0)
        self.place_initial_ball()

        # Set up GUI for coordinate input, turn display, and grid size input
        self.setup_gui()

        # Generate the initial 1x1x1 grid for the menu
        self.generate_grid(1)

    def points(self):#Funtion that counts the points of the player by searching for the empty spaces that are fully sorrunded by a color
        nocolor=[]#set of balls that has no color
        self.black_points=0 #set to cero so it always counts the points at that turn
        self.white_points=0
        for n in self.vertices: #look in every vertex, if the position of such vertex has a ball attached then, do nothing. If such vextex has no ball, then goes into the nocolor set.
            x,y,z = n
            if (n==(x,y,z) and (not((x,y,z) in self.balls))):
                nocolor.append(n)
        # Check each empty vertex to see if it’s surrounded by one color. Ideallly this should be a BFS and not this but it works...
        for pos in nocolor:
                adj_positions = self.get_adjacent_positions(pos)
                adjacent_colors = set()  # Track unique colors around the empty space

                # Get colors of adjacent balls (if any)
                for adj_pos in adj_positions:
                    if adj_pos in self.balls:
                        adjacent_colors.add(self.balls[adj_pos]['color'])

                # If all adjacent positions have balls of the same color, count the point
                if len(adjacent_colors) == 1:  # Only one color surrounds the empty space
                    color = next(iter(adjacent_colors))  # Get the color (0 or 1)
                    if color == 0:  # Black
                        self.black_points += 1
                    else:  # White
                        self.white_points += 1
                # If there are no adjacent balls or mixed colors, no points are awarded for this space
            # Return the points
        self.text_points.setText(f"Black points: {self.black_points}\nWhite points: {self.white_points}")#Change the points on screen.
        #return self.black_points, self.white_points  #

        

    def setup_collision_system(self):
        """Configure the collision system for mouse picking."""
        self.cTrav = CollisionTraverser()  # Collision traverser for raycasting
        self.pickerQueue = CollisionHandlerQueue()  # Queue to store collision results
        self.pickerNode = CollisionNode("mouseRay")  # Node for the ray
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)  # Attach ray to camera
        self.pickerRay = CollisionRay()  # Ray for detecting collisions
        self.pickerNode.addSolid(self.pickerRay)  # Add ray to the node
        self.pickerNode.setFromCollideMask(1)  # Set collision mask to detect only objects with mask 1
        self.cTrav.addCollider(self.pickerNP, self.pickerQueue)  # Add collider to traverser

    def bind_inputs(self):
        """Bind keyboard and mouse inputs for game controls."""
        # Camera controls
        self.accept("space", self.camera_control.start_rotation)
        self.accept("space-up", self.camera_control.stop_rotation)
        self.accept("wheel_up", self.camera_control.zoom_in)
        self.accept("wheel_down", self.camera_control.zoom_out)
        self.accept("arrow_left", self.camera_control.rotate_left)
        self.accept("arrow_right", self.camera_control.rotate_right)
        self.accept("arrow_up", self.camera_control.rotate_up)
        self.accept("arrow_down", self.camera_control.rotate_down)
        self.accept("p", self.points)

        # Game controls
        self.accept("mouse1", self.check_click)  # Left click to place pieces
        self.accept("mouse3", self.change_camera_center)  # Right click to center camera
        self.accept("r", self.reset_camera)  # Reset camera to grid center
        self.accept("w", self.show_one_floor, [None])  # Show next horizontal plane
        self.accept("s", self.show_everything)  # Show all planes

    def place_initial_ball(self): #place a black ball to represent the 0,0,0
        initial_ball = self.loader.loadModel("smiley")
        initial_ball.setPos(0, 0, 0)
        initial_ball.setTexture(self.loader.loadTexture("textures/black.png"), 1)
        initial_ball.setScale(0.11)
        initial_ball.reparentTo(self.render)

    def generate_grid(self, size):
        size = int(size)  # Ensure size is an integer
        self.size = size  # Update grid size

        # Remove all existing balls (nodes and data)
        for ball_data in list(self.balls.values()):  # Use list() to avoid runtime changes
            ball_data['node'].removeNode()
        self.balls.clear()  # Clear the balls dictionary

        # Remove all existing nodes, including their collision nodes
        for node in self.nodes:
            if not node.is_empty():  # Check if node still exists
                # Remove the collision node attached to this vertex node
                collision_node = node.find("**/+CollisionNode")
                if collision_node:
                    collision_node.removeNode()
                node.removeNode()
        
        # Clear lists to ensure no references remain
        self.nodes = []
        self.edges = []
        self.vertices = []

        # Generate new grid
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    # Create vertex node
                    vertex_node = NodePath(f"vertex_{x},{y},{z}")
                    vertex_node.setPos(x, y, z)
                    vertex_node.reparentTo(self.render)

                    # Add collision sphere
                    collision_sphere = CollisionSphere(0, 0, 0, 0.1)  # Small radius for clickable spots
                    collision_node = vertex_node.attachNewNode(CollisionNode(f'cnode_{x}{y}{z}'))
                    collision_node.node().addSolid(collision_sphere)
                    collision_node.node().setIntoCollideMask(1)  # Set collision mask
                    collision_node.show()  # Show collision spheres
                    collision_node.setColor(0.5, 0.5, 0.5, 1)  # Gray color for visibility

                    # Connect to adjacent vertices (edges)
                    if x + 1 < self.size:
                        self.edges.append(((x, y, z), (x + 1, y, z)))
                    if y + 1 < self.size:
                        self.edges.append(((x, y, z), (x, y + 1, z)))
                    if z + 1 < self.size:
                        self.edges.append(((x, y, z), (x, y, z + 1)))

                    # Store vertex and node
                    self.vertices.append((x, y, z))
                    self.nodes.append(vertex_node)

        # Place initial black ball at (0, 0, 0) for the new grid
        self.place_initial_ball()
        self.reset_camera()  # Adjust camera to the new grid center
        #print(self.vertices) #debug

    def set_grid_size(self, input_text=None): #set the grid size to the user input
        text = self.size_entry.get() if input_text is None else str(input_text)
        try:
            new_size = int(text.strip())  # Convert the text to an integer, stripping whitespace
            self.size = new_size
            self.generate_grid(new_size)  # Regenerate grid with new size
            self.turn = 1  # Reset turn for new grid
            self.balls.clear()  # Clear existing balls (already handled in generate_grid, but ensure consistency)
            self.place_initial_ball()  # Place new initial ball
            self.turn_text.setText(f"Turn: {self.turn}\n")
            self.size_entry["focus"] = 0  # Clear focus after submission
            #print(f"Grid size set to {new_size}x{new_size}x{new_size}")
        except ValueError:
            print("Invalid input: Please enter a numeric grid size (e.g., 5)")
        except Exception as e:
            print(f"Error setting grid size: {e}")

    def setup_gui(self):#GUI
        # Display turn and instructions
        self.turn_text = OnscreenText(
            text=f"Turn: {self.turn}\n",
            pos=(-1.9, 0.90), scale=0.07, align=TextNode.ALeft
        )
        self.hotkeys = OnscreenText(
            text="Press space and move the mouse to rotate\nLeft click to play\nRight click to change the center\nR to reset camera\nW to move between planes\nS to see the whole grid\n",
            pos=(-1.9, 0.80), scale=0.07, align=TextNode.ALeft
        )
        self.text_points = OnscreenText(
            text=f"Black points: {self.black_points}\nWhite points: {self.white_points}",
            pos=(-1.9, 0.40), scale=0.07, align=TextNode.ALeft
        )
        # Instructions for coordinate input 
        self.coord_label = OnscreenText(
            text="Enter x,y,z", pos=(-1.9, -0.90), scale=0.07, align=TextNode.ALeft
        )

        # Create entry field for coordinate input
        self.coord_entry = DirectEntry(
            text="", scale=0.05, command=self.process_coordinates,
            initialText="", numLines=1, focus=0,
            pos=(-1.5, 0, -0.9), frameColor=(0, 0, 0, 0.5),
            text_fg=(1, 1, 1, 1), width=6
        )
        self.coord_entry.bind(DGG.ENTER, self.process_coordinates)

        # Create button to submit coordinates
        self.submit_button = DirectButton(
            text="Submit Move", scale=0.05, command=self.process_coordinates,
            pos=(-1, 0, -0.9), frameColor=(0, 1, 0, 0.5), text_fg=(1, 1, 1, 1)
        )

        # Instructions for grid size input
        self.size_label = OnscreenText(
            text="Enter the grid size", pos=(-1.9, -0.80), scale=0.07, align=TextNode.ALeft
        )

        # Create entry field for grid size input
        self.size_entry = DirectEntry(
            text="", scale=0.05, command=self.set_grid_size,
            initialText="", numLines=1, focus=0,
            pos=(-1.3, 0, -0.8), frameColor=(0, 0, 0, 0.5),
            text_fg=(1, 1, 1, 1), width=3
        )
        self.size_entry.bind(DGG.ENTER, self.set_grid_size)

    def process_coordinates(self, input_text=None):
        text = self.coord_entry.get() if input_text is None else input_text
        try:
            coords = [int(x.strip()) for x in text.split(',')]
            if len(coords) != 3:
                #print("Invalid input: Please enter three numbers separated by commas (e.g., 0,0,0)")
                return
            x, y, z = coords

            if not (0 <= x < self.size and 0 <= y < self.size and 0 <= z < self.size):
                #print(f"Coordinates {x},{y},{z} are outside the grid bounds ({self.size}x{self.size}x{self.size})")
                return

            pos = (x, y, z)
            if pos in self.balls:
                #print(f"Position {pos} already occupied")
                return

            self.spawn_model(pos)
            self.turn += 1
            #print(f"Turn incremented to: {self.turn}")
            self.turn_text.setText(f"Turn: {self.turn}")
            self.coord_entry["focus"] = 0  # Clear focus after submission
            print("Entry field focus cleared after submission")

        except ValueError:
            print("Invalid input: Please enter numeric coordinates (e.g., 0,0,0)")
        except Exception as e:
            print(f"Error processing coordinates: {e}")

    def check_click(self):
        if not self.mouseWatcherNode.hasMouse():
            print("No mouse input detected")
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

            if not (0 <= pos_tuple[0] < self.size and 0 <= pos_tuple[1] < self.size and 0 <= pos_tuple[2] < self.size):
                print(f"Position {pos_tuple} is outside the grid bounds ({self.size}x{self.size}x{self.size})")
                return

            if pos_tuple in self.balls:
                print(f"Position {pos_tuple} already occupied")
                return

            self.spawn_model(pos_tuple)
            self.turn += 1
            print(f"Turn incremented to: {self.turn}")
            self.turn_text.setText(f"Turn: {self.turn}")
        else:
            print("No collision detected")

    def spawn_model(self, pos):
        model = self.ball_model.copyTo(self.render)
        texture = self.black_texture if self.current_color == 0 else self.white_texture
        model.setTexture(texture, 1)
        model.setScale(0.5)
        model.setPos(pos[0], pos[1], pos[2])
        model.reparentTo(self.render)

        pos_tuple = tuple(int(round(coord)) for coord in pos)
        self.balls[pos_tuple] = {'node': model, 'color': self.current_color}
        self.current_color = 1 - self.current_color  # Switch between black (0) and white (1)

        self.check_all_groups_for_captures()

    def check_all_groups_for_captures(self):

        visited = set()
        for pos in list(self.balls.keys()):
            if pos not in visited:
                color = self.balls[pos]['color']
                group = self.get_group(pos, color, visited.copy())
                if group and not self.group_has_liberty(group):
                    self.remove_group(group)
                visited.update(group)

    def get_adjacent_positions(self, pos): #Return a list of adjacent positions within grid bounds
        x, y, z = pos
        adj = [
            (x + 1, y, z), (x - 1, y, z),
            (x, y + 1, z), (x, y - 1, z),
            (x, y, z + 1), (x, y, z - 1)
        ]
        return [(ax, ay, az) for ax, ay, az in adj if 0 <= ax < self.size and 0 <= ay < self.size and 0 <= az < self.size]

    def has_liberty(self, pos):#Check if the position has at least one empty adjacent spot.
        return any(adj_pos not in self.balls for adj_pos in self.get_adjacent_positions(pos))

    def get_group(self, pos, color, visited=None):#Find all connected balls of the same color using DFS.
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
            to_check.extend(self.get_adjacent_positions(current))
        return group

    def group_has_liberty(self, group):#Check if a group of balls has at least one liberty (empty adjacent position).
        return any(adj_pos not in self.balls and adj_pos not in group 
                  for pos in group for adj_pos in self.get_adjacent_positions(pos))

    def remove_group(self, group):#Remove all balls in the group from the scene and tracking
        for pos in group:
            if pos in self.balls:
                self.balls[pos]['node'].removeNode()
                del self.balls[pos]
                print(f"Despawned ball at {pos}")

    def reset_camera(self):#Reset the camera to the center of the grid.
        center = Point3((self.size - 1) / 2, (self.size - 1) / 2, (self.size - 1) / 2)
        self.camera_control.center = center
        self.camera_control.update_camera_position()

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

    def show_nothing(self):#Hide all grid nodes and balls.
       
        for node in self.nodes:
            node.setScale(0.0)
        for ball_data in self.balls.values():
            ball_data['node'].setScale(0.0)
        #print("Showing nothing now.")

    def show_everything(self):#Show all grid nodes and balls.
        if (self.size==1):
            return
        
        for node in self.nodes:
            node.setScale(1.0)
        for ball_data in self.balls.values():
            ball_data['node'].setScale(0.5)
        #print("Showing everything now.")
        self.current_plane-=1 #Substrac 1 to the plane counter 
        #so if you want to see a certain plane then see everything and then back to see the plane you were watching,
        #  as the plane funtion always add 1 to the counter, in order to see the next one the next time, 
        # by substracting 1 we can assure than the next time the player press w it will show the same plane just before looking at everything 

    def show_one_floor(self, current_z=None):#Show only one horizontal plane (z-level).
        if current_z is None:
            # Cycle through z-levels (0 to size-1)
            if not hasattr(self, 'current_plane'):
                self.current_plane = 0  # Start with the bottom plane (z=0)
            else:
                self.current_plane = (self.current_plane + 1) % self.size  # Cycle to next plane
            z = self.current_plane
        else:
            # Use the specified z-level (for testing or manual input)
            z = current_z
            if not (0 <= z < self.size):
                #print(f"Invalid z-level: {z}. Must be between 0 and {self.size-1}")
                return

        #print(f"Showing horizontal plane at z = {z}")

        # Show/hide grid nodes (CollisionSpheres)
        for node in self.nodes:
            # Extract coordinates from the node name (e.g., "vertex_x,y,z" -> split by "_" then ",")
            name_parts = node.getName().split('_')
            if len(name_parts) > 1:  # Ensure the name has the "vertex_" prefix
                coords = name_parts[1].split(',')  # Get the coordinates part
                x,y, z_pos = [float(coord) for coord in coords]  # Convert to floats
                if int(z_pos) == z:
                    node.setScale(1.0)  # Show nodes on this plane
                else:
                    node.setScale(0.0)  # Hide nodes on other planes
            else:
                #print(f"Unexpected node name format: {node.getName()}")
                continue

        # Show/hide balls (from self.balls)
        for pos, ball_data in list(self.balls.items()):  # Use list() to avoid runtime changes
            x,y,z_pos = pos
            if z_pos == z:
                ball_data['node'].setScale(0.5)  # Show balls on this plane (maintain original scale)
            else:
                ball_data['node'].setScale(0.0)  # Hide balls on other planes

app = GridDemo(1)  # Set the size of the board
app.run()