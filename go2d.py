import tkinter as tk

root = tk.Tk()
root.title("Go")
N = 9  

class Point():
    def __init__(self, coordinates):
        self.coordinates = coordinates 
        self.status = 'empty'
        self.neighbors = set()


# Crear puntos
Points_matrix = [[[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],]

for i in range(N):
    for j in range(N):
        Points_matrix[i][j] = Point([i,j])

#asignando vecinos 

for i in range(1,N-1):
    Points_matrix[i][0].neighbors.add(Points_matrix[i][1])
    Points_matrix[i][0].neighbors.add(Points_matrix[i+1][0])
    Points_matrix[i][0].neighbors.add(Points_matrix[i-1][0])

    Points_matrix[i][-1].neighbors.add(Points_matrix[i][-2])
    Points_matrix[i][-1].neighbors.add(Points_matrix[i+1][-1])
    Points_matrix[i][-1].neighbors.add(Points_matrix[i-1][-1])

    Points_matrix[0][i].neighbors.add(Points_matrix[1][i])
    Points_matrix[0][i].neighbors.add(Points_matrix[0][i+1])
    Points_matrix[0][i].neighbors.add(Points_matrix[0][i-1])

    Points_matrix[-1][i].neighbors.add(Points_matrix[-2][i])
    Points_matrix[-1][i].neighbors.add(Points_matrix[-1][i+1])
    Points_matrix[-1][i].neighbors.add(Points_matrix[-1][i-1])

    for j in range(1,N-1):
        Points_matrix[i][j].neighbors.add(Points_matrix[i+1][j])
        Points_matrix[i][j].neighbors.add(Points_matrix[i-1][j])
        Points_matrix[i][j].neighbors.add(Points_matrix[i][j+1])
        Points_matrix[i][j].neighbors.add(Points_matrix[i][j-1])

Points_matrix[0][0].neighbors.add(Points_matrix[0][1])
Points_matrix[0][0].neighbors.add(Points_matrix[1][0])

Points_matrix[-1][0].neighbors.add(Points_matrix[-2][0])
Points_matrix[-1][0].neighbors.add(Points_matrix[-1][1])

Points_matrix[0][-1].neighbors.add(Points_matrix[0][-2])
Points_matrix[0][-1].neighbors.add(Points_matrix[1][-1])

Points_matrix[-1][-1].neighbors.add(Points_matrix[-2][-1])
Points_matrix[-1][-1].neighbors.add(Points_matrix[-1][-2])


cell_size = 50
mid_cell_size = cell_size / 2
canvas_size = N * cell_size

canvas = tk.Canvas(root, width=canvas_size, height=canvas_size, bg = "SystemButtonFace")
canvas.pack()

mid_cell_size = cell_size / 2


colour = True # black = True, white = False
count = True



def place_stone(event):
    global colour, count, stone, touched_point

    if not(count):
        canvas.delete(stone)

    coord = [round((event.x-mid_cell_size)/cell_size),round((event.y-mid_cell_size) / cell_size)]
    touched_point = Points_matrix[coord[0]][coord[1]]
    
    x = touched_point.coordinates[0]* cell_size + mid_cell_size
    y = touched_point.coordinates[1]* cell_size + mid_cell_size

    if touched_point.status == 'empty':
        if colour:
            stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill="black")
            count = False
        else:
            stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill="white")
            count = False
    
    else:
        print('invalid')

    


def update():
    global colour, touched_point, count
    if colour:
    
        touched_point.status = 'black'
        print('white turn')
        colour = False
    else: 
        
        touched_point.status = 'white'
        print('black turn')
        colour = True

    for i in range(N):
        for j in range(N):

            print('posicion '+str(i)+str(j),Points_matrix[i][j].status)
            
            if Points_matrix[i][j].status == 'empty':
                continue

            elif Points_matrix[i][j].status == 'black':
                canvas.create_oval(x-15, y-15, x+15, y+15, fill="black")

            elif Points_matrix[i][j].status == 'white': 
                canvas.create_oval(x-15, y-15, x+15, y+15, fill="white")
    count = True


'''
def view_neighbors(event):

    coord = [round((event.x-mid_cell_size)/cell_size),round((event.y-mid_cell_size) / cell_size)]
    touched_point = Points_matrix[coord[0]][coord[1]]
    
    for n in touched_point.neighbors:
        x = n.coordinates[0]* cell_size + mid_cell_size
        y = n.coordinates[1]* cell_size + mid_cell_size

        canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")
'''


for i in range(N):
    
    x = i * cell_size + mid_cell_size
    y = i * cell_size + mid_cell_size
    
    canvas.create_line(x, mid_cell_size, x, canvas_size - mid_cell_size, fill="black", width=2)
    canvas.create_line(mid_cell_size, y, canvas_size - mid_cell_size, y, fill="black", width=2)



play = tk.Button(root, text='Play', height=2, width=10, pady = 5,command = update)
play.pack()


canvas.bind('<Button-1>', place_stone)

root.mainloop()
