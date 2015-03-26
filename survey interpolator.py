#attempt to make a drillhole desurvey tool using simple smooth interpolation of dip and azimuth 
#between survey points

import numpy as np

survey = {0: [0, 30, 60, 350], 1: [30, 60, 60, 355], 2: [60, 90, 58, 357], 3: [90, 120, 55, 1], 4: [120, 150, 50, 3], 5: [150, 180, 45, 359], 6: [180, 200, 40, 355]}



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
    
ans = densifySurvey(survey)
print "Resulting Dict", ans
