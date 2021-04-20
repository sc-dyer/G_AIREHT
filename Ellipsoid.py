#Its an ellipsoid
#A possible shape for a garnet
#Has a,b, and c axis
from Shape import Shape
import math

class Ellipsoid(Shape):

	def __init__(self,a,b,c):
		#A,B,C are the semi-axes that define the ellipsoid
		#For garnets, aAx will be the one used for shell thickness
		self.aAx = a
		self.bAx = b
		self.cAx = c
		self.calcVol()

	def calcVol(self):
		#Calculate volume of ellipsoid
		vol = 4/3*math.pi*self.aAx*self.bAx*self.cAx
		self.volume = vol

	def getVolume(self):
		return self.volume

	def getDim(self):
		return self.aAx

	def calcABC(self):
		#Going backwards from volume but assuming aspect ratio is the same
		ba = self.bAx/self.aAx
		ca = self.cAx/self.aAx
		newA = (self.volume*3/(4*math.pi*ba*ca))**(1./3)
		self.aAx = newA
		self.bAx =newA*ba 
		self.cAx = newA*ca

	def growByDim(self,dim):
		
		#Gotta define ratios first
		ba = self.bAx/self.aAx
		ca = self.cAx/self.aAx

		#Maintain the aspect ratio of the ellipsoid
		self.aAx += dim
		self.bAx += dim*ba
		self.cAx += dim*ca
		self.calcVol()

	def growByVol(self, vol):
		#Increment volume by vol
		self.volume += vol
		self.calcABC()

	def getRescale(self, factor):
		#Returns a new ellipsoid that is the same as this one but rescaled by "factor"
		ba = self.bAx/self.aAx
		ca = self.cAx/self.aAx
		newA = self.aAx/factor
		newB = newA*ba
		newC = newA*ca 		
		newEllipsoid = Ellipsoid(newA, newB, newC)

		return newEllipsoid


