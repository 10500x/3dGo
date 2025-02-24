from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4
from panda3d.core import loadPrcFile
from panda3d.core import Vec2, Vec3
from panda3d.core import LineSegs, NodePath, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue, CollisionRay
from panda3d.core import Point3
import math
from camera import Camera
loadPrcFile("config\conf.prc")

class Grid(ShowBase):
    def __init__(self, size, spacing, render, loader):
        self.picker = CollisionTraverser()  # Initialize the collision traverser
        self.pq = CollisionHandlerQueue()   # Initialize the collision handler queue
        self.vertices = {}  # Dictionary to store vertex nodes
        self.grid_size = size  # Grid size, always gridsize-1
        self.spacing = spacing  # Space between lines
        self.render = render    # Use the render from Main
        self.loader = loader    # Use the loader from Main
        self.create_grid(self.grid_size, self.spacing)
    def create_grid(self,size,spacing):
        # Create a node for the grid
        grid_node = LineSegs("grid")
        grid_node.setThickness(1)  # Adjust thickness of lines
        # Store intersection points
        intersections = []
        # Generate horizontal and vertical lines
        for h in range (0,size):
            for i in range(0,size+1):
                x = i * spacing
                y = i * spacing

                # Horizontal line
                grid_node.moveTo(0, x, h)
                grid_node.drawTo(size * spacing, x, h)

                # Vertical line
                grid_node.moveTo(y, 0, h)
                grid_node.drawTo(y, size * spacing, h)

                # Add intersection points
                for j in range(size+1):
                    intersections.append((j * spacing, i * spacing, h))
        # Convert to node
        grid_np = NodePath(grid_node.create())
        grid_np.reparentTo(self.render)
        # Place spheres at intersections
        for pos in intersections:
            self.create_vertex_object(pos)

    def create_vertex_object(self, position):
        """Creates an invisible collision sphere at the vertex."""
        vertex_node = NodePath("vertex")  # Empty node to store objects
        vertex_node.setPos(position)
        vertex_node.reparentTo(self.render)

        """Creates a small sphere at a given position."""
        sphere = self.loader.loadModel("smiley")  # Using a built-in model for example
        sphere.setScale(0.05)  # Make it small
        sphere.setPos(position)
        sphere.reparentTo(self.render)
        sphere.setTexture(self.loader.loadTexture("textures/white.png"), 1)

         # Add collision node to sphere
        c_node = CollisionNode("vertex")
        c_node.addSolid(CollisionSphere(0, 0, 0, 0.5))  # Small sphere for collision
        c_node.setIntoCollideMask(1)  # Enable collision detection
        c_np = vertex_node.attachNewNode(c_node)
        
        self.picker.addCollider(c_np, self.pq)
        self.vertices[c_np] = vertex_node  # Store NodePath reference