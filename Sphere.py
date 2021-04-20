#Its a sphere
#A possible shape for a garnet
#Has a volume and a radius
from Ellipsoid import Ellipsoid
import math

class Sphere(Ellipsoid):
#Special case of ellipsoid where a,b,c = rad
	def __init__(self,rad):
		self.radius = rad
		super().__init__(rad,rad,rad)

#Everything below removed since sphere extends ellipsoid now		
		#self.calcVol()

	#def calcVol(self):
		#Calculates the volume of the sphere
		#vol = 4/3*math.pi*self.radius**3
		#self.volume = vol

	# def getVolume(self):
	# 	return self.volume

	# def getDim(self):
	# 	return self.radius

	# def growByDim(self, dim):
	# 	#Increment radius by dim
	# 	self.radius += dim
	# 	self.calcVol()

	def calcRad(self):
	 	#working backwards to get radius from volume
	 	super.calcABC()
	 	self.radius = self.aAx
	

	# def growByVol(self, vol):
	# 	#Increment volume by vol
	# 	self.volume += vol
	# 	self.calcRad()