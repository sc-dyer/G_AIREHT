#This is a garnet
#I am going to attempt to define it recursively
#God help me

#Garnets have a shape, composition, and density
from Shape import Shape 
from GeochemConst import *
from Component import Component
from ComponentMol import *
from GarnetComponent import GarnetComponent
from GarnetComponentMol import GarnetComponentMol
import copy


class Garnet:

	#Base case, the base shape should have the same dimensions of the shell thickness
	#E.g if shell thickness is 0.002 then the radius of the basecase sphere should be 0.002
	#I guess for ellipsoids since shell thickness varies depending on the axis we will define shell thickness as the one used for the a axis
	def __init__(self,crystalShape,grtCompo,nextGarnet=None,numGrt = 1):
		self.grtShape = crystalShape
		
		self.composition = copy.deepcopy(grtCompo) #This should be an array of GarnetComponentMol, this is the composition of this shell

		self.density = GRT_DENSITY/1000#Assumes same density for all (just for now I guess) convert it to g/mm^3 because blob uses mm

		self.nextShell = nextGarnet #base case is None, the next garnet can have its own composition and density


		self.bigAx = self.grtShape.getDim()
		#Only need to define number of garnets upoon nucleation
		if nextGarnet == None:
			self.numGrt = numGrt #number of garnets of this size class (base number is 1 which would look at every garnet individually)
		else:
			self.numGrt = nextGarnet.numGrt

		self.totVol = self.grtShape.getVolume() #Total volume is same as shape volume
		if(nextGarnet != None):
			self.shellVol = self.totVol - self.nextShell.totVol #Shell volume is the total volume less total volume of the next smallest shell
			#self.shellThick = self.grtShape.getDim() - self.nextShell.grtShape.getDim()
		else:
			self.shellVol = self.totVol #Base case tot and shell vol are same
			#self.shellThick = self.grtShape.getDim()#Gets radius for sphere and aAx for ellipsoid
		#Get the mols of the shell and the mols of the garnet

		

		self.calcShellMol() 
		self.calcTotMol()

		#Can add a thing to delete the inner garnet to speed things up but will be unable to moniter the garnet composition



	def calcShellMol(self):
		#This will calculate the mols of components in a single shell in this garnet
		#Assumes that the form of garnet is X3Al2Si3O12 where X is anything in CMPNT
		#Will also renormalize composition to 1 in case there are minor discrepencies
		mass = self.shellVol*self.density #Calculated mass of garnet
		molGrt = []

		for i in range(len(self.composition)):
			#Calculate mols of garnet for each component
			massSum = 0
			for j in range(len(self.composition)):
				#Sum up the masses of each component based on mol fraction
				massSum += self.composition[j].weight*self.composition[j].molFrac

			cmpntMol = self.composition[i].molFrac*mass/massSum #Convert the mol fraction to mols
			self.composition[i].mol = cmpntMol

		

	def calcTotMol(self):
		#Not a truly recursive function but close enough
		#Trying to limit our coputation time and ram usage
		#totComposition is another list of garnet endmembers which dont have a mol fraction but a mol total which
		#Is equal to the sum of mols for every shell in all garnets of this size class
		if(self.nextShell == None):
			#Define the basecase where only one shell so total mol is shellMol
			self.totComposition = copy.deepcopy(self.composition) #The only case where totMol can also have a mol fraction
		else:
			self.totComposition = []
			for i in range(len(self.composition)):
				totMol = self.nextShell.totComposition[i].mol + self.composition[i].mol*self.numGrt #calculate the total mol for this component will multiply each shell by the number of garnets in this size class
				thisComposition = GarnetComponentMol(self.composition[i],molIn=totMol) #Mol fraction will be zero
				self.totComposition.append(thisComposition)#Takes total from the next shell and adds it to current shell
	
	def growGarnet(self, compo, growDim):
		#Grows the garnet by growDim with composition of compo
		newShape = copy.deepcopy(self.grtShape)

		#print("Old radius: " + str(newShape.getDim()))

		newShape.growByDim(growDim)

		#print("New radius: " + str(newShape.getDim()))

		newShell = Garnet(newShape,compo,nextGarnet = self)
		return newShell

	def getCompoAsComponentMol(self):
		#Gets the composition of the garnet as a list of ComponentMol
		molList = self.totComposition[0].getComponentMols()

		#print(molList[0].element + ": " + str(molList[0].mol))

		for i in range(1,len(self.composition)):
			#Cycles through every garnet component converts to a list of ComponentMols and sums it with molList
			thisMolList = self.totComposition[i].getComponentMols()

			molList = addComponentList(molList,thisMolList)
		return molList


	def getProfileComp(self):
		#This will return the compositional profile of the garnet as a 2D list of GarnetComponentMol
		if(self.nextShell == None):
			#Define basecase
			compProfile = []
			
		else:
			compProfile = self.nextShell.getProfileComp()
			
		compProfile.append(self.composition)
		return compProfile

	def getProfileX(self):
		#Returns a list of x-values for plotting the profile
		if(self.nextShell == None):
			#Define basecase
			xProfile = []
			
		else:
			xProfile = self.nextShell.getProfileX()
			
		xProfile.append(self.bigAx)
		return xProfile

	def getProfileVol(self):
		#Does the same as the ones above but returns the shell volume as an array
		if(self.nextShell == None):
			#Define basecase
			volProfile = []
			
		else:
			volProfile = self.nextShell.getProfileVol()
			
		volProfile.append(self.shellVol)
		return volProfile


