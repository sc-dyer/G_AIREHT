#A simple class to define elemental components of a rock
class Component:
    
    def __init__(self, name, M, ox, cNum, oName):
        
        self.element = name
        self.weight = M
        self.ox2cat = ox #ratio of O to cation if in an oxide
        self.catNum = cNum # Num of cations in an oxide
        self.oxName = oName
        