#Class for defining garnet components
from ComponentMol import ComponentMol

class GarnetComponent:

	def __init__(self,catName,endMemName, formulaList):
		#A garnet component is an endmember, it has a cation assuming form X3Al2Si3O12 where X is the cation
		#It also has an endmember name like spss, py, etc
		#The formula is a list of components where the amount of mol is equal to the amount in the formula
		self.cation = catName
		self.endMember = endMemName #This should be the same as the endmember code in theriak-domino
		self.formula = formulaList #This is a list of ComponentMols

		self.weight = 0
		#Calculate molar weight based on the formula
		for i in range(len(self.formula)):
			component = self.formula[i]
			compWeight = component.weight*component.mol
			self.weight += compWeight