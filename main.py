from Garnet import Garnet
from GarnetCSD import GarnetCSD,NUM_SHELLS
from Sphere import Sphere
from Ellipsoid import Ellipsoid
from GeochemConst import *
from ComponentMol import *
from GarnetComponentMol import GarnetComponentMol
from Traverse import Traverse
from CompoProfile import CompoProfile
from SampleComp import SampleComp

import easygui
import os
import matplotlib.pyplot as plt
import pandas as pd
import re
import sys

isDebug = False

sys.setrecursionlimit(NUM_SHELLS*3)
#print(sys.getrecursionlimit())
SAMPLE_COL = "Name"
#Begin the actual program
#Start by getting the traverse data:

print('Choose the csv file for the traverse')
#travIn = input('Enter the name and directory of the csv file for the traverse: ')
if isDebug:
	#travIn = "./TestData/TestTrav.csv"
	travIn = easygui.fileopenbox('Choose the csv file for the traverse',default="/home/sabastien/Documents/Carleton/Probe/Central sections/Garnet_CSVs/*.csv")
else:
	travIn = easygui.fileopenbox('Choose the csv file for the traverse',default="*.csv")

if travIn != None:
	travIn = travIn.strip()
	travIn = travIn.strip('"')



	#gen = int(input("Enter the garnet generation to plot: "))
	plt.rcParams['font.size'] = 18
	plt.rcParams['axes.linewidth'] = 2
	#Make and plot the traverses
	trav = Traverse(travIn)
	travFig = plt.figure(figsize = (12,8))
	travAx = travFig.add_subplot()

	trav.plotAll(travAx)
	print("Please click on the plot where you want to split it in half, if you are satisfied with the plot as is, exit the window")
	plt.show()

	#I am going to try to make this program take a geochemical csv file like THERIN_Generator, then allow the user to select from list
	if isDebug:
		fileIn = "./TestData/TestGeochem.csv"
	else:
		fileIn = easygui.fileopenbox('Select the csv file where the geochemical data is stored',default="*.csv")
	
	geochemDF = pd.read_csv(fileIn)

	samples = list(geochemDF[SAMPLE_COL])

	msg = "Select the sample to use"
	title = "Sample selection"
	chosenSample = easygui.choicebox(msg,title,samples)

	presentCmpnts = []
	wtCompo = []
	#Now should know which row to use
	selectedRow = geochemDF[geochemDF["Name"] == chosenSample]#Not sure if there is a better way
	
	for i in range(len(COMPONENTS)):
		if not(COMPONENTS[i].element == C.element or COMPONENTS[i].element == H.element):
			
			try:
				wtCompo.append(float(selectedRow[COMPONENTS[i].oxName]))
				presentCmpnts.append(COMPONENTS[i])
			except:
				print("Component " + COMPONENTS[i].oxName + " not present in file" )
	


	# #Ask if user wishes to bin the sample
	# msg = "Do you wish to bin the CSD?"
	# title = ""
	# choices = ["Yes","No"]
	# isBinned = easygui.ynbox(msg,title,choices)
	isBinned = False
	#Okay now we can have a thing for user input
	if isDebug:
		volume = 0.075
		density = 4.19
		database = "tcdb"
		radInterval = 0.3
	else:
		title = "User Input"
		msg = "Please provide the following information"
		if isBinned:
			lastField = "Number of bins"
		else:
			lastField = "Radius Interval (mm)"
		fieldNames = ["Scanned Volume (cm^3)","Density (g/cm^3)","Database Filename",lastField]

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
		
	
	
		volume = float(fieldValues[0].strip())
		density = float(fieldValues[1].strip())
		database = fieldValues[2].strip()
	
		radInterval = float(fieldValues[3].strip())
	
	name = chosenSample

	
	mass = density*volume

	sampleCompo = SampleComp(name,wtCompo,presentCmpnts,mass)

	redCo2 = True
	h2o = 100
	co2 = 100

	sampleCompo.calcO2(redCo2,co2,h2o)
	composition = sampleCompo.molArray
	



	#Code for selecting the blob file
	if isDebug:
		#blobIn = "./TestData/TestBlob.xlsx"
		blobIn = easygui.fileopenbox("Choose the xlsx file that the blob data is stored in",default="/home/sabastien/Documents/Carleton/Blob Output/XLSX files/*.xlsx")
		outputDir = "./TestData/TestOutputC"
	else:
		blobIn = easygui.fileopenbox("Choose the xlsx file that the blob data is stored in",default="*.xlsx")
		outputDir = easygui.diropenbox("Select the directory to save output")
	if os.name == 'nt':#PC
		outputDir += "\\"
   
	else:#Mac or linux
		outputDir += "/"
    
	if blobIn != None:



		#now make the csd
		scannedCSD = GarnetCSD(blobIn,trav.selectedTrav,composition,volume, name)
		msg = "Do you wish to save memory by not plotting the individual garnet compositions? WARNING: Selecting No will cause the program to use a lot of RAM for samples with a lot of garnets"
		title = ""
		choices = ["Yes","No"]
		saveMem = easygui.ynbox(msg,title,choices)
		#saveMem = True
		interpFig = plt.figure(figsize = (12,8))
		interpAx = interpFig.add_subplot()

		trav.selectedTrav.plotInterpolants(interpAx,radInterval)
		
		plt.show()
		check = easygui.ynbox("Continue?",title,choices)
		if check:
			scannedCSD.fractionateGarnet(outputDir, database,radInterval, saveMem)

			interpFig.savefig(outputDir + "OriginalTrav.svg")
			plt.show()
	else:
		print("No blob file chosen, ending program...")
else:
	print("No csv file chosen, ending program...")
	