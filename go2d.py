import tkinter as tk

root = tk.Tk()
root.title("Go")
N = 9

class Point():
    def __init__(self, coordinates):
        self.coordinates = coordinates 
        self.status = 'empty'
        self.stoneID = None
        self.neighbors = set()

    def find_conected(self,conected):
            
        if self.status != 'empty':
            conected.add(self)

            for n in self.neighbors-conected:
                if self.status == n.status:
                    n.find_conected(conected)
        return conected

    
    def death_decision(self): # True = the conected should die
        conected = set()
        conected = self.find_conected(conected)
        b = False
        if len(conected) != 0: 
            b = True
            for m in conected:
                for q in m.neighbors:
                    b = b and (q.status != 'empty')
            if b:
                for m in conected:
                    m.status = 'empty'
                    canvas.delete(m.stoneID)
        return b 

    

# Crear puntoscd tu-repositorio

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

    b = touched_point.death_decision()

    if b:
        print('invalid')
    else:
        if touched_point.status == 'empty':

            if colour:
                stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill="black")
                count = False
            else:
                stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill="white")
                count = False

            touched_point.stoneID = stone

        else:
            print('invalid')

    




def update():
    global colour, touched_point, count
    count = True


    if colour:
        touched_point.status = 'black'
        
        for n in touched_point.neighbors:
            n.death_decision()

        print('white turn')
        colour = False

    else: 
        touched_point.status = 'white'

        for n in touched_point.neighbors:
            n.death_decision()

        print('black turn')
        colour = True



for i in range(N):
    
    x = i * cell_size + mid_cell_size
    y = i * cell_size + mid_cell_size
    
    canvas.create_line(x, mid_cell_size, x, canvas_size - mid_cell_size, fill="black", width=2)
    canvas.create_line(mid_cell_size, y, canvas_size - mid_cell_size, y, fill="black", width=2)



play = tk.Button(root, text='Play', height=2, width=10, pady = 5,command = update)
play.pack()

canvas.bind('<Button-1>', place_stone)

root.mainloop()