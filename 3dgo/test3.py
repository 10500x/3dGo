from panda3d.core import LineSegs, NodePath, CollisionTraverser, CollisionNode, CollisionRay, CollisionHandlerQueue
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3

class GridDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.grid_size = 10  # Number of lines
        self.spacing = 1.0  # Space between lines

        # Collision system
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        
        self.picker_ray = CollisionRay()
        picker_node = CollisionNode("mouseRay")
        picker_node.addSolid(self.picker_ray)
        picker_np = self.camera.attachNewNode(picker_node)
        
        self.picker.addCollider(picker_np, self.pq)

        self.accept("mouse1", self.on_click)  # Left-click event

        self.vertices = []  # Store vertex objects for picking
        self.create_grid()

    def create_grid(self):
        """Creates the grid and intersection vertices."""
        grid_node = LineSegs("grid")
        grid_node.setThickness(2)

        for i in range(self.grid_size):
            x = i * self.spacing
            y = i * self.spacing

            # Draw grid lines
            grid_node.moveTo(0, x, 0)
            grid_node.drawTo(self.grid_size * self.spacing, x, 0)
            grid_node.moveTo(y, 0, 0)
            grid_node.drawTo(y, self.grid_size * self.spacing, 0)

            # Create vertex objects
            for j in range(self.grid_size):
                pos = (j * self.spacing, i * self.spacing, 0)
                self.create_vertex_object(pos)

        # Convert to node
        grid_np = NodePath(grid_node.create())
        grid_np.reparentTo(self.render)

    def create_vertex_object(self, position):
        """Creates a sphere at the given position and adds collision detection."""
        sphere = self.loader.loadModel("smiley")  # Using built-in model
        sphere.setScale(0.1)
        sphere.setPos(*position)
        sphere.reparentTo(self.render)

        # Add collision node to sphere
        c_node = CollisionNode("vertex")
        c_node.addSolid(CollisionRay(0, 0, 0, 0, 0, 1))  # Ray for collision
        c_node.setFromCollideMask(1)  
        c_np = sphere.attachNewNode(c_node)
        
        self.picker.addCollider(c_np, self.pq)
        self.vertices.append((sphere, position))  # Store for reference

    def on_click(self):
        """Handles click events to detect which vertex was clicked."""
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.picker_ray.setFromLens(self.camNode, mpos.getX(), mpos.getY())

            self.picker.traverse(self.render)

            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                picked_obj = self.pq.getEntry(0).getIntoNodePath().getParent()

                for vertex, pos in self.vertices:
                    if picked_obj == vertex:
                        self.spawn_model(pos)
                        break

    def spawn_model(self, position):
        """Spawns a new 3D model at the given position."""
        model = self.loader.loadModel("models/misc/xyzAxis")  # Replace with custom model
        model.setScale(0.2)
        model.setPos(position)
        model.reparentTo(self.render)

app = GridDemo()
app.run()
