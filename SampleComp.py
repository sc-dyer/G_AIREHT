from Component import Component
from ComponentMol import *
from GeochemConst import *

import easygui
REMOVE_AP = False#Temporary constant, set as true if you want to remove Ca as apatite
#A class for handling each record in a table of compositions
class SampleComp:
    
    def __init__(self, nameIn, wtArrayIn, componentsIn, sampleMass):
        self.name = nameIn
        self.wtArray = wtArrayIn
        self.components = componentsIn #The components that correspond to each weight
        self.mass = sampleMass #Mass in g
        self.convertMol()
        
        
    def convertMol(self):
        #Convert wt% to mols as cations!
        msg = "Do you want to remove Phosphorous as Apatite?"
        title = ""
        choices = ["Yes","No"]
        removeAp = easygui.ynbox(msg,title,choices)
        self.molArray = []
        feOPos = -1
        fe2O3Pos = -1
        CaOPos = -1
        PPos = -1
        for i in range(len(self.wtArray)):

            oxideWeight = self.components[i].weight*self.components[i].catNum + self.components[i].catNum*self.components[i].ox2cat*O.weight #Oxide M = M component * cations in oxide + M O * #O in oxide
            weightComponent = (self.wtArray[i]/100)*self.mass
            


            mol = self.components[i].catNum*weightComponent/oxideWeight # CatNum * Wt / M gives number of mols of that cation
            thisComponent = ComponentMol(self.components[i],mol)
            self.molArray.append(thisComponent)

            if self.components[i].oxName== "FeO":
                feOPos = i
            elif self.components[i].oxName == "Fe2O3":
                fe2O3Pos = i
            
            if self.components[i].oxName == "CaO":
                CaOPos = i
            if self.components[i].oxName == "P2O5":
                PPos = i
        #Basically if there is both FeO and Fe2O3 in the sample composition then 
        #add them together and put the total in the FeO column and bring the Fe2O3 column with 0
        if feOPos >= 0 and fe2O3Pos >= 0:
            self.molArray[feOPos].mol += self.molArray[fe2O3Pos].mol
            self.molArray.pop(fe2O3Pos)
            self.components.pop(fe2O3Pos)#This makes the wtArray not match with the components, shouldnt be an issue because wtArray isnt used again
        elif fe2O3Pos >=0:
            #Convert to FeO
            self.molArray[fe2O3Pos] = ComponentMol(Fe,self.molArray[fe2O3Pos].mol)
        
        #This is used if removing Ca with apatite
        #Calculates the proportion based on a formula Ca5(PO4)3(OH,F,Cl)
        if CaOPos >= 0 and PPos >= 0 and removeAp:
            CaRemoval = self.molArray[PPos].mol*5/3
            self.molArray[CaOPos].mol -= CaRemoval
            self.molArray.pop(PPos)
        elif PPos >= 0 and not removeAp:
            self.molArray.pop(PPos)

            
          
    def calcO2(self, redCO2, CO2, H2O):
        #Adds to the molArray the amount of O2 that works with the amount of CO2 and H2O
        hComponent = ComponentMol(H,H2O*2)
        cComponent = ComponentMol(C,CO2)
        oComponent = ComponentMol(O,0)

        #Add up the proportionate amount of mols of O for each component
        self.molArray.append(hComponent)
        for i in range(len(self.molArray)):
            oComponent.mol += self.molArray[i].mol* self.molArray[i].ox2cat
        if not redCO2:
             oComponent.mol += cComponent.mol* cComponent.ox2cat

        self.molArray.append(cComponent)
        self.molArray.append(oComponent)
        



    # def convertMolCent(self):
    #     #Convert mol to mol %
    #     #Note this is not molar oxides, just %Mol of Cations
    #     #Shouldnt be hard to alter this to do mol% oxides though
        
    #     self.molCent = []
    #     totMol = sum(self.molArray)
        
    #     for elem in self.molArray:
    #         percent = 100*elem/totMol
    #         self.molCent.append(round(percent, 5))
            
    # def writeTHERINcompo(self, redCO2, CO2, H2O):
    #     #Makes the composition line for the THERIN file
    #     mol_O = 0
    #     therin = ""
    #     for i in range(len(self.molArray)):
    #         #IF block, writes to the file and calculates Oxygen
    #         #If a CO2 or H2O value is given, they will ignore the values that might be in the data tables
    #         #If CO2 is reduced, it will ignore the value for the Oxygen calculation
    #         currComp = self.components[i]
    #         if self.molArray[i] > 0:
                
    #             if redCO2 or CO2 >= 0:
    #                 if H2O >= 0:
    #                     if currComp.formula!= "H2O" and currComp.formula!= "CO2" :
    #                         mol_O += self.molArray[i]*currComp.ox2cat            
    #                         therin += currComp.cation.upper() + "(" + str(self.molArray[i]) + ")"
    #                 elif currComp.formula!= "CO2":#Ignore the CO2 column for adding up mols of stuff
    #                     mol_O += self.molArray[i]*currComp.ox2cat            
    #                     therin += currComp.cation.upper() + "(" + str(self.molArray[i]) + ")"
    #             else:
    #                 if H2O >= 0:
    #                     if currComp.formula!= "H2O":
    #                         mol_O += self.molArray[i]*currComp.ox2cat            
    #                         therin += currComp.cation.upper() + "(" + str(self.molArray[i]) + ")"
    #                 else:
    #                         mol_O += self.molArray[i]*currComp.ox2cat            
    #                         therin += currComp.cation.upper() + "(" + str(self.molArray[i]) + ")"
                
    #             if not redCO2 and CO2 < 0:#This is to catch if CO2 is reduced but you still have a value provided in the data table
    #                 if currComp.formula== "CO2":
    #                         mol_O += self.molArray[i]*currComp.ox2cat            
    #                         therin += currComp.cation.upper() + "(" + str(self.molArray[i]) + ")"
    #             elif redCO2 and CO2 <0:
    #                 if currComp.formula== "CO2":
    #                     therin += currComp.cation.upper() + "(" + str(self.molArray[i]) + ")"
                    
    #     #Write preset C and H into file
    #     if CO2 >= 0 and not redCO2:
    #         mol_O += CO2*2
    #         therin += "C(" + str(CO2) + ")"
    #     elif CO2 >= 0:
    #         therin += "C(" + str(CO2) + ")"
            
        
    #     if H2O >= 0:
    #         mol_O += H2O
    #         therin += "H(" + str(H2O*2) + ")"
    
    #     therin += "O(" + str(round(mol_O,6)) + ")     *"
    #     return therin