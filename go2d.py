import tkinter as tk

root = tk.Tk()
root.title("Go")

N = 9

class Point(): 
    '''
    This class represents a Point in Go Board 
    Atributes: 
    - coordinates : posicion in the Go Board
    - status : empty, black or white
    - stoneID : the circle drawn in the canvas when the point is not empty
    - neighbors : set of neighbors, initialized empty but assigned manualy, 2,3 or 4, for corner, lateral or central points respectively
    '''
    def __init__(self, coordinates):
        self.coordinates = coordinates 
        self.status = 'empty'     
        self.stoneID = None         
        self.neighbors = set()    

    def find_conected(self,conected): 
        '''
        returns the set of points that are conected with a specific point when is not empty 
        '''
        if self.status != 'empty':
            conected.add(self)

            for n in self.neighbors-conected:
                if self.status == n.status:
                    n.find_conected(conected)
        return conected

    
    def death_decision(self, test = False): 
        '''
        decides whether a point should die following GO rules, (True = the point should die). If test = True
        the function does not change the point status nor delete the stone
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
                    m.status = 'empty'
                    canvas.delete(m.stoneID)
        return b

    

Points_matrix = [[[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],
                 [[],[],[],[],[],[],[],[],[]],] # matrix where the points are stored 


# asigning neighbors manualy-----------------------------

for i in range(N):
    for j in range(N):
        Points_matrix[i][j] = Point([i,j])

for i in range(1,N-1):
    # Lateral points 
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
        # central points 
        Points_matrix[i][j].neighbors.add(Points_matrix[i+1][j])
        Points_matrix[i][j].neighbors.add(Points_matrix[i-1][j])
        Points_matrix[i][j].neighbors.add(Points_matrix[i][j+1])
        Points_matrix[i][j].neighbors.add(Points_matrix[i][j-1])

# corner points
Points_matrix[0][0].neighbors.add(Points_matrix[0][1])
Points_matrix[0][0].neighbors.add(Points_matrix[1][0])

Points_matrix[-1][0].neighbors.add(Points_matrix[-2][0])
Points_matrix[-1][0].neighbors.add(Points_matrix[-1][1])

Points_matrix[0][-1].neighbors.add(Points_matrix[0][-2])
Points_matrix[0][-1].neighbors.add(Points_matrix[1][-1])

Points_matrix[-1][-1].neighbors.add(Points_matrix[-2][-1])
Points_matrix[-1][-1].neighbors.add(Points_matrix[-1][-2])


# canvas board info
cell_size = 50
mid_cell_size = cell_size / 2
canvas_size = N * cell_size

canvas = tk.Canvas(root, width=canvas_size, height=canvas_size, bg = "SystemButtonFace")
canvas.pack()

mid_cell_size = cell_size / 2



colour = 'black' # Colour of actual player
count = True # first click (if false, last stone is deleted)
legal = False # if True, permits update the game

def place_stone(event):
    '''
    This function draw a stone when the player click the canvas and the movemente is legal.
    This function chek the rules and does not makes permanent changes in the matrix of points nor
    in the status of them.  
    '''
    global colour, count, stone, touched_point, legal
    
    coord = [round((event.x-mid_cell_size)/cell_size),round((event.y-mid_cell_size) / cell_size)]
    touched_point = Points_matrix[coord[0]][coord[1]]
    
    x = touched_point.coordinates[0]* cell_size + mid_cell_size
    y = touched_point.coordinates[1]* cell_size + mid_cell_size


    if not(count):
        canvas.delete(stone)


    if touched_point.status == 'empty':

        # b1 Chek if the touched point makes the conected component to die
        touched_point.status = colour
        b1 = touched_point.death_decision(test = True)  
        touched_point.status = 'empty'

        if b1: 

            # if b1 is True, b2 cheks if the movement kills a conected component of the oponent
            b2 = False
            touched_point.status = colour
            conected = set()
            conected = touched_point.find_conected(conected)

            for m in conected:
                for n in m.neighbors-conected:
                    b2 = b2 or n.death_decision(test = True)

            touched_point.status = 'empty'

            if b2:   # if b2 True, the movement is legal besides b1 
                stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill=colour)
                count = False
                legal = True

            else: # if not, the movement is a suicide
                print('invalid, not suicide')
                count = False
                stone = canvas.create_oval(x-1e-16, y-1e-16, x+1e-16, y+1e-16, fill=colour) # note that this oval is practically invisble
                
                    
        else:
            stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill=colour)
            count = False
            legal = True

        touched_point.stoneID = stone
    else:
        print('invalid, the place is not empty')

    

def update():
    '''
    this function activates when the player press the play button, if a movement was made and it is legal, makes permanents changes
    in the matrix of points and chage the turn. 
    '''
    global colour, touched_point, count, legal

    if legal:
        legal = False
        count = True

        touched_point.status = colour
        conected = set()
        conected = touched_point.find_conected(conected)

        for n in touched_point.neighbors-conected:
                n.death_decision()

        # changing the turn 
        if colour == 'black':
            colour = 'white'
        else:
            colour = 'black'

        print(colour+' turn')
    else: 
        print('plaese play a legal move')


# Draw of the board

for i in range(N):
    
    x = i * cell_size + mid_cell_size
    y = i * cell_size + mid_cell_size
    
    canvas.create_line(x, mid_cell_size, x, canvas_size - mid_cell_size, fill="black", width=2)
    canvas.create_line(mid_cell_size, y, canvas_size - mid_cell_size, y, fill="black", width=2)

# play button

play = tk.Button(root, text='Play', height=2, width=10, pady = 5,command = update)
play.pack()

canvas.bind('<Button-1>', place_stone)

root.mainloop()