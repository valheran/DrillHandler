
import math
import csv
import numpy as np
import collections
import bisect
# planned sequence of events
#1 read in data from file splitting out by hole id
# make a dictionary of collars using holeid as key
# for each hole make a survey dictionary. Perhaps this can actually done by making a dictionary using hole id as key
#and a list of [collar, survey] as the items
#2 make the trace coordinates by iterating the traceMaker class over the drillhole dictionary, returning a
#sequence of x,y,z co-ords for each hole
#3 using these coords, create line segments in a shape file to represent the trace in plan view
#Then need to figure out how to add log data as attributes- perhaps by breaking down the hole into more segments



class traceMaker:
    #creates a series of x,y,z coordinates from an intial collar location and a series of downhole surveys
    #the resultiing dictionary uses downhole length as its key
    
    def __init__(self, collar, survey):
        self.Xo = float(collar[0])
        self.Yo = float(collar[1])
        self.Zo = float(collar[2])
        self.survey = survey
        self.temp={0:[self.Xo, self.Yo, self.Zo]} #sets up the collar coordinate
       # self.results = collections.OrderedDict()
        #create the list of 3D co-ordinates downhole
        
        for keys in survey:
            
            slist=survey[keys]
            #print slist
            #print type(slist[0])
            sampfrom = float(slist[0])
            sampto=float(slist[1])
            dip = float(slist[2])
            azi = float(slist[3])
            coords = self.calc(sampfrom, sampto, dip, azi)
            self.Xo=coords[0]
            self.Yo=coords[1]
            self.Zo=coords[2]
            #reskey = int(keys)+1 #to keep the result keys one interger ahead as 0 is already been used when initialised this is from old version
            #that didnt use downhole length as the key
            self.temp[sampto] = coords
            #print coords
		#convert into an ordered dictionary (sequential downhole depth) to help with searchability
        self.results = collections.OrderedDict(sorted(self.temp.items()))

    def calc(self, sampfrom, sampto, dip, azi):
        #calculates the coordinates at the sampto downhole length using the previous coord as a start poit
        #ie the sampfrom location
        rdip = math.radians(dip)
        razi = math.radians(azi)

        downholelength = sampto - sampfrom
        segadvance = math.cos(rdip) * downholelength
        X = self.Xo + math.sin(razi) * segadvance
        Y = self.Yo + math.cos(razi) * segadvance
        Z = self.Zo - math.sin(rdip) * downholelength
        coords = [X,Y,Z]
        return coords
#function to build the traces from coords
def geomBuilder(holedat):
    nodestring =[]
    for index in holedat:
        coordsXYZ=holedat[index]
        node =QgsPoint(coordsXYZ[0], coordsXYZ[1])
        nodestring.append(node)
        
    drilltrace = QgsGeometry.fromPolyline(nodestring)
    return drilltrace    
    
    
 #read collar and survey files into drillholes dict file
def readFromFile():
    collars = []
    drillholes = {}
    with open(r'H:\Scripting\collars.csv', 'r') as col:
        next(col)
        readercol=csv.reader(col)
            
        for holeid,x,y,z,EOH in readercol:
            
            collars=[x,y,z,EOH]
            a = holeid
            i=0
                    
            with open(r'H:\Scripting\surveys.csv', 'r') as sur:
                next(sur)
                readersur = csv.reader(sur)
                surveys={}
                for hole, sampfrom, sampto,dip,azi in readersur:
                    if hole ==a:
                        surv = [sampfrom, sampto, dip, azi]
                        surveys[i]=surv
                        i=i+1
                #print"survey from file", surveys
                desurvey = densifySurvey(surveys)    #run desurvey/densify algorithm
                #print "survey", surveys
                #print "desurvey",desurvey
                drillholes[holeid] = [collars, desurvey] 
    #print drillholes
    return drillholes
"""collar1 =[1,1,100]
survey1 = {1:[0,30,45, 45], 2:[30,60,45, 45], 3:[60,90,45, 45]} 
collar2 =[20,10,100]
survey2 = {1:[0,30,45, 45], 2:[30,60,45, 45], 3:[60,90,45, 45]} 
collar3 =[0,20,100]
survey3 = {1:[0,30,45, 45], 2:[30,60,45, 45], 3:[60,90,45, 45]} 

drillholes = {'DD01':[collar1, survey1], 'DD02':[collar2, survey2], 'DD03':[collar3, survey3]}
"""

def calcXYZ(drillholes):
#calculate XYZ coords for all drillholes
    for holes in drillholes:
        holedata = drillholes[holes]
        collar = holedata[0]
        survey =holedata[1]
        trace = traceMaker(collar, survey)
        drillholeXYZ[holes] = trace.results
    return drillholeXYZ
    
def writeLayer(drillXYZ): 
    #create a layer to hold plan drill traces
    layer = QgsVectorLayer("LineString", "Drill traces", "memory")
    pr = layer.dataProvider()
    #add features to layer
    features=[]
    for holes in drillholeXYZ:
        holedat = drillholeXYZ[holes]
        trace = geomBuilder(holedat)
        feat=QgsFeature()
        feat.setGeometry(trace)
        features.append(feat)
        
    pr.addFeatures(features)
      
    #add layer to map canvas  
    QgsMapLayerRegistry.instance().addMapLayer(layer)#create a container for data  from file
    
def densifySurvey(data):
    #a drillhole desurvey tool using simple smooth interpolation of dip and azimuth 
    #between survey points
    d=data
    i=len(d.keys())-1
    entry=0
    newkey=0 # a key variable for creating the new dictionary
    densurvey = {}
    #this works as long as the survey dictionary keys are sequential starting from 0
    while (entry< i):
        next=entry +1 
        list=d[entry]
        list2=d[next] #the next survey in the sequence)
        dh1 = float(list[0])
        dh2= float(list2[0])
        dip1=float(list[2])
        dip2=float(list2[2])
        azi1=float(list[3])
        azi2 = float(list2[3])
        #print dhl, dip1, dip2, azi1, azi2
        #print "iteration", entry
        
        interpdhlList=np.linspace(dh1, dh2, num =10) #create the extra downhole locations
        #need some handling of azis moving between 359 and 001
        if abs(azi1 - azi2) > 300: #detect when azi's are either side of 360
            if azi1 <180:
                azi1 = azi1+360   #add 360 to the smaller number to get a continuous number line to interpolate
            else:
                azi2 = azi2 +360
                
        for item, objects in enumerate(interpdhlList):
            try:
                dipInterp =np.interp(float(objects),[dh1,dh2], [dip1,dip2]) #object is the current dhl to calculate for
                aziInterp =np.interp(float(objects),[dh1,dh2], [azi1,azi2])
                if aziInterp >360:     #correct for azi's greater than 360
                    aziInterp = aziInterp-360
                    
                interpsurv = [objects, interpdhlList[item +1], dipInterp, aziInterp]
                densurvey[newkey]=interpsurv
                newkey=newkey+1
                #print interpsurv
            except IndexError:
                pass
        entry = entry +1
    #add on final survey entry (from last survey to end of hole) as cant be interpolated
    newkey=newkey+1
    densurvey[newkey]=d[entry]
    return densurvey   
 #make a function to lookup a drillhole  and pull a downhole coordinateMode
#perhaps use the bisect function of the ordered dictionary
#then try and make it so that if an exact match isnt found, a near enough value is found and coords are made from that
#this is a precursor to being able to create attributed log style traces.

#after creating the coords for top and bottom, need to now pull all existing coords in between
#again bisect should do the trick to get the top and bottom range, then iterate through the keys
#consider turning this into a class? to share variables internally
def downholeLocator(drillholedata, downholelength):
	#a function to retrieve XYZ coordinates of any given downhole depth
	dhl = downholelength #the target downhole depth to find
	dhdata = drillholedata #the survey dictionary for the target drillhole
	
	
	keylist= dhdata.keys()
	idx = bisect.bisect(keylist, dhl) -1 #search for the insertion point suitable for target depth, and give index of closests uphole entry	
	upholenode =keylist[idx] #the dh depth of the closest node uphole of target
	dholenode = keylist[idx+1]
	extension = dhl-upholenode #the distance past the node to reach desired dh depth
	uhncoord = dhdata[upholenode] #retrieve the XYZ coords of the uphole node
	dhncoord = dhdata[dholenode]
	alpha = math.atan((dhncoord[0]-uhncoord[0])/(dhncoord[2]-uhncoord[2])) #calculate the angle in the XZ plane
	beta = math.atan((dhncoord[1]-uhncoord[1])/(dhncoord[2]-uhncoord[2])) #calculate angle in the YZ plane
	#calculate the coords for the target dhl using the uphole node and the now known angles
	Xdhl = uhncoord[0] - math.sin(alpha)* extension
	Ydhl = uhncoord[1] - math.sin(beta) * extension
	Zdhl = uhncoord[2] - math.cos(alpha) * exstension
		
	return [Xdhl, Ydhl, Zdhl]

#the execution sequence
#create empty containers
drillholes = {}
drillholeXYZ = {}
#start executing the methods
drillholes = readFromFile()
drillXYZ=calcXYZ(drillholes)
print "drill coordinates", drillXYZ
#writeLayer(drillXYZ)
#calculate XYZ coords for all drillholes
