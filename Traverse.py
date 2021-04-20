#Class to open and manage the measured garnet traverse
#Must be in a csv file with the following header:
#x (mm),Ca,Mg,Fe,Mn 
#The unit for components should be mol fraction
#This class is an extension of CompoProfile
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import numpy as np
import pandas as pd
import easygui

from CompoProfile import CompoProfile
from GeochemConst import GRT_CMPNT, ALM

class Traverse(CompoProfile):

	def __init__(self, fileName):
		#Read the file containg probe data and store it in this object

		CompoProfile.__init__(self)
		self.pltMark = 'o'

		#open the csv file
		try:
			grtFile = open(fileName, 'r')
		except:
			print("No csv file found at location:")
			print(fileName)
			return
		
		grtdf = pd.read_csv(fileName)
		self.x = list(grtdf['x (mm)'])
		for i in range(len(GRT_CMPNT)):
			self.cmpnts[i] = list(grtdf[GRT_CMPNT[i].cation])

		

	def plotAll(self, pltIn):
		#Method to plot all components on one plot
		#Assumes that the Fe component is much higher than the rest, plots it on seperate axis
		colours = ['green','blue','orange','red']
		symbols = ['o','^','s','P']
		pltAlm = pltIn.twinx()
		
		self.travPlot = pltIn #Saves the plot to the object

		#Loop for plotting
		for i in range(len(GRT_CMPNT)):
			self.pltColour = colours[i]
			self.pltMark = symbols[i]
			if(GRT_CMPNT[i] == ALM):
				CompoProfile.plotCompo(self,GRT_CMPNT[i].cation,pltAlm,7)
			else:
				CompoProfile.plotCompo(self,GRT_CMPNT[i].cation,pltIn,7)

		pltIn.set_xlabel("Distance (mm)", fontsize = 24)
		pltIn.set_ylabel("X (Ca,Mn,Mg)", fontsize = 24)

		#Uncomment these lines if you want everything on the same scale
		pltIn.set_ylim(0,0.4)
		pltAlm.set_ylim(0.4,0.9)

		pltAlm.set_ylabel("X (Fe)", fontsize = 24, rotation = -90)
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

		pltIn.xaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
		pltIn.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.2))
		pltIn.yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.1))
		pltIn.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.02))

		pltAlm.xaxis.set_major_locator(mpl.ticker.MultipleLocator(1))
		pltAlm.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.2))
		pltAlm.yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.1))
		pltAlm.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.02))
		#This is to set up the stuff for splitting the plot in half, assuming that you input a full traverse instead of a half traverse
		self.cid = pltIn.figure.canvas.mpl_connect('button_press_event',self.travClick)
		self.splitLine = pltIn.plot([0],[0]) #create an empty line
		self.selectedTrav = self.splitTrav(self.x[0] - 1,False)#Sets the baseline to leftTrav is empty and rightTrav = this. This is basically if you want to input just a half traverse, however it assumes that it is the right half

	def travClick(self, event):
		#When the plot is clicked, draw a vertical line where clicked and store that value as the new 0 for splitting the traverse
		#Will ask for confirmation before drawing and storing the location.
		#It can be changed as many times as desired
		self.splitLine.pop(0).remove()
		newZero = event.xdata
		self.travPlot.autoscale(False)
		self.splitLine = self.travPlot.plot([newZero,newZero],[-100,100],color = 'black',linestyle = '--')
		
		
		title = ""
		msg = "Split traverse at x = " + str(newZero) + "?"
		answer = easygui.boolbox(msg,title,["Yes","No"])
		#answer = input('Split traverse at x = ' + str(newZero) +'? (y/n)')
		if answer:
			msg = "Take the left or right side?"
			selLeft = easygui.boolbox(msg,title,["Left","Right"])
			self.selectedTrav = self.splitTrav(newZero,selLeft)
			plt.draw()
			print("Done, you may now exit this plot or choose a different x location to split the traverse.")

		

	def splitTrav(self,xPos, selectLeft):
		#Method for splitting the traverse into two halves at the inputted xPos
		#Assumes xpos will never exactly equal to an x position on the traverse
		#The two halves are CompoProfile objects with the same data of their respective halves of this Traverse object
		#They will be stored in the travSplit array so that they can be ambiguously referenced. 
		#They will contain a little less info but maintain most of the core stuff

		count = 0
		#Finds the index of the datapoint to the right of the selected x
		while(self.x[count] < xPos):
			count+=1


		xRightIndex = count

		xLeftIndex = count - 1
	
		#initialize travSplit array to hold the two halves and the two sides of the traverse
		self.travSplit= []
		rightTrav = CompoProfile()
		leftTrav = CompoProfile()
		rightTrav.pltMark = 'o'
		leftTrav.pltMark = 'o'
		leftTrav.pltColour = 'blue' #So it can be differentiated on the plot

		#Build the contained arrays
		#First calculate the value at 0 using linear interpolation
		#This allows for modelling from 0
		rightTrav.x.append(0)
		leftTrav.x.append(0)
		for i in range(len(GRT_CMPNT)):
			#Append the composition at 0 to both left and right traverse since they should be the same
			zeroVal = self.interpCompoAtX(xPos,GRT_CMPNT[i].cation)
			rightTrav.cmpnts[i].append(zeroVal)
			leftTrav.cmpnts[i].append(zeroVal)
		for i in range(xRightIndex,len(self.x)):
			
			rightTrav.x.append(self.x[i] - xPos)
			for j in range(len(GRT_CMPNT)):
				rightTrav.cmpnts[j].append(self.cmpnts[j][i])
			

		#Flips the left Traverse
		for i in range(xLeftIndex,-1,-1):
			leftTrav.x.append(xPos - self.x[i])
			for j in range(len(GRT_CMPNT)):
				leftTrav.cmpnts[j].append(self.cmpnts[j][i])


		#Add the two traverses to travSplit
		if len(rightTrav.x) > 0:
			self.travSplit.append(rightTrav)
			if not selectLeft:
				return rightTrav
		if len(leftTrav.x) > 0:
			self.travSplit.append(leftTrav)
			if selectLeft:
				return leftTrav
	



