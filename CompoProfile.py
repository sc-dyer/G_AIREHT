#General class to be extended by the Traverse class and the Model class
#Defines methods that can be used by any garnet composition profile
#Extended by Model and Traverse
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import numpy as np
import pandas as pd
from GeochemConst import GRT_CMPNT, ALM
from scipy.interpolate import interp1d

class CompoProfile:

	def __init__(self):

		#Empty initialization, defines the variables all CompoProfiles should have

		self.x = [] #distance in mm
		#mol fraction
		self.pltColour = 'black'
		self.pltLine = 'None'
		self.pltMark = 'None'
		self.cmpnts = [[],[],[],[]]#Array for mn,mg,ca,fe, each corresponds to a value in CMPNT
		


	def plotCompo(self, key, pltIn,mrkSize):
		#Plots the composition of a specific component in pltIn
		#input key should be one of the CMPNT
		#mrkSize input used for convenience when plotting things on different sized plots
		for i in range(len(GRT_CMPNT)):
			if(key==GRT_CMPNT[i].cation):
				yComp = self.cmpnts[i]
			
		
		pltIn.plot(self.x, yComp, color = self.pltColour, marker = self.pltMark, linestyle = self.pltLine, markersize = mrkSize, linewidth = 2, label = key)
	
	def getCmpnt(self, key):
		#Returns the array of whatever component was input to key
		#This is for user probing
		val = []
		for i in range(len(GRT_CMPNT)):
			if(key==GRT_CMPNT[i].cation):
				val = self.cmpnts[i]
		return val

	def compareProfile(self,compare,wFile, name):
		#Comparison must be another CompoProfile object
		#This method returns multiple values of S (standard error) for each component in the form of Root Mean Squared Error, plus an average value of S. 
		#The unit of S is mol fraction, 
		#Assumes that these are two non-identical arrays CompoProfiles (e.g. a model and a traverse, or two different models)
		#Also assumes that both arrays start from core and go to the rims, does not perform any translations 
		#Will take each x value of comparison and find what the composition should be at that x in "this"
		#Does this by interpolating between the closest two points at each x in compare
		#The intention is to compare a model profile to a half traverse, so it will interpolate values between points on the model for a least square regression

		self.rmse= [] #Standard Error as root mean square error
		self.nrmse = [] #Normalized RMSE
		
		for i in range(len(GRT_CMPNT)):
			thisCmpnt = []
			thatCmpnt = []
			

			for j in range(len(compare.x)):
				compoAtX = self.interpCompoAtX(compare.x[j],GRT_CMPNT[i].cation)
				if compoAtX >= 0:
					thisCmpnt.append(compoAtX)
					thatCmpnt.append(compare.cmpnts[i][j])

			thisCmpnt = np.array(thisCmpnt)
			thatCmpnt = np.array(thatCmpnt)
			rmse = np.sqrt(((thisCmpnt - thatCmpnt)**2).mean()) #calculate root mean square error
			
			nrmse = rmse/(thatCmpnt.mean()) #Normalize to mean of the measured profile, NOTE: Can also use the range -> try both?

			self.rmse.append(rmse)
			self.nrmse.append(nrmse)
		
		#Build next line to write to file in the order of RMSE(CMPNT1),RMSE(CMPNT2)...,RMSE(Average),NRMSE(CMPNT1),NRMSE(CMPNT2)..NRMSE(Average)
		nextLine = name + ","
		for i in range(len(self.rmse)):
			nextLine += str(self.rmse[i]) + ","
		nextLine += str(sum(self.rmse)/len(self.rmse)) + ','

		for i in range(len(self.nrmse)):
			nextLine += str(self.nrmse[i]) + ","
		nrmseAvg = sum(self.nrmse)/len(self.nrmse)
		nextLine += str(nrmseAvg) + '\n'

		

		wFile.write(nextLine)

		return nrmseAvg
		
			
	def interpCompoAtX(self,xVal,key):
		#Linearly interpolate the composition between to points on the model to get the exact value at an x position
		#
		count = 0
		while count < len(self.x) and self.x[count] < xVal:
					count += 1

		compoAtX = -1 
		if count >= 0 and count <len(self.x):
			for i in range(len(GRT_CMPNT)):

				if GRT_CMPNT[i].cation == key:
					rightX = self.x[count]

					leftX = self.x[count-1]
				
					rightCmpnt = self.cmpnts[i][count]
					leftCmpnt = self.cmpnts[i][count-1]

					#linearly interpolate between two points and get the value at xVal
					slope = (rightCmpnt-leftCmpnt)/(rightX-leftX)
					midX = xVal - leftX
					compoAtX = midX*slope + leftCmpnt

		return compoAtX #Returns -1 if the first cell was to the right of the input xVal or if it is attempting to interpolate past the model size


	def scipyInterp(self, kindIn='linear'):
		#Function that initializes numpy arrays for each component and interpolates the values to create continuous functions

		npCmpnts = np.array([np.array(cmpnt) for cmpnt in self.cmpnts]) #Make numpy arrays for each component
		npX = np.array(self.x)
		self.interpComp = []
		#Interpolate each component with npX and store new function in interpComp
		for i in range(len(npCmpnts)):
			thisInterp = interp1d(npX, npCmpnts[i],kind=kindIn)
			self.interpComp.append(thisInterp)


	def plotInterpolants(self, pltIn, interval=0):
		#Plot the interpolated profile as lines
		#Very similar to the function plotAll in Traverse.py
		#Doing this here because I can see utility in all CompoProfiles
		#Will display lines at each interval or non if interval is 0 or less

		colours = ['green','blue','orange','red']
		#pltIn.set_xlim(min(self.x),max(self.x))
		pltAlm = pltIn.twinx()

		pltIn.set_xlabel("Distance (mm)", fontsize = 24)
		pltIn.set_ylabel("X (Ca,Mn,Mg)", fontsize = 24)

		#Uncomment these lines if you want everything on the same scale
		

		pltAlm.set_ylabel("X (Fe)", fontsize = 24, rotation = -90)
		
		
		#Plot each interpolated profile
		maxY = 0
		for i in range(len(GRT_CMPNT)):
			pltColour = colours[i]
			yComp = self.interpComp[i]
			xComp = np.array(self.x)
			if(GRT_CMPNT[i] == ALM):
				pltAlm.plot(xComp, yComp(xComp), color = pltColour, marker = 'None', linestyle = "-", markersize = 7, linewidth = 2, label = GRT_CMPNT[i].cation)
			else:
				if max(self.cmpnts[i]) > maxY:
					maxY = max(self.cmpnts[i])
				pltIn.plot(xComp, yComp(xComp), color = pltColour, marker = 'None', linestyle = "-", markersize = 7, linewidth = 2, label = GRT_CMPNT[i].cation)

		pltIn.legend(loc = 'upper left')
		pltAlm.legend(loc = 'upper right')
		pltIn.xaxis.set_tick_params(which='major', size=10, width=2, direction='in', top='on')
		pltIn.xaxis.set_tick_params(which='minor', size=7, width=2, direction='in', top='on')
		pltIn.yaxis.set_tick_params(which='major', size=10, width=2, direction='in', right=False)
		pltIn.yaxis.set_tick_params(which='minor', size=7, width=2, direction='in', right=False)

		pltAlm.xaxis.set_tick_params(which='major', size=10, width=2, direction='in', top='on')
		pltAlm.xaxis.set_tick_params(which='minor', size=7, width=2, direction='in', top='on')
		pltAlm.yaxis.set_tick_params(which='major', size=10, width=2, direction='in', right=True)
		pltAlm.yaxis.set_tick_params(which='minor', size=7, width=2, direction='in', right=True)

		pltIn.xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
		pltIn.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
		pltIn.yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.1))
		pltIn.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.02))

		pltAlm.xaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
		pltAlm.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.1))
		pltAlm.yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.1))
		pltAlm.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.02))
		
		pltIn.set_ylim(0,0.4)
		pltAlm.set_ylim(0.4,0.9)
		
		#Plot the vertical lines at each interval
		if(interval >= 0):
			numIntervals = int(max(self.x)/interval)
			thisInterval = interval
			#Plot horizontal line at every interval :)
			for i in range(numIntervals):
				
				pltIn.plot([thisInterval,thisInterval],[-100,100],color = 'black', linestyle = "--")
				thisInterval += interval
			#Last plot is usually smaller than the interval
			#So plotting htat line as well
			if(numIntervals*interval < max(self.x)):
				
				pltIn.plot([max(self.x),max(self.x)],[-100,100],color = 'black', linestyle = "--")

	def extrapCore(self, avgInterval, distance):
		#This method assumes the left side of a CompoProfile is the core of a mineral
		#It then averages the values across avgInterval where avgInterval is a number of cells
		#It then extends that average to the left by distance in mm
		#This only needs to add one cell at the beginning of each array and move all others to the right
		#Trying this out to see if extrapolating the core is better than stretching the whole profile
		avgCore = [0,0,0,0]

		for i in range(avgInterval):

			for j in range(len(GRT_CMPNT)):
				avgCore[j] += self.cmpnts[j][i]

		newCmpnt = [[],[],[],[]]
		for i in range(len(GRT_CMPNT)):
			avgCore[i] /= avgInterval
			newCmpnt[i].append(avgCore[i])

		newX = [0]
		
		#Need to move every cell over to the right
		#Setting the first cell as 0 always
		for i in range(len(self.x)):
			newX.append(self.x[i]+distance)
			for j in range(len(GRT_CMPNT)):
				newCmpnt[j].append(self.cmpnts[j][i])

		self.x = newX
		self.cmpnts = newCmpnt

