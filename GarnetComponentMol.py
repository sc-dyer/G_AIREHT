#This is like ComponentMol but instead its for the GarnetComponents
#There is probably a more polymorphic way to implement these but this works for now
#By for now I mean forever
from GarnetComponent import GarnetComponent
from ComponentMol import *
import copy

class GarnetComponentMol(GarnetComponent):

	def __init__(self,grtIn, xIn=0, molIn=0):
		#Takes all properties from grtIn and assigns an amount of mols and a mol fraction
		grtCopy = copy.deepcopy(grtIn)
		super().__init__(grtCopy.cation,grtCopy.endMember,grtCopy.formula)
		self.molFrac = xIn #This should add to 1 with the other garnet components
		self.mol = molIn

	def getComponentMols(self):
		#Method that returns a list of ComponentMols which make up the GarnetComponentMol
		componentList = []

		for i in range(len(self.formula)):
			#For each component in the formula, multiply it by the mol of the garnetComponent
			mol = self.formula[i].mol*self.mol
			componentList.append(ComponentMol(self.formula[i],mol))
			
		return componentList
