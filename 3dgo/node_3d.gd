extends Node3D

const BOARD_SIZE = 3  # 9x9 Go boards
const STACK_HEIGHT = 3  # Number of layers
const LAYER_SPACING = 10  # Adjust spacing between boards

func _ready():
	for z in range(STACK_HEIGHT):
		var board = create_board()
		board.position = Vector3(0, z * LAYER_SPACING, 0)  # Move along Y-axis
		add_child(board)  # Make sure the board is added to the scene

func create_board():
	var mesh_instance = MeshInstance3D.new()
	var mesh = PlaneMesh.new()
	mesh.size = Vector2(BOARD_SIZE, BOARD_SIZE)  # Make boards bigger
	mesh_instance.mesh = mesh

	return mesh_instance  # Return the new board
