#Abstract class definition of a shape
#Garnets can have a shape (sphere or ellipsoid)
#All shapes have volume and surface area but I am excluding SA for now

from abc import ABC, abstractmethod 

class Shape(ABC):

	def getVolume(self):
		pass

	def calcVol(self):
		pass

	def getDim(self):
		#mehod for getting a defining dimension
		pass

	def growByDim(self, dim):
		#Method to grow the shape by incrementing the defining dimension by dim
		#This will maintain all aspect ratios
		pass

	def growByVol(self, vol):
		#Method to grow shape by incrementing the volume by vol
		#This will maintain all aspect ratios
		pass