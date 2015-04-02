
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
#2 make the trace coordinates by iterating the DrillholeCoordBuilder class over the drillhole dictionary, returning a
#sequence of x,y,z co-ords for each hole
#3 using these coords, create line segments in a shape file to represent the trace in plan view
#Then need to figure out how to add log data as attributes- perhaps by breaking down the hole into more segments



class DrillholeCoordBuilder:
    #a class which calculates the XYZ coords for an entire drillhole
    #creates a series of x,y,z coordinates from an intial collar location and a series of downhole surveys
    #the resultiing ordered dictionary uses downhole length as its key, and a list of [X,Y,Z] coords as the item
    
    def __init__(self, collar, survey):
        self.Xo = float(collar[0])
        self.Yo = float(collar[1])
        self.Zo = float(collar[2])
        self.survey = survey
        self.temp={0:[self.Xo, self.Yo, self.Zo]} #sets up the collar coordinate
       # self.results = collections.OrderedDict()
        #create the list of 3D co-ordinates downhole
            
        k = 0
        while k < (len(survey.keys())-1):
            slist = survey[k]
            
            sampfrom = float(slist[0])
            
            dip = float(slist[1])
            azi = float(slist[2])
            try:
                slist2 = survey[k+1]
                sampto=float(slist2[0])
            except KeyError:
                sampto = float(collar[3]) #make the last sampto the EOH depth
            
            coords = self.calc(sampfrom, sampto, dip, azi)
            self.Xo=coords[0]
            self.Yo=coords[1]
            self.Zo=coords[2]
            self.temp[sampto] = coords
            k=k+1
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
def geomBuilder(coordlist):
    #takes a dictionary of lists (XYZ) coords. and creates a list of XY coord pairs(ie for plan view.
    #this is then converted into a QGS polyline object that can then be written to a layer
    #keys are unimportant
    nodestring =[]
    for index in coordlist:
        coordsXYZ=coordlist[index]
        node =QgsPoint(coordsXYZ[0], coordsXYZ[1])
        nodestring.append(node)
        
    linestring = QgsGeometry.fromPolyline(nodestring)
    return linestring    
    
    
 #read collar and survey files into drillholes dict file
def readFromFile():
    collars = []
    drillholes = {}
    with open(r'E:\GitHub\DrillHandler\collars.csv', 'r') as col:
        next(col)
        readercol=csv.reader(col)
            
        for holeid,x,y,z,EOH in readercol:
            
            collars=[x,y,z,EOH]
            a = holeid
            i=0
                    
            with open(r'E:\GitHub\DrillHandler\surveys.csv', 'r') as sur:
                next(sur)
                readersur = csv.reader(sur)
                surveys={}
                for hole, depth,dip,azi in readersur:
                    if hole ==a:
                        surv = [depth, dip, azi]
                        surveys[i]=surv
                        i=i+1
                #print"survey from file", surveys
                desurvey = densifySurvey(surveys)    #run desurvey/densify algorithm
                #print "survey", surveys
                #print "desurvey",desurvey
                drillholes[holeid] = [collars, desurvey] 
    #print drillholes
    return drillholes

def calcXYZ(drillholes):
#calculate XYZ coords for all drillholes
    for holes in drillholes:
        holedata = drillholes[holes]
        collar = holedata[0]
        survey =holedata[1]
        trace = DrillholeCoordBuilder(collar, survey)
        drillholeXYZ[holes] = trace.results
    return drillholeXYZ
    
def writeLayer(drillXYZ): 
    #create a layer to hold plan drill traces
    layer = QgsVectorLayer("LineString", "Drill traces", "memory")
    pr = layer.dataProvider()
    #add features to layer
    features=[]
    for holes in drillXYZ:
        holedat = drillXYZ[holes]
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
        dip1=float(list[1])
        dip2=float(list2[1])
        azi1=float(list[2])
        azi2 = float(list2[2])
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
                    
                interpsurv = [objects, dipInterp, aziInterp]
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

class IntervalCoordBuilder:
#a class which calculates the XYZ coords for a specified interval of a given drillhole
#data parsed is the drillhole XYZ dictionary (ordered, keys=downhole depth) and the sart and end of the desired interval
    def __init__(self, drillholedata, sampfrom, sampto):
        #initialise instance variables
        self.dhdata = drillholedata #the XYZ dictionary for the target drillhole
        self.keylist= self.dhdata.keys()
        #print"keylist", self.keylist
        self.sampfrom = sampfrom
        self.sampto = sampto
        #initialise result container which will be used to build geometries
        self.intervalcoords= collections.OrderedDict()
        #execute algorithm to create coords
        self.createCoordList()
    
    def downholeLocator(self, downholedepth):
        #a function to retrieve XYZ coordinates of any given downhole depth
        dhd = downholedepth #the target downhole depth to find
        #print "DHdepth", dhd
        idx = bisect.bisect(self.keylist, dhd) -1 #search for the insertion point suitable for target depth, and give index of closests uphole entry    
        #print "idx", idx
        upholenode = self.keylist[idx] #the dh depth of the closest node uphole of target
        #print"upholenode", upholenode
        dholenode = self.keylist[idx+1]
        #print "dholenode", dholenode
        dhlength = dholenode - upholenode
        extension = dhd-upholenode #the distance past the node to reach desired dh depth
        uhncoord = self.dhdata[upholenode] #retrieve the XYZ coords of the uphole node
        dhncoord = self.dhdata[dholenode]
        #print " node coords", uhncoord, dhncoord
        alpha =  math.acos((dhncoord[2]-uhncoord[2])/dhlength)
        theta = math.asin((dhncoord[0]-uhncoord[0])/dhlength)
        phi = math.asin((dhncoord[1]-uhncoord[1])/dhlength)
        #calculate the coords for the target dhl using the uphole node and the now known angles
        Xdhl = uhncoord[0] +math.sin(theta)* extension
        Ydhl = uhncoord[1] + math.sin(phi) * extension
        Zdhl = uhncoord[2] + math.cos(alpha) * extension
            
        return [Xdhl, Ydhl, Zdhl]

    def gatherNodes(self):
        #function to collect the coordinates (specifically the dict keys) that fall in the target interval
        inInterval = []
        for k in self.keylist:
            if k >= self.sampfrom and k<=self.sampto:
                inInterval.append(k)
        return inInterval

    def createCoordList(self):
        #create the list of XYZ coords that represents the drillhole interval
        #result is a dictionary of coords (list) with downhole depth as key

        #get start coord
        if self.dhdata.has_key(self.sampfrom):
            pass #this entry will be picked up by gatherNodes
        else:
            self.intervalcoords[self.sampfrom] = self.downholeLocator(self.sampfrom)
        #get middle coords
        for i in self.gatherNodes():
            self.intervalcoords[i]=self.dhdata[i]        

        #getend coord
        if self.dhdata.has_key(self.sampto):
            pass #this entry was picked up by gatherNodes
        else:
            self.intervalcoords[self.sampto] = self.downholeLocator(self.sampto)


class LogDrawer:
#class to draw attributed traces of drillholes from tabular log data
    def __init__(self, drillholedata, logfile):
        self.holecoords = drillholedata #set the XYZ coord data for the drillhole dataset
        self.logfile = logfile #path of the target logfile
        self.tlayer = self.createEmptyLog()
        self.logPlanBuilder()

    def createEmptyLog(self):
        #function to create a memory layer with correct field types from the csv logfile
        
        csvfile = open(self.logfile, 'rb')
        reader = csv.reader(csvfile)
        header = reader.next()
        # Get sample
        sample = reader.next()
        fieldsample = dict(zip(header, sample))
        #print "fieldsample", fieldsample
        fieldnametypes = {}
        # create dict of fieldname:type
        for key in fieldsample.keys():
            try:
                float(fieldsample[key])
                fieldtype = 'real'
            except ValueError:
                fieldtype = 'string'
            fieldnametypes[key] = fieldtype
        # Build up the URI needed to create memory layer
        uri = "templog?"
        for fld in header:
            uri += 'field={}:{}&'.format(fld, fieldnametypes[fld])
        tlayer = QgsVectorLayer(uri, "templayer", "memory")
        return tlayer

    def logPlanBuilder(self):
        #a function to take an attribute table with drillhole log data and create traces for each entry

        #load the log file 
        logdata = QgsVectorLayer(self.logfile, 'magsus', 'ogr')
        tprov=self.tlayer.dataProvider()
        logprov=logdata.dataProvider()
        #create iterator
        logiter = logdata.getFeatures()
        #create the new shapefile TODO make the pathstring up from logfile name, perhaps even CRS from GUI?
        writer = QgsVectorFileWriter("E:\GitHub\DrillHandler\log.shp", "CP1250",tprov.fields(), QGis.WKBLineString, logprov.crs(),'ESRI Shapefile')
        #iterate over all log entries and create the trace geometries into the new shapefile
        for logfeature in logiter:
            #initialise variables
            holeid = logfeature.attributes()[logfeature.fieldNameIndex('HoleID')]
            lsampfrom =float( logfeature.attributes()[logfeature.fieldNameIndex('From')])
            lsampto = float(logfeature.attributes()[logfeature.fieldNameIndex('To')])
            holeXYZ = self.holecoords[holeid]
            #print "holeXYZ", holeXYZ
            #print"from", lsampfrom
            #print"to", lsampto
            loginterval = IntervalCoordBuilder(holeXYZ, lsampfrom, lsampto)
            logresultinterval= loginterval.intervalcoords
            #print "interval", logresultinterval
            #create the geometry from the interval coords
            logtrace = geomBuilder(logresultinterval)
            #create a new feature, set geometry from above and add the attributes from original data table
            logfeat=QgsFeature()
            logfeat.setGeometry(logtrace)
            logfeat.setAttributes(logfeature.attributes())
            writer.addFeature(logfeat)
            #logfeatures.append(logfeat)
        del writer
        #the following should probably be (re)moved in the final version to a more appropriate location
        loglayer =QgsVectorLayer("E:\GitHub\DrillHandler\log.shp", "magsuslog", 'ogr')
        QgsMapLayerRegistry.instance().addMapLayer(loglayer)


#the execution sequence
#create empty containers
drillholes = {}
drillholeXYZ = {}
#start executing the methods
drillholes = readFromFile()
drillXYZ=calcXYZ(drillholes)
#print "drill coordinates", drillXYZ


writeLayer(drillXYZ)
logfilepath = "E:\GitHub\DrillHandler\magsus.csv"
LogDrawer(drillXYZ, logfilepath)
