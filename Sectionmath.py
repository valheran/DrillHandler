#playing around with projecting X-Y Z coords onto any vertical plane

import math

#define the plane in terms of origin and a strike/azimuth references to the cardinal axes [x,y,azi]
sectionplane = [0, 0,271]

#define the coord to be projected onto the plane  [x,y, z]

tarpoint = [-8, -10, 10]

#calculate the properties of the xy trangulation between section origin and target point
delY =  tarpoint[1] - sectionplane[1]
print "delY", delY
delX = tarpoint[0] -sectionplane[0]
print "delX", delX
dist = math.sqrt( delX**2  +  delY**2)
print "dist", dist
#calculate the angle from origin to tarpint
alpha = math.atan2(delY, delX) 
print "alpha", alpha
#calculate the angle between the point and the plane
beta = alpha - math.radians(90 - sectionplane[2] )
#beta = math.radians(sectionplane[2] -90) - alphaprint "beta", beta
#calculate the along section coord using beta and distance from origin
xS = math.cos(beta) * dist

sectioncoord = [xS, tarpoint[2]]
print "section coord", sectioncoord
