#This is a class for reading and modelling garnet CSDs
#It can read a blob output file and use Garnet.py to model garnet growth
#Maybe it will do more in the far future but this is the goal for now

from Garnet import Garnet
from GeochemConst import *
from Shape import Shape
from Sphere import Sphere
from Ellipsoid import Ellipsoid
from CompoProfile import CompoProfile
from ComponentMol import *
from GarnetComponentMol import GarnetComponentMol
from SCRIPT_Generator import *

import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import easygui
import math
import copy
import sys
import pdb

NUM_SHELLS = 4000 #This is the number of garnet shells the biggest garnet will have 
#DATABASE = "tcdb55c2_COHmelt.txt"

EQ_PARAM = 0.00000001

CORE_AVG_INDEX = 3 #Number of cells to average for the core composition
class GarnetCSD:

	def __init__(self,blobFileName,garnetProfile,rockCompo, rockVolume, sampleName, numBins = 0):

		self.composition = rockCompo #This is a list of ComponentMol objects that define the rock composition
		self.grtProfile = garnetProfile #This is the CompoProfile object that is a half profile that defines the zoning in the garnet
		self.rockVol = rockVolume
		#Now need to open up the blob file to build the crystal list
		blobDF = pd.read_excel(blobFileName) #Assumes that formatting has not changed from default blob output
		self.name = sampleName
		self.crystalList = [] #Empty list to fill with Shape entries

		blobDF = blobDF.dropna() #Sometimes empty rows at the end mess up calculations
			
		#Choose temperature and pressure range:
		title = "PT range"
		msg = "Please provide min and max temperature and pressure"
		
		fieldNames = ["Tmin","Tmax","Pmin","Pmax"]

		fieldValues = easygui.multenterbox(msg,title, fieldNames)
		# make sure that none of the fields was left blank
		# Gotta make things a little bit idiot proof
		while 1:
			if fieldValues == None: break
			errmsg = ""
			for i in range(len(fieldNames)):
				if fieldValues[i].strip() == "":
					errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
			if errmsg == "": break # no problems found
			fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)
		
	
	
		self.T1 = int(fieldValues[0].strip())
		self.T2 = int(fieldValues[1].strip())
		self.P1 = int(fieldValues[2].strip())
		self.P2 = int(fieldValues[3].strip())



		#Ask user to choose if using spheres or ellipsoids
		msg = "Are garnets spheres or ellipsoids?"
		title = ""
		choices = ["Sphere","Ellipsoid"]
		reply = "Sphere" #Ellipsoid doesnt do much atm
		# reply = easygui.buttonbox(msg,title,choices)
		#reply = "Sphere" #Only works for Spheres right now, need to think about size independent growth of ellipsoids
		if(reply==choices[0]):
			volume = list(blobDF['Volume (mm^3)'])

			for i in range(len(volume)):
				#If spheres, it will recalculate the radius from the volume
				#if not math.isnan(volume[i]):
				thisRad = (volume[i]*3/(4*math.pi))**(1./3)
				self.crystalList.append(Sphere(thisRad))

		elif(reply == choices[1]):
			#If ellipsoid it uses the PEllipsoid data
			# #It should be that rad1 > rad2 > rad3
			# rad1 = list(blobDF['PEllipsoid Rad1 (mm)'])
			# rad2 = list(blobDF['PEllipsoid Rad2 (mm)'])
			# rad3 = list(blobDF['PEllipsoid Rad3 (mm)'])
			
			# for i in range(len(rad1)):
			# 	if not math.isnan(rad1[i]):
			# 		self.crystalList.append(Ellipsoid(rad1[i],rad2[i],rad3[i]))

			#Average out the ratios so all ellipsoids are the same shape and grow with the same dimensions
			avgEllipsoid = self.getAvgEllipsoid(blobDF)
			volume = list(blobDF['Volume (mm^3)'])

			for i in range(len(volume)):
				#Need to rescale the avg ellipsoid to fit the volume of each garnet
				#if not math.isnan(volume[i]):
				ratioAB = avgEllipsoid.aAx/avgEllipsoid.bAx
				ratioBC = avgEllipsoid.bAx/avgEllipsoid.cAx
				thisA = ((3*ratioAB**2*ratioBC*volume[i])/(math.pi*4))**(1/3)
				thisB = thisA/ratioAB
				thisC = thisB/ratioBC
					
				self.crystalList.append(Ellipsoid(thisA,thisB,thisC))
		else:
			print("Error: No option chosen")
			return

		#Okay now we need to stretch the garnet profile to fit with the long dimension of the ellipsoid or the radius of the sphere
		#This is so the profile matches up with the biggest garnet

		self.quickSortCrystals(0,len(self.crystalList)-1)
		self.numCrystals = []

		#Added support for binning but I dont think its needed
		#Still the code is here
		if(numBins > 0):
			#Break things up into seperate bins
			binSize = (self.crystalList[0].getDim() - self.crystalList[len(self.crystalList)-1].getDim())/numBins
			newCrystalList = []
			
			
			hiBin = self.crystalList[0].getDim()
			#make new crystalList with a crystalSize equal to he highest radius in that bin interval
			for i in range(numBins):
				thisInterval = hiBin-i*binSize #each value in bins represent the upperbounds of that bin
				nextInterval = hiBin-(i+1)*binSize
				numInBin = 0
				biggestInBin = Sphere(0)
				for crystal in self.crystalList:
					if crystal.getDim() <= thisInterval and crystal.getDim() > nextInterval:
						numInBin += 1
						if crystal.getDim() > biggestInBin.getDim():
							biggestInBin = crystal
							#the biggest in the bin is the crystal that gets put in the new crystalList
				if numInBin > 0:
					newCrystalList.append(biggestInBin)
					self.numCrystals.append(numInBin)

			self.crystalList = newCrystalList

		travRad = max(self.grtProfile.x) #Radius of the garnet measured in the microprobe profile

		minDiff = sys.float_info.max
		# for i in range (len(self.crystalList) - 1):
		# 	radDiff = self.crystalList[i].getDim()-self.crystalList[i+1].getDim()
		# 	if radDiff > 0:
		# 		minDiff = min(radDiff,minDiff)
		#This makes sure that a shell is not bigger than the difference in radius between any two garnets
		self.shellThick = min(minDiff, self.crystalList[0].getDim()/NUM_SHELLS)

		#Instead of stretching, lets try extrapolating the core inwards:
		radAdd = self.crystalList[0].getDim() - travRad
		msg = "Extrapolate to core or stretch profile?"
		title = ""
		choices = ["Extrapolate","Stretch"]
		reply = easygui.buttonbox(msg,title,choices)
		if radAdd > 0 and reply == choices[0]: #In case the biggest garnet has a radius smaller than traverse length
			self.grtProfile.extrapCore(CORE_AVG_INDEX, radAdd)
		else: 
			scaleFactor = self.crystalList[0].getDim()/travRad #The scaling factor to convert the x values in grtProfile to be the same size as the radius or a axis of ellipsoid
			
			for i in range(len(self.grtProfile.x)): 
				#Rescale x
				self.grtProfile.x[i] = scaleFactor*self.grtProfile.x[i]

		self.grtProfile.scipyInterp() #Initialize the interpolated numpy arrays

		self.garnetList = [] #This is what we will be working with for the most part, it is where all the garnets will grow and be stored


	def quickSortCrystals(self, low, high):
		#Function to sort the garnets by volume
		#Lets do a quick sort because thats fun
		#better to sort biggest to smallest
		if low < high:

			i = low - 1
			pivot = self.crystalList[high].getVolume() #Compare every element in list to the pivot
			
			for j in range(low,high):

				if(self.crystalList[j].getVolume() >= pivot):
					#Increment i by 1 if j is bigger than pivot
					#Then swap element at i and j

					i = i + 1
					self.crystalList[i], self.crystalList[j] = self.crystalList[j], self.crystalList[i]

			#Swap element at high and element at i + 1
			#Putting all elements bigger in volume to left of the element at high
			self.crystalList[i+1], self.crystalList[high] = self.crystalList[high], self.crystalList[i+1]

			pi = i + 1
			
			self.quickSortCrystals(low, pi-1)
			self.quickSortCrystals(pi+1, high)

	def fractionateGarnet(self, outputDir, database, radInterval=0, memorySave = False):
		#A method to fractionate garnet and output the composition at each radInterval
		#Set memorySave to True if you want it to run faster but it wont plot the individual garnets
		writeFile = outputDir + "Output.txt"
		try: 
			outFile = open(writeFile, 'w')
		except:
			print('Problem creating new file')
			exit(0)

		currComposition = self.composition
		therin = ""
		for i in range(len(currComposition)):
			if currComposition[i].mol < 0:
				currComposition[i].mol = 0
			therin += currComposition[i].element.upper() + "({:7.6f})".format(currComposition[i].mol)

		stream = "Initial composition: " + therin
		print(stream)
		outFile.write(stream +"\n")
		self.writeScriptFiles(outputDir, 0, database)

		count = 1
		self.growGarnetShell(memorySave)
		garnetPlotList = [0]
		while(self.garnetList[0].bigAx < self.crystalList[0].getDim()-self.shellThick):
			#Grow garnet until the biggest garnet is one shell away from its max size (or just over one shell away)
			self.growGarnetShell(memorySave)
			
			if(abs(self.garnetList[0].bigAx-radInterval*count)<self.shellThick):
				

				#print("Biggest Radius = " + str(self.garnetList[0].bigAx))
				#print(self.garnetList[0].composition[0].endMember + ": " + str(self.garnetList[0].composition[0].molFrac))
				#print("Number of garnets: " + str(len(self.garnetList)))

				self.calcTotalGarnetMol()
				
				

				self.writeScriptFiles(outputDir, count, database)

				stream = "Stage" + str(count) + ":"
				print(stream)
				outFile.write(stream+"\n")
				stream = str(len(self.garnetList)) + " garnets grown"
				print(stream)
				outFile.write(stream+"\n")
				stream = "Largest radius: " + str(self.garnetList[0].bigAx) + "mm"
				print(stream)
				outFile.write(stream+"\n")
				stream = "Total garnet volume: " + str(self.calcTotVol()) + "mm^3"
				print(stream)
				outFile.write(stream+"\n")

				if garnetPlotList[len(garnetPlotList)-1] != len(self.garnetList) - 1:
					grtIndex = len(self.garnetList)-1
					
					garnetPlotList.append(grtIndex) #To plot these guys later
					
				# for num in garnetPlotList:
				# 	self.plotGarnet(num)
				# plt.show()
				# print("Volumes are:")
				# for garn in self.garnetList:
				# 	print(garn.totVol)
				# print("Outer Shell:")
				# for garn in self.garnetList:
				# 	print(str(garn.composition[0].molFrac) + "," + str(garn.composition[1].molFrac) + "," + str(garn.composition[2].molFrac) + "," + str(garn.composition[3].molFrac))
				
				# print("Radius:")
				# for garn in self.garnetList:
				# 	print(garn.bigAx)
				# print("Mol Sum:")
				# for garn in self.garnetList:
				# 	thisCompo = garn.getCompoAsComponentMol()
				# 	compoString = ""
				# 	for cmpnt in thisCompo:
				# 		compoString += cmpnt.element +": " + str(cmpnt.mol) + ", "
				# 	print(compoString)

				# for i in range(len(self.totGarnetMol)):
				# 	print("Total mol of " + self.totGarnetMol[i].element + " = " + str(self.totGarnetMol[i].mol))

				count += 1

		self.calcTotalGarnetMol()		
		self.writeScriptFiles(outputDir, count, database)
		stream = "Stage" + str(count) + ":"
		print(stream)
		outFile.write(stream+"\n")
		stream = str(len(self.garnetList)) + " garnets grown"
		print(stream)
		outFile.write(stream+"\n")
		stream = "Largest radius: " + str(self.garnetList[0].bigAx) + "mm"
		print(stream)
		outFile.write(stream+"\n")
		stream = "Total garnet volume: " + str(self.calcTotVol()) + "mm^3"
		print(stream)
		outFile.write(stream+"\n")

		# print("Volumes are:")
		# for garn in self.garnetList:
		# 	print(garn.totVol)
		# print("Outer Shell:")
		# for garn in self.garnetList:
		# 	print(str(garn.composition[0].molFrac) + "," + str(garn.composition[1].molFrac) + "," + str(garn.composition[2].molFrac) + "," + str(garn.composition[3].molFrac))
				
		# print("Radius:")
		# for garn in self.garnetList:
		# 	print(garn.bigAx)
		# print("Mol Sum:")
		# for garn in self.garnetList:
		# 	thisCompo = garn.getCompoAsComponentMol()
		# 	compoString = ""
		# 	for cmpnt in thisCompo:
		# 		compoString += cmpnt.element +": " + str(cmpnt.mol) + ", "
		# 	print(compoString)
		# for i in range(len(self.totGarnetMol)):
		# 			print("Total mol of " + self.totGarnetMol[i].element + " = " + str(self.totGarnetMol[i].mol))

		
		stream = "Done growing garnets"
		print(stream)
		outFile.write(stream)
		outFile.close()
		if not memorySave:
			for num in garnetPlotList:
				self.plotGarnet(num, outputDir)

		# print("\n\n\n")
		# print("Verifying garnet sizes:")
		# for i in range(len(self.crystalList)):
		# 	finalSize = self.garnetList[i].bigAx #+ self.shellThick
		# 	finalVol = (finalSize**3)*(4/3)*math.pi
			
		# 	if finalSize - self.crystalList[i].getDim() > EQ_PARAM:
		# 		print("Garnet " + str(i+1) + " is too big")
		# 		print("Rad diff = " + str(finalSize- self.crystalList[i].getDim()))
		# 		print("Vol diff = " + str(finalVol-self.crystalList[i].getVolume()))
		# 	elif finalSize - self.crystalList[i].getDim() < EQ_PARAM:
		# 		print("Garnet " + str(i + 1) + " is too small")
		# 		print("Rad diff = " + str(self.crystalList[i].getDim()-finalSize))
		# 		print("Vol diff = " + str(self.crystalList[i].getVolume() - finalVol))
		# 	print("\n")

	def growGarnetShell(self, memorySave):
		#Function to grow an additional shell of garnet
		#Will add a new garnet once the radius difference between the last garnet and the next one is sufficient
		

		if len(self.garnetList) == 0: #Initialize first garnet
			firstShellCompo = self.getShellCompo(self.shellThick,0)
			self.shellCount = 0 #Number of shells in the biggest garnet
			if len(self.numCrystals) == 0:
				binNum = 1 
			else:
				binNum = self.numCrystals[0]
			self.nucleateGarnet(self.crystalList[0],firstShellCompo,self.shellThick,binNum)
			# print("Shell Thickness = " + str(self.shellThick))
			print("First garnet nucleated")

		else:
			#First calculate the next composition interval
			biggestRad = self.garnetList[0].bigAx

			#This condition is part of the nucleation parameter
			#Ensures to only add shellExcess when about to nucleate
			#This way we can add shellThick to the nucleus and all the crystals and maintain the appropriate 
			#size ratios
			if(self.shellCount != self.shellsAtNextGrt):
				nextShellRad = biggestRad + self.shellThick
				thisShellThick = self.shellThick
			else:
				nextShellRad = biggestRad + self.shellExcess
				thisShellThick = self.shellExcess
				

			nextShellCompo = self.getShellCompo(nextShellRad,biggestRad)
			#Grow each garnet with composition nextShellCompo and thickness of thisShellThick
			for i in range(len(self.garnetList)):
				self.garnetList[i] = self.garnetList[i].growGarnet(nextShellCompo, thisShellThick)
				if memorySave and self.garnetList[i].nextShell != None:
					del self.garnetList[i].nextShell

		
			#This nucleates new garnet when needed:
			if(self.shellCount > self.shellsAtNextGrt): #This difference shouldnt be greater than 2

					if len(self.numCrystals) == 0:
						binNum = 1 
					else:
						binNum = self.numCrystals[0]
					self.nucleateGarnet(self.crystalList[len(self.garnetList)],nextShellCompo, self.shellThick, binNum)
					if self.shellCount == self.shellsAtNextGrt:
						# print("self.shellCount == self.shellsAtNextGrt")
						self.growGarnetShell(memorySave)


		self.shellCount +=1


	def getShellCompo(self,xHi,xLo):
		#Gets the average composition of the profile between xHi and xLo and returns it
		#As a list of GarnetComponentMols
		shellCompo = []

		for i in range(len(self.grtProfile.interpComp)):
			thisProfile = self.grtProfile.interpComp[i]
			if(xHi <= self.crystalList[0].getDim()):
				shellX = (thisProfile(xHi) + thisProfile(xLo))/2
			else:
				shellX = (thisProfile(self.crystalList[0].getDim()) + thisProfile(xLo))/2
			shellCompo.append(GarnetComponentMol(GRT_CMPNT[i],shellX))
		return shellCompo



	def nucleateGarnet(self, garnetShape,garnetCompo,firstThick,grtsInBin):
		#Function to nucleate a new garnet with the same aspect ratio of garnet shape

		rescaleFactor = garnetShape.getDim()/firstThick #Determines the scaling factor required to maintain the aspect ratio of a garnet with dimension of shell thickness
		nucleusShape = garnetShape.getRescale(rescaleFactor)

		nucleus = Garnet(nucleusShape, garnetCompo,numGrt = grtsInBin)
		if(len(self.garnetList) > 0):
			lastGrt = len(self.garnetList)-1
			verifyDiff = self.crystalList[lastGrt].getDim()-self.crystalList[lastGrt+1].getDim()
			actualDiff = self.garnetList[lastGrt].bigAx - nucleus.bigAx
			# print("Difference should be " + str(verifyDiff) + " is actually " + str(actualDiff))
		#Determine nucleation parameters for NEXT garnet
		if(len(self.crystalList) > len(self.garnetList)+1):
			thisGrt = len(self.garnetList)
			
			nextGrt = thisGrt + 1
			radDiff = self.crystalList[thisGrt].getDim()-self.crystalList[nextGrt].getDim()
			if radDiff >= self.shellThick:
				self.shellsAtNextGrt= int(radDiff/self.shellThick) + self.shellCount #This is the number of shells the biggest garnet when the next garnet nucleates (minus 1)
				self.shellExcess = radDiff%self.shellThick #This is the thickness of that extra shell
			else:
				while abs(radDiff) <= EQ_PARAM:
					#Nucleates all garnets that have the same size
					# print("Same radius")
					self.garnetList.append(nucleus)
					garnetShape = self.crystalList[len(self.garnetList)]
					rescaleFactor = garnetShape.getDim()/firstThick #Determines the scaling factor required to maintain the aspect ratio of a garnet with dimension of shell thickness
					nucleusShape = garnetShape.getRescale(rescaleFactor)
					nucleus = Garnet(nucleusShape, garnetCompo,numGrt = grtsInBin)

					lastGrt = len(self.garnetList)-1
					verifyDiff = self.crystalList[lastGrt].getDim()-self.crystalList[lastGrt+1].getDim()
					actualDiff = self.garnetList[lastGrt].bigAx - nucleus.bigAx
					# print("Difference should be " + str(verifyDiff) + " is actually " + str(actualDiff))

					if(len(self.crystalList) > len(self.garnetList)+1):
						thisGrt = len(self.garnetList)
						nextGrt = thisGrt + 1
						radDiff = self.crystalList[thisGrt].getDim()-self.crystalList[nextGrt].getDim()

						self.shellsAtNextGrt= int(radDiff/self.shellThick) + self.shellCount #This is the number of shells the biggest garnet when the next garnet nucleates (minus 1)
						self.shellExcess = radDiff%self.shellThick #This is the thickness of that extra shell
					else:
						self.shellsAtNextGrt = NUM_SHELLS + len(self.garnetList) + 1 #Makes sure no more nucleation occurs
						self.shellExcess = 0
						radDiff = sys.float_info.max
				while radDiff < nucleus.bigAx:
					#For instances when the difference between this garnet and the next is smaller than the thickness of the shell
					#Nucleates the next garnet with a smaller initial shell size
					#pdb.set_trace()
					# print("Nucleus radius = " + str(nucleus.bigAx))
					# print("Next garnet radius difference = " + str(radDiff))

					self.garnetList.append(nucleus)
					firstThick = nucleus.bigAx - radDiff
					# print("Nucleus radius = " + str(firstThick))
					garnetShape = self.crystalList[len(self.garnetList)]
					rescaleFactor = garnetShape.getDim()/firstThick #Determines the scaling factor required to maintain the aspect ratio of a garnet with dimension of shell thickness
					nucleusShape = garnetShape.getRescale(rescaleFactor)
					nucleus = Garnet(nucleusShape, garnetCompo,numGrt = grtsInBin)

					lastGrt = len(self.garnetList)-1
					verifyDiff = self.crystalList[lastGrt].getDim()-self.crystalList[lastGrt+1].getDim()
					actualDiff = self.garnetList[lastGrt].bigAx - nucleus.bigAx
					# print("Difference should be " + str(verifyDiff) + " is actually " + str(actualDiff))

					if(len(self.crystalList) > len(self.garnetList)+1):
						thisGrt = len(self.garnetList)
						nextGrt = thisGrt + 1
						radDiff = self.crystalList[thisGrt].getDim()-self.crystalList[nextGrt].getDim()
						# print("Next garnet radius difference = " + str(radDiff))
						self.shellsAtNextGrt= int((radDiff-firstThick)/self.shellThick) + self.shellCount + 1#This is the number of shells the biggest garnet when the next garnet nucleates (minus 1)
						self.shellExcess = (radDiff-firstThick)%self.shellThick #This is the thickness of that extra shell
					else:
						self.shellsAtNextGrt = NUM_SHELLS + len(self.garnetList) + 1 #Makes sure no more nucleation occurs
						self.shellExcess = 0
						radDiff = sys.float_info.max
			# print("ShellCount = " + str(self.shellCount))
			# print("ShellsAtNextGrt = " + str(self.shellsAtNextGrt))
			# print("\n")
		else:
			self.shellsAtNextGrt = NUM_SHELLS + len(self.garnetList) + 1 #Makes sure no more nucleation occurs
			self.shellExcess = 0


		self.garnetList.append(nucleus)



	def calcTotalGarnetMol(self):
		#Calculate total mols of all garnet components
		#This will return an array of ComponentMol not GarnetComponentMol
		self.totGarnetMol = copy.deepcopy(self.garnetList[0].getCompoAsComponentMol()) #Get the composition of the first garnet


		for i in range(1,len(self.garnetList)):
			#Add each garnet composition to totGarnetMol

			thisGarnetCompo = self.garnetList[i].getCompoAsComponentMol()
			self.totGarnetMol = addComponentList(self.totGarnetMol,thisGarnetCompo)
			



	def writeScriptFiles(self, thisDir, fracStep, database):
		#Write script files for the current composition
		#For isopleths, it uses the composition of the next biggest shell

		#First get the composition of the next shell, this is what will be written into the script file
		if len(self.garnetList) == 0: 
			biggestRad = 0
			currComposition = self.composition
		else:
			biggestRad = self.garnetList[0].bigAx
			currComposition = subComponentList(self.composition, self.totGarnetMol)
		nextShellRad = biggestRad + self.shellThick
		if nextShellRad > self.crystalList[0].getDim():
			nextShellRad = self.crystalList[0].getDim()
		nextShellCompo = self.getShellCompo(nextShellRad,biggestRad)
		

		# print("Total Composition:")
		# compoString = ""
		# for cmpnt in self.composition:
		# 	compoString += cmpnt.element +": " + str(cmpnt.mol) + ", "
		# print(compoString)
		# compoString = ""
		# print("After removal of garnet:")
		# for cmpnt in currComposition:
		# 	compoString += cmpnt.element +": " + str(cmpnt.mol) + ", "
		# print(compoString)

		iterName = self.name + '_Stage{:02d}'.format(fracStep)
		#Generate the therin composition string
		therin = ""
		for i in range(len(currComposition)):
			if currComposition[i].mol < 0:
				currComposition[i].mol = 0
			therin += currComposition[i].element.upper() + "({:7.6f})".format(currComposition[i].mol)

		phaseScript(therin,self.P1,self.P2,self.T1,self.T2,iterName,thisDir,database)

		#Now generate the isopleth script files
		for i in range(len(nextShellCompo)):
			componentName = nextShellCompo[i].endMember
			targetCompo = nextShellCompo[i].molFrac
			#Calculate range of mol fraction +- 10% of the target composition
			compoStep = round_sig(targetCompo*0.05)
			compoStart = round_sig(targetCompo - 2*compoStep)
			compoEnd =round_sig( targetCompo + 2*compoStep)
			isoScript(therin, self.P1, self.P2, self.T1, self.T2, iterName, thisDir, database,"GARNET", componentName,compoStart, compoEnd,compoStep)

		#and now volume
		grtVol = self.calcTotVol()/(10*10*10) #converted to cm^3
		#shellVol = self.calcShellVol()/(10*10*10)
		if grtVol > 0:
			volStep = round_sig(grtVol*0.05)
			volStart = round_sig(grtVol - 2*volStep)
			volEnd = round_sig(grtVol + 2*volStep)
			volScript(therin, self.P1, self.P2, self.T1, self.T2,iterName, thisDir,database, "GARNET", volStart,volEnd, volStep,"_vol")

			#shellStep = round_sig(shellVol*0.5)
			#shellStart = 0
			#shellEnd = round_sig(shellStep*2)
			#volScript(therin,self.P1,self.P2,self.T1,self.T2,iterName,thisDir,database,"GARNET",shellStart,shellEnd,shellStep,"_shellVol")

	def getAvgEllipsoid(self, blobIn):
		#Takes the blobIn as a pandas table
		#Average the aspect ratios of all the ellipsoids and returns the average ellipsoid
		#This way we can work with a "standardized" ellipsoid that grows the same way for every garnet
		rad1 = blobIn['PEllipsoid Rad1 (mm)'].to_numpy()
		rad2 = blobIn['PEllipsoid Rad2 (mm)'].to_numpy()
		rad3 = blobIn['PEllipsoid Rad3 (mm)'].to_numpy()

		#ratio12 = rad1/rad2 ratio23 = rad2/rad3 ratio12*ratio23 = rad1/rad3
		ratio12 = rad1/rad2
		ratio23 = rad2/rad3

		avgR12 = np.average(ratio12)
		avgR23 = np.average(ratio23)

		#Volume of ellipsoid doesnt matter so set rad3 = 1
		modelR2 = avgR23
		modelR1 = avgR12*modelR2
		modelEllip = Ellipsoid(modelR1,modelR2,1)

		return modelEllip


	def plotGarnet(self, grtNum, saveDir):
		#Plots an individual garnet composition
		#Will plot mol fraction (fracAx), mols (molAx), and volume (volAx)
		#Wont show the plot right away so that multiple garnets can be shown at the same time

		thisGrt = self.garnetList[grtNum]
		thisCompo = thisGrt.getProfileComp()
		thisX = thisGrt.getProfileX() 
		thisVol = thisGrt.getProfileVol()

		if len(thisX) == len(thisCompo): #verify these operations were performed correctly when retrieving the values
			fracList =[]
			molList = []
			for elem in GRT_CMPNT:
				fracList.append([])
				molList.append([])
			for i in range (len(thisCompo)):
				
			
				for j in range(len(thisCompo[i])):

						fracList[j].append(thisCompo[i][j].molFrac)
						molList[j].append(thisCompo[i][j].mol)
				
			thisFig =plt.figure(figsize =(16,10))
			figName = "Garnet" + str(grtNum+1)

			thisFig.suptitle(figName, fontsize=16)

			fracAx = thisFig.add_subplot(311)
			colours = ['green','blue','orange','red']

			#Set xlimit of every plot to the size of the biggest garnet, so it is easier to compare
			biggestRad = self.garnetList[0].bigAx	
			fracAx.set_xlim(0,biggestRad)

			fracAlm = fracAx.twinx()

			fracAx.set_xlabel("x (mm)")
			fracAx.set_ylabel("X (Ca,Mn,Mg)")

			fracAlm.set_ylabel("X (Fe)")
			
			molAx = thisFig.add_subplot(312)
			molAx.set_xlim(0,biggestRad)
			molAlm = molAx.twinx()

			molAx.set_xlabel("x (mm)")
			molAx.set_ylabel("mol (Ca,Mn,Mg)")
			molAlm.set_ylabel("mol (Fe)")

			volAx = thisFig.add_subplot(313)
			volAx.set_xlim(0,biggestRad)
			volAx.set_xlabel("x (mm)")
			volAx.set_ylabel("Shell Volume (mm$^3$)")


			#Plot each interpolated profile
			for i in range(len(GRT_CMPNT)):
				pltColour = colours[i]
				yFrac = fracList[i]
				yMol = molList[i]
				xComp = thisX
				if(GRT_CMPNT[i] == ALM):
					fracAlm.plot(xComp, yFrac, color = pltColour, marker = 'None', linestyle = "-", markersize = 7, linewidth = 1, label = GRT_CMPNT[i].cation)
					molAlm.plot(xComp, yMol, color = pltColour, marker = 'None', linestyle = "-", markersize = 7, linewidth = 1, label = GRT_CMPNT[i].cation)
				else:
					fracAx.plot(xComp, yFrac, color = pltColour, marker = 'None', linestyle = "-", markersize = 7, linewidth = 1, label = GRT_CMPNT[i].cation)
					molAx.plot(xComp, yMol, color = pltColour, marker = 'None', linestyle = "-", markersize = 7, linewidth = 1, label = GRT_CMPNT[i].cation)

			volAx.plot(thisX, thisVol, color = 'black', marker = 'None', linestyle = '-', markersize = 7, linewidth = 1, label = "Volume")

			fracAx.legend(fontsize = 14, loc = 'upper left')
			fracAlm.legend(fontsize = 14, loc = 'upper right')
			molAx.legend(fontsize = 14, loc = 'upper left')
			molAlm.legend(fontsize = 14, loc = 'upper right')
			
			figName += ".svg"
			thisFig.show()
			thisFig.savefig(saveDir + figName)
		else:
			print("Error with plotting garnet compositions")

	def calcTotVol(self):
		#Returns the total volume of garnet so far

		totVolCSD = 0
		for grt in self.garnetList:
			totVolCSD += grt.totVol*grt.numGrt 

		return totVolCSD

	def calcShellVol(self):
		#Returns volume of just the outer shell of garnets so far

		shellVolCSD = 0
		for grt in self.garnetList:
			shellVolCSD += grt.shellVol*grt.numGrt

		return shellVolCSD

def round_sig(x, sig=3):
   	return round(x, sig-int(math.floor(math.log10(abs(x))))-1)





