import tkinter as tk

# Board info

N = 5
cell_size = 50
mid_cell_size = cell_size / 2
canvas_size = N * cell_size
mid_cell_size = cell_size / 2

# Window configuration

root = tk.Tk()
root.title("Go")
root.geometry('1400x'+str(int(canvas_size+30)))

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

main_canvas = tk.Canvas(main_frame)
main_canvas.pack(side="top", fill="both", expand=True)

scrollbar = tk.Scrollbar(main_frame, orient="horizontal", command = main_canvas.xview)
scrollbar.pack(side="bottom", fill="x")

main_canvas.configure(xscrollcommand = scrollbar.set)

inner_frame = tk.Frame(main_canvas)
main_canvas.create_window((0, 0), window = inner_frame, anchor="nw")

# Point class

class Point(): 
    '''
    This class represents a Point in Go Board 
    Atributes: 
    - coordinates : posicion in the Go Board
    - status : empty, black or white
    - canvas : canvas that represents the board where the point is
    - stoneID : the circle drawn in the canvas when the point is not empty
    - neighbors : set of neighbors, initialized empty but assigned manualy, 3,4, 5 or 6, for corner, edge, lateral or central points respectively
    '''
    def __init__(self, coordinates):
        self.coordinates = coordinates 
        self.status = 'empty'
        self.canvas = None     
        self.stoneID = None         
        self.neighbors = set()    

    def find_conected(self,conected): 
        '''
        returns the set of all the points of the same color that are conected with the point.
        '''
        if self.status != 'empty':
            conected.add(self)

            for n in self.neighbors-conected:
                if self.status == n.status:
                    n.find_conected(conected)
        return conected

    
    def death_decision(self, test = False): 
        '''
        decides whether a point should die, (True = the point should die). If test = True
        the function does not change the point status nor delete the stone, if test = False
        the function deletes permanently all the conectd component of the point and changes the stastus of them. 
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
                    canvas = m.canvas
                    m.status = 'empty'
                    canvas.delete(m.stoneID)
        return b


# Drawing the boards

abc = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N']

tableros = []

for i in range(N):
    Board = tk.Canvas(inner_frame ,width = cell_size*N,height = cell_size*N, background = 'SystemButtonFace' )
    for j in range(N):
            
        x = j * cell_size + mid_cell_size
        y = j * cell_size + mid_cell_size
        label = tk.Label(inner_frame,text=abc[j], font=('Arial',14))
        Board.create_window(x,-5, window = label)

        Board.create_line(x, mid_cell_size, x, canvas_size - mid_cell_size, fill="black", width=2)
        Board.create_line(mid_cell_size, y, canvas_size - mid_cell_size, y, fill="black", width=2)

    Board.grid(row = 0, column = i, padx = 10, pady = 20)

    tableros.append(Board)

# asigning neighbors manualy

Points_matrix = []

for i in range(N):
    Points_matrix.append([])
    for j in range(N):
        Points_matrix[i].append([])
        for k in range(N):
            Points_matrix[i][j].append([])

            Points_matrix[i][j][k] = Point([i,j,k])
            Points_matrix[i][j][k].canvas = tableros[k]   


for i in range(1,N-1):
    # the twelve edge points (four neighbors each) 

    #1
    Points_matrix[i][0][0].neighbors.add(Points_matrix[i-1][0][0])  
    Points_matrix[i][0][0].neighbors.add(Points_matrix[i+1][0][0])
    Points_matrix[i][0][0].neighbors.add(Points_matrix[i][1][0])
    Points_matrix[i][0][0].neighbors.add(Points_matrix[i][0][1]) 

    #2
    Points_matrix[i][-1][0].neighbors.add(Points_matrix[i-1][-1][0])  
    Points_matrix[i][-1][0].neighbors.add(Points_matrix[i+1][-1][0])
    Points_matrix[i][-1][0].neighbors.add(Points_matrix[i][-2][0])
    Points_matrix[i][-1][0].neighbors.add(Points_matrix[i][-1][1]) 

    #3
    Points_matrix[i][-1][-1].neighbors.add(Points_matrix[i-1][-1][-1])  
    Points_matrix[i][-1][-1].neighbors.add(Points_matrix[i+1][-1][-1])
    Points_matrix[i][-1][-1].neighbors.add(Points_matrix[i][-1][-2])
    Points_matrix[i][-1][-1].neighbors.add(Points_matrix[i][-2][-1]) 

    #4
    Points_matrix[i][0][-1].neighbors.add(Points_matrix[i-1][0][-1])  
    Points_matrix[i][0][-1].neighbors.add(Points_matrix[i+1][0][-1])
    Points_matrix[i][0][-1].neighbors.add(Points_matrix[i][1][-1])
    Points_matrix[i][0][-1].neighbors.add(Points_matrix[i][0][-2]) 

    #5
    Points_matrix[0][i][0].neighbors.add(Points_matrix[0][i-1][0])  
    Points_matrix[0][i][0].neighbors.add(Points_matrix[0][i+1][0])
    Points_matrix[0][i][0].neighbors.add(Points_matrix[1][i][0])
    Points_matrix[0][i][0].neighbors.add(Points_matrix[0][i][1]) 

    #6
    Points_matrix[-1][i][0].neighbors.add(Points_matrix[-1][i-1][0])  
    Points_matrix[-1][i][0].neighbors.add(Points_matrix[-1][i+1][0])
    Points_matrix[-1][i][0].neighbors.add(Points_matrix[-2][i][0])
    Points_matrix[-1][i][0].neighbors.add(Points_matrix[-1][i][1]) 

    #7
    Points_matrix[-1][i][-1].neighbors.add(Points_matrix[-1][i-1][-1])  
    Points_matrix[-1][i][-1].neighbors.add(Points_matrix[-1][i+1][-1])
    Points_matrix[-1][i][-1].neighbors.add(Points_matrix[-1][i][-2])
    Points_matrix[-1][i][-1].neighbors.add(Points_matrix[-2][i][-1]) 

    #8
    Points_matrix[0][i][-1].neighbors.add(Points_matrix[0][i-1][-1])  
    Points_matrix[0][i][-1].neighbors.add(Points_matrix[0][i+1][-1])
    Points_matrix[0][i][-1].neighbors.add(Points_matrix[1][i][-1])
    Points_matrix[0][i][-1].neighbors.add(Points_matrix[0][i][-2]) 

    #9
    Points_matrix[0][0][i].neighbors.add(Points_matrix[0][0][i-1])  
    Points_matrix[0][0][i].neighbors.add(Points_matrix[0][0][i+1])
    Points_matrix[0][0][i].neighbors.add(Points_matrix[1][0][i])
    Points_matrix[0][0][i].neighbors.add(Points_matrix[0][1][i]) 

    #10
    Points_matrix[-1][0][i].neighbors.add(Points_matrix[-1][0][i-1])  
    Points_matrix[-1][0][i].neighbors.add(Points_matrix[-1][0][i+1])
    Points_matrix[-1][0][i].neighbors.add(Points_matrix[-2][0][i])
    Points_matrix[-1][0][i].neighbors.add(Points_matrix[-1][1][i]) 

    #11
    Points_matrix[-1][-1][i].neighbors.add(Points_matrix[-1][-1][i-1])  
    Points_matrix[-1][-1][i].neighbors.add(Points_matrix[-1][-1][i+1])
    Points_matrix[-1][-1][i].neighbors.add(Points_matrix[-1][-2][i])
    Points_matrix[-1][-1][i].neighbors.add(Points_matrix[-2][-1][i]) 

    #12
    Points_matrix[0][-1][i].neighbors.add(Points_matrix[0][-1][i-1])  
    Points_matrix[0][-1][i].neighbors.add(Points_matrix[0][-1][i+1])
    Points_matrix[0][-1][i].neighbors.add(Points_matrix[1][-1][i])
    Points_matrix[0][-1][i].neighbors.add(Points_matrix[0][-2][i]) 

    for j in range(1,N-1):
        # the six faces of lateral points (five neighbors each) 

        #1
        Points_matrix[i][j][0].neighbors.add(Points_matrix[i][j][1])
        Points_matrix[i][j][0].neighbors.add(Points_matrix[i-1][j][0])
        Points_matrix[i][j][0].neighbors.add(Points_matrix[i+1][j][0])
        Points_matrix[i][j][0].neighbors.add(Points_matrix[i][j-1][0])
        Points_matrix[i][j][0].neighbors.add(Points_matrix[i][j+1][0])

        #2
        Points_matrix[i][j][-1].neighbors.add(Points_matrix[i][j][-2])
        Points_matrix[i][j][-1].neighbors.add(Points_matrix[i-1][j][-1])
        Points_matrix[i][j][-1].neighbors.add(Points_matrix[i+1][j][-1])
        Points_matrix[i][j][-1].neighbors.add(Points_matrix[i][j-1][-1])
        Points_matrix[i][j][-1].neighbors.add(Points_matrix[i][j+1][-1])

        #3
        Points_matrix[i][0][j].neighbors.add(Points_matrix[i][1][j])
        Points_matrix[i][0][j].neighbors.add(Points_matrix[i-1][0][j])
        Points_matrix[i][0][j].neighbors.add(Points_matrix[i+1][0][j])
        Points_matrix[i][0][j].neighbors.add(Points_matrix[i][0][j-1])
        Points_matrix[i][0][j].neighbors.add(Points_matrix[i][0][j+1])

        #4
        Points_matrix[i][-1][j].neighbors.add(Points_matrix[i][-2][j])
        Points_matrix[i][-1][j].neighbors.add(Points_matrix[i-1][-1][j])
        Points_matrix[i][-1][j].neighbors.add(Points_matrix[i+1][-1][j])
        Points_matrix[i][-1][j].neighbors.add(Points_matrix[i][-1][j-1])
        Points_matrix[i][-1][j].neighbors.add(Points_matrix[i][-1][j+1])

        #5
        Points_matrix[0][i][j].neighbors.add(Points_matrix[1][i][j])
        Points_matrix[0][i][j].neighbors.add(Points_matrix[0][i-1][j])
        Points_matrix[0][i][j].neighbors.add(Points_matrix[0][i+1][j])
        Points_matrix[0][i][j].neighbors.add(Points_matrix[0][i][j-1])
        Points_matrix[0][i][j].neighbors.add(Points_matrix[0][i][j+1])

        #6
        Points_matrix[-1][i][j].neighbors.add(Points_matrix[-2][i][j])
        Points_matrix[-1][i][j].neighbors.add(Points_matrix[-1][i-1][j])
        Points_matrix[-1][i][j].neighbors.add(Points_matrix[-1][i+1][j])
        Points_matrix[-1][i][j].neighbors.add(Points_matrix[-1][i][j-1])
        Points_matrix[-1][i][j].neighbors.add(Points_matrix[-1][i][j+1])

        for k in range(1,N-1):
            # central points (six neighbors)
            Points_matrix[i][j][k].neighbors.add(Points_matrix[i][j][k-1]) 
            Points_matrix[i][j][k].neighbors.add(Points_matrix[i][j][k+1]) 
            Points_matrix[i][j][k].neighbors.add(Points_matrix[i][j-1][k]) 
            Points_matrix[i][j][k].neighbors.add(Points_matrix[i][j+1][k]) 
            Points_matrix[i][j][k].neighbors.add(Points_matrix[i-1][j][k]) 
            Points_matrix[i][j][k].neighbors.add(Points_matrix[i+1][j][k]) 
            
# the eight corner points (three neighbors each)

#1
Points_matrix[0][0][0].neighbors.add(Points_matrix[1][0][0])
Points_matrix[0][0][0].neighbors.add(Points_matrix[0][1][0])
Points_matrix[0][0][0].neighbors.add(Points_matrix[0][0][1])

#2
Points_matrix[-1][0][0].neighbors.add(Points_matrix[-2][0][0])
Points_matrix[-1][0][0].neighbors.add(Points_matrix[-1][1][0])
Points_matrix[-1][0][0].neighbors.add(Points_matrix[-1][0][1])

#3
Points_matrix[-1][-1][0].neighbors.add(Points_matrix[-2][-1][0])
Points_matrix[-1][-1][0].neighbors.add(Points_matrix[-1][-2][0])
Points_matrix[-1][-1][0].neighbors.add(Points_matrix[-1][-1][1])

#4
Points_matrix[-1][-1][-1].neighbors.add(Points_matrix[-2][-1][-1])
Points_matrix[-1][-1][-1].neighbors.add(Points_matrix[-1][-2][-1])
Points_matrix[-1][-1][-1].neighbors.add(Points_matrix[-1][-1][-2])

#5
Points_matrix[0][-1][-1].neighbors.add(Points_matrix[-1][-1][-1])
Points_matrix[0][-1][-1].neighbors.add(Points_matrix[0][-2][-1])
Points_matrix[0][-1][-1].neighbors.add(Points_matrix[0][-1][-2])

#6
Points_matrix[0][0][-1].neighbors.add(Points_matrix[-1][0][-1])
Points_matrix[0][0][-1].neighbors.add(Points_matrix[0][-1][-1])
Points_matrix[0][0][-1].neighbors.add(Points_matrix[0][0][-2])

#7
Points_matrix[-1][0][-1].neighbors.add(Points_matrix[-2][0][-1])
Points_matrix[-1][0][-1].neighbors.add(Points_matrix[-1][-1][-1])
Points_matrix[-1][0][-1].neighbors.add(Points_matrix[-1][0][-2])

#8
Points_matrix[0][-1][0].neighbors.add(Points_matrix[1][-1][0])
Points_matrix[0][-1][0].neighbors.add(Points_matrix[0][-2][0])
Points_matrix[0][-1][0].neighbors.add(Points_matrix[0][-1][1])

# principal functions

colour = 'black' # Colour of actual player
count = True # first click (if false, last stone is deleted)
legal = False # if True, permits update the game
last_stone = None
last_canvas = None 

def place_stone(event,canv_id):
    '''
    This function draw a stone when the player click the canvas and the movemente is legal.
    This function check the rules and does not makes permanent changes in the matrix of points nor
    in the status of them.  
    '''
    global colour, count, last_stone, last_canvas, touched_point, legal
    
    canvas = event.widget

    if not(count) and last_stone is not None and last_canvas is not None:
        last_canvas.delete(last_stone)


    last_canvas = canvas

    idx = 0
    for t in tableros:
        if t != canv_id:
            idx += 1
        else:
            break

    coord = [round((event.x-mid_cell_size)/cell_size),round((event.y-mid_cell_size) / cell_size)]
    touched_point = Points_matrix[coord[0]][coord[1]][idx]
    
    #print('toched_point = ',str(coord[0])+str(coord[1])+str(idx))
    
    x = touched_point.coordinates[0]* cell_size + mid_cell_size
    y = touched_point.coordinates[1]* cell_size + mid_cell_size

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
                last_stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill=colour)
                count = False
                legal = True

            else: # if not, the movement is a suicide
                print('invalid, not suicide')
                count = False
                last_stone = canvas.create_oval(x-1e-16, y-1e-16, x+1e-16, y+1e-16, fill=colour) # note that this oval is practically invisble
                    
        else:
            last_stone = canvas.create_oval(x-15, y-15, x+15, y+15, fill=colour)
            count = False
            legal = True

        touched_point.stoneID = last_stone
    else:
        print('invalid, the place is not empty')

    

def update(event):
    '''
    this function activates when the player press the space key, if a movement was made and it is legal, makes permanents changes
    in the matrix of points and change the turn. 
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


'''
play = tk.Button(inner_frame, text='Play', height=2, width=10, pady = 5,command = update)
play.grid(row = 1, column = 4)
'''


def region_search(point,region = set(),col_border = set()):
    if point.status == 'empty':
        region.add(point)
        #print(point.coordinates,' added')
        for n in (point.neighbors-region):
            region_search(n,region,col_border)
    else:
        col_border.add(point.status)
        #print(point.status, 'color added')
    return region, col_border



def count_points(event):
    black_points = 0
    white_points = 0
    visited = set()

    for i in range(N):
        for j in range(N):
            for k in range(N):
                actual  = Points_matrix[i][j][k]
                if actual.status == 'empty' and actual not in visited:
                    region = set()
                    col_border = set()
                    region, col_border = region_search(actual, region, col_border)

                    for v in region:
                        visited.add(v)

                    print(actual.coordinates)
                    print(len(region))
                    print(col_border)

                    if len(col_border) == 1:
                        if 'black' in col_border:
                            black_points += len(region)
                        else:
                            white_points += len(region)
                    

                elif actual.status == 'black':
                    black_points += 1
                elif actual.status == 'white':
                    white_points += 1

    print('\n Black : '+str(black_points)+'\n')
    print('White : '+str(white_points)+'\n')



root.bind('<space>',update)


for T in tableros:
    T.bind('<Button-1>', lambda event, canvas = T : place_stone(event, canvas))

def update_scroll_region(event):
    main_canvas.configure(scrollregion = main_canvas.bbox("all"))

root.bind('<f>',count_points)

inner_frame.bind("<Configure>", update_scroll_region)

root.mainloop()