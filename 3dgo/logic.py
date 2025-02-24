from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile
loadPrcFile("config\conf.prc")

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

# Ejecutar el juego
game = Board()

game.run()