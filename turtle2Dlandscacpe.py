from turtle import *
from tkinter import *
from random import *

print("INITIALISED")
speed(0)
minVersatz=-50
maxVersatz=50
ht()

def r(pseudoH,step):
    if(step!=0):
     return (randint(minVersatz,maxVersatz)/(step*pseudoH))
    else: return (randint(minVersatz,maxVersatz)/(pseudoH))

def mountainChain(startingPoints,pseudoH,length,printPosX,printPosY,color,steps):
    pencolor(color)
    fillcolor(color)
    begin_fill()
    step=1
    points=startingPoints
    for m in range (0,steps):
        for i in range (len(points)-1,0,-1):
            points.insert(i,(points[i-1]+points[i])/2+r(pseudoH,step))
        step+=1
    for x in range (len(points)):
        try:
           points[x]=(points[x-2]+2*points[x-1]+
                      4*points[x]+2*points[x+1]
                      +points[x+2])/10
        except:
            IndexError
    pu()
    goto(printPosX,printPosY)
    x,y=xcor(),ycor()
    pd()
    for n in range(0,len(points)):
        goto((length)/(len(points)-1)*n+x,y+points[n])
    x,y=xcor(),ycor()
    goto(x,-500)
    goto(printPosX,-500)
    goto(printPosX,printPosY)
    end_fill()

#orange (0.9999,0.6,0.0)
backgroundColor=(0.9999,0.6,0.0)
fillcolor(backgroundColor)
pencolor(backgroundColor)
begin_fill()
goto(500,1000)
goto(-500,1000)
goto(-500,-1000)
goto(500,-1000)
goto(500,1000)
end_fill()

mountainChain([0,0],          1.5,  1000,-500, -25,(0.9,0.9,0.9),    8)
mountainChain([0,0],          2,   1000,-500, -75, (0.8,0.8,0.8),    7)
mountainChain([0,0],          3,   1000,-500,-125,(0.5,0.6,0.5),    7)
mountainChain([0,0],          4,   1000,-500,-150,(0.3,0.5,0.3),    7)
mountainChain([0,0],          5,   1000,-500,-175,(0.1,0.3,0.15),    7)

ts = getscreen()

ts.getcanvas().postscript(file="mountains.eps")

done()

print("FINISHED")


