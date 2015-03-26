import csv
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
                 
            drillholes[holeid] = [collars, surveys]
                    

#print collars.items()
print drillholes.keys()
print drillholes.items()
