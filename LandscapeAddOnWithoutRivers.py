"""
This is an Add-on for Blender. It creates Landscapes with simple simulations for water, erosion and forest-distribution.
Copyright (C) 2015  Roman Riesen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

bl_info = {
    "name": "Landscape",
    "author": "Roman Riesen",
    "version": (0, 0, 1),
    "blender": (2, 74, 0),
    "location": "View3D > Add > mesh",
    "description": ("Adds a landscape mesh (Square Diamond Algorithm) as well as tools for erosion and forrest <<maps>>."),
    "warning": "",
    "category": "Add mesh",}

import bpy
from bpy.props import *
from random import randint,uniform,seed
from math import ceil,degrees,atan
from bpy.props import *

##utils

def inFloatRange(value, limit1,limit2):
    if value >= limit1 and value <= limit2:
        return True
    if value >= limit2 and value <= limit1:
        return True
    else: return False

def sumOf2DArray (array):
       n =0
       for x in range (len(array)):
           n+= sum(array[x])
       return n

def lenOf2DArray (array):
       n =0
       for x in range (len(array)):
           n+= len(array[x])
       return n

def in2DArray (value,array):
    for i in range(len(array)):
        if value in array[i]:
            return True
    return False



def getArrayValue (x,y,array):#data "wraping" around the edges.
    size = len(array)
    x=x%size
    y=y%size
    return(array[x][y])

def setArrayValue (x,y,value,array): #data "wraping" around the edges
    size = len(array)
    x= x%size
    y = y%size
    array[x][y]=value

def numberOfMoorNeighbours (x,y,array):
    neighbours = 0
    for u in range (x-1,x+1):
        for v in range (y-1,y+1):
            if u == x and v == y:
                continue
            elif getArrayValue(x,y,array) == 1:
                neighbours += 1

    return neighbours

def myGaussianBlur (array,steps):
    size = len(array)
    for n in range(steps):
        for x in range(size):
            for y in range (size):
                   setArrayValue(x,y,
                   (getArrayValue(x-1,y-1,array) +2*getArrayValue(x-1,y,array) + getArrayValue(x-1,y+1,array)
                   +2*getArrayValue(x,y-1,array) +12*getArrayValue(x,y,array) + 2*getArrayValue(x,y+1,array)
                   +getArrayValue(x+1,y-1,array) +2*getArrayValue(x+1,y,array) + getArrayValue(x+1,y+1,array))/24,
                   array)


def blenderOutput(zCoords,name = "terrain", finalSize=10, position = None):
    if position == None:
        position = bpy.context.scene.cursor_location
    size=len(zCoords)
    #Verts
    Verts=[]
    for x in range(-1,size):# -1 so I have a perfect wrap and can use array modifier.
        for y in range(-1,size):
            Verts.append([x*(finalSize/size)+position[0],y*(finalSize/size)+position[1],float(zCoords[x][y])+position[2]])
    #Edges are automatically made if Faces are defined.
    Edges=[]
    #Faces are defined by the indices of the vertices.
    Faces=[]
    ##    """
    ##    if size = 2
    ##    faces should be:
    ##    0143
    ##    1254
    ##
    ##    3476
    ##    4587
    ##    """
    for i in range (0,size*size+size-1):
#        if (i%size == 0):
#            continue
#        else:
            Faces.append([i+size+1,i+size+2,i+1,i])
#    #Ungultige Elemente Entfernen, da ich keinen besseren Weg fand
    for j in range (1,size*size):
        if(j%size==0):
            x=Faces[j]
            Faces.remove(x)
    mesh = bpy.data.meshes.new(name+"_data")  #Data Instanziert
    mesh.from_pydata(Verts, Edges, Faces)      #Erstellung des Polygons
    mesh.update()
    object = bpy.data.objects.new(name, mesh)  #Namensgebung
    object.data = mesh
    scene = bpy.context.scene
    scene.objects.link(object)
    object.select = True
    scene.objects.active = object

    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
    object.location = position

    return object

def createVertexGroups (heights = "0.3,0.6"):
    heights.append(float("inf"))

    vertexGroups=[x[:] for x in [[]]*2*len(heights)]
    bpy.ops.object.mode_set(mode='EDIT')
    terrainObject = bpy.context.active_object
    terrainObjectData = terrainObject.data

    bpy.ops.object.mode_set(mode='OBJECT')
    size = int(len([ v.index for v in terrainObjectData.vertices])**0.5)
    blenderSizeX =bpy.context.active_object.dimensions.x
    blenderSizeY =bpy.context.active_object.dimensions.y
    blenderSizeZ =bpy.context.active_object.dimensions.z

    for i in range(len(list(heights))):
        heights[i] = heights[i]*blenderSizeZ

    bpy.ops.object.mode_set(mode='EDIT')

    for heightLvl in range (len(heights)):

        flatVert=terrainObject.vertex_groups.new("Flat, height: %s"%str(heightLvl+1))

        steepVert=terrainObject.vertex_groups.new("Steep, height: %s"%str(heightLvl+1))

        bpy.ops.object.mode_set(mode='OBJECT')
        for x in range (size):
            for y in range (size):
                if angleMap[x][y]<=angle and heightMap[x][y] < heights[heightLvl]:
                    flatVert.add([i],1,'ADD')

                elif heightMap[x][y] < heights[heightLvl]:
                    steepVert.add([i],1,'ADD')

                groupIndex+=2
                i+=1
        bpy.ops.object.mode_set(mode='EDIT')


def createCyclesWaterMaterial():
    #Set all scenes to cycle render engine
    for scene in bpy.data.scenes:
        scene.render.engine = 'CYCLES'

    #create new Material called 'water material'
    seaMaterial = bpy.data.materials.new('Water material')
    seaMaterial.use_nodes =True
    #shortcut to material nodes
    nodes = seaMaterial.node_tree.nodes
    #delete all existing nodes
    for node in nodes:
        nodes.remove(node)

    #create a glossy shader
    node_water = nodes.new(type='ShaderNodeBsdfGlossy')
    node_water.inputs[0].default_value = (0.47,0.68,0.9,1)
    node_water.inputs[1].default_value = 0.01
    node_water.location = -400,0
    #create output node
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = 0,0
    #shortcut to links
    link = links = seaMaterial.node_tree.links
    #connect glossy shader with output node
    output = node_water.outputs[0]
    input = node_output.inputs[0]
    link = links.new(output,input)
    #set viewport color
    seaMaterial.diffuse_color = (0.0,0.0,1.0)
    #return the material
    return seaMaterial


def createCyclesTerrainMaterial():

    for scene in bpy.data.scenes:
        scene.render.engine = 'CYCLES'

    terrainMaterial = bpy.data.materials.new('Terrain material')
    terrainMaterial.use_nodes =True

    nodes = terrainMaterial.node_tree.nodes

    for node in nodes:
        nodes.remove(node)

    node_snow = nodes.new(type='ShaderNodeBsdfDiffuse')
    node_snow.inputs[0].default_value = (0.9,0.9,0.9,1)
    node_snow.inputs[1].default_value = 5.0
    node_snow.location = -750,1000

    node_stone = nodes.new(type='ShaderNodeBsdfDiffuse')
    node_stone.inputs[0].default_value = (0.35,0.35,0.35,1)
    node_stone.location = -750,800

    node_mixSnowAndStone = nodes.new(type='ShaderNodeMixShader')
    node_mixSnowAndStone.location = -450,900

    node_mixStone = nodes.new(type='ShaderNodeMixShader')
    node_mixStone.location = -150,700

    node_grass = nodes.new(type='ShaderNodeBsdfDiffuse')
    node_grass.inputs[0].default_value = (0.1,0.5,0.1,1)
    node_grass.inputs[1].default_value = 5.0
    node_grass.location = -750,575

    node_dirt = nodes.new(type='ShaderNodeBsdfDiffuse')
    node_dirt.inputs[0].default_value = (0.35,0.25,0.1,1)
    node_dirt.location = -750,375

    node_mixGrassAndDirt = nodes.new(type='ShaderNodeMixShader')
    node_mixGrassAndDirt.location = -450,475

    node_snowAngleColorRamp = nodes.new(type='ShaderNodeValToRGB')
    node_snowAngleColorRamp.location = -1350,850
    node_snowAngleColorRamp.color_ramp.interpolation = 'CONSTANT'
    node_snowAngleColorRamp.color_ramp.elements[1].position = 0.75
    node_snowAngleColorRamp.color_ramp.elements[0].color = (1.0,1.0,1.0,1.0)
    node_snowAngleColorRamp.color_ramp.elements[1].color = (0.0,0.0,0.0,1.0)

    node_geometry = nodes.new(type='ShaderNodeNewGeometry') #Hat auch nur 30 Minuten gebraucht, um herauszufinden, dass es sowohl NewGeometry als auch Geometry gibt.
    node_geometry.location = -1800,700

    node_separateRGBSnow = nodes.new(type='ShaderNodeSeparateRGB')
    node_separateRGBSnow.location = -1570,650

    node_dirtAngleColorRamp = nodes.new(type='ShaderNodeValToRGB')
    node_dirtAngleColorRamp.location = -1350,575
    node_dirtAngleColorRamp.color_ramp.interpolation = 'EASE'
    node_dirtAngleColorRamp.color_ramp.elements[0].position = 0.6
    node_dirtAngleColorRamp.color_ramp.elements[1].position = 0.75
    node_dirtAngleColorRamp.color_ramp.elements[0].color = (1.0,1.0,1.0,1.0)
    node_dirtAngleColorRamp.color_ramp.elements[1].color = (0.0,0.0,0.0,1.0)


    node_noiseSnowHeight= nodes.new(type='ShaderNodeTexNoise') #not to be confused with Snow White.
    node_noiseSnowHeight.location = -1600,200

    node_substractRandomValue= nodes.new(type='ShaderNodeMath')
    node_substractRandomValue.location = -1400,200
    node_substractRandomValue.operation = 'MULTIPLY'

    node_textureCoordinates= nodes.new(type='ShaderNodeTexCoord')
    node_textureCoordinates.location = -1800,0

    node_separateXYZ= nodes.new(type='ShaderNodeSeparateXYZ')
    node_separateXYZ.location = -1600,0

    node_snowHeightColorRamp = nodes.new(type='ShaderNodeValToRGB')
    node_snowHeightColorRamp.location = -1200,200
    node_snowHeightColorRamp.color_ramp.interpolation = 'EASE'
    node_snowHeightColorRamp.color_ramp.elements[0].position = 0.6
    node_snowHeightColorRamp.color_ramp.elements[1].position = 0.65
    node_snowHeightColorRamp.color_ramp.elements[0].color = (1.0,1.0,1.0,1.0)
    node_snowHeightColorRamp.color_ramp.elements[1].color = (0.0,0.0,0.0,1.0)

    node_stoneHeightColorRamp = nodes.new(type='ShaderNodeValToRGB')
    node_stoneHeightColorRamp.location = -1200,-100
    node_stoneHeightColorRamp.color_ramp.interpolation = 'EASE'
    node_stoneHeightColorRamp.color_ramp.elements[0].position = 0.4
    node_stoneHeightColorRamp.color_ramp.elements[1].position = 0.5
    node_stoneHeightColorRamp.color_ramp.elements[0].color = (1.0,1.0,1.0,1.0)
    node_stoneHeightColorRamp.color_ramp.elements[1].color = (0.0,0.0,0.0,1.0)


    node_mixFinal = nodes.new(type='ShaderNodeMixShader')
    node_mixFinal.location = 100,475


    node_pointinessColorRamp = nodes.new(type='ShaderNodeValToRGB')
    node_pointinessColorRamp.location = -600,-275
    node_pointinessColorRamp.color_ramp.interpolation = 'CONSTANT'
    node_pointinessColorRamp.color_ramp.elements[1].position = 0.5

    node_invertPointiness= nodes.new(type='ShaderNodeInvert')
    node_invertPointiness.location = -800,-275


    # create output node
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = 400,0

    ## MAKE ZELDAS..ehm...LINKS.

    links = terrainMaterial.node_tree.links

    output = node_stone.outputs[0]
    input = node_mixSnowAndStone.inputs[2]
    link = links.new(output,input)

    output = node_snow.outputs[0]
    input = node_mixSnowAndStone.inputs[1]
    link = links.new(output,input)

    output = node_dirt.outputs[0]
    input = node_mixGrassAndDirt.inputs[2]
    link = links.new(output,input)

    output = node_grass.outputs[0]
    input = node_mixGrassAndDirt.inputs[1]
    link = links.new(output,input)

    output = node_snowAngleColorRamp.inputs[0]
    input = node_separateRGBSnow.outputs[2]
    link = links.new(output,input)

    output = node_dirtAngleColorRamp.inputs[0]
    input = node_separateRGBSnow.outputs[2]
    link = links.new(output,input)

    output = node_separateRGBSnow.inputs[0]
    input = node_geometry.outputs[1]
    link = links.new(output,input)

    output = node_mixSnowAndStone.inputs[0]
    input = node_snowAngleColorRamp.outputs[0]
    link = links.new(output,input)

    output = node_mixGrassAndDirt.inputs[0]
    input = node_dirtAngleColorRamp.outputs[0]
    link = links.new(output,input)

    output = node_separateXYZ.inputs[0]
    input = node_textureCoordinates.outputs[0]
    link = links.new(output,input)

    output = node_substractRandomValue.inputs[0]
    input = node_separateXYZ.outputs[2]
    link = links.new(output,input)

    output = node_substractRandomValue.inputs[1]
    input = node_noiseSnowHeight.outputs[1]
    link = links.new(output,input)

    output = node_snowHeightColorRamp.inputs[0]
    input = node_substractRandomValue.outputs[0]
    link = links.new(output,input)

    output = node_mixStone.inputs[1]
    input = node_mixSnowAndStone.outputs[0]
    link = links.new(output,input)

    output = node_mixStone.inputs[2]
    input = node_stone.outputs[0]
    link = links.new(output,input)

    output = node_mixStone.inputs[0]
    input = node_snowHeightColorRamp.outputs[0]
    link = links.new(output,input)

    output = node_stoneHeightColorRamp.inputs[0]
    input = node_separateXYZ.outputs[2]
    link = links.new(output,input)

    output = node_mixFinal.inputs[0]
    input = node_stoneHeightColorRamp.outputs[0]
    link = links.new(output,input)

    output = node_mixFinal.inputs[1]
    input = node_mixStone.outputs[0]
    link = links.new(output,input)

    output = node_mixFinal.inputs[2]
    input = node_mixGrassAndDirt.outputs[0]
    link = links.new(output,input)


    output = node_mixFinal.outputs[0]
    input = node_output.inputs[0]
    link = links.new(output,input)

    return terrainMaterial

class createAngleAndHeightMapOfTerrain():
        def __init__ (self,obj = None,heightMap = None):
            if obj == None :
                obj = bpy.context.active_object
            objD = obj.data
            size = int(len([ v.index for v in obj.data.vertices])**0.5)-1
            bpy.ops.object.mode_set(mode='EDIT')
            #each point represents the angle to the next vertices in positive x and y direction.
            self.angleMap=[x[:] for x in [[float(0)]*size]*size]
            if heightMap == None:
               self.heightMap=[x[:] for x in [[float(0)]*size]*size]
               i= -1
               for x in range(-1,size):
                  for y in range(-1,size):
                      self.heightMap[x][y]=objD.vertices[i].co[2]
                      i+=1
            else: self.heightMap = heightMap

            self.distanceBetweenVertices = obj.dimensions.x/size
            for x in range (-1,size):
                for y in range (-1,size):

                    t1=abs(self.calculateAngle(self.heightMap[x][y],getArrayValue(x+1,y,self.heightMap)))
                    t2=abs(self.calculateAngle(self.heightMap[x][y],getArrayValue(x,y+1,self.heightMap)))
                    t3=abs(self.calculateAngle(self.heightMap[x][y],getArrayValue(x-1,y,self.heightMap)))
                    t4=abs(self.calculateAngle(self.heightMap[x][y],getArrayValue(x,y-1,self.heightMap)))
                    self.angleMap[x][y]=max(t1,t2,t3,t4)#I want the higher angle

            bpy.ops.object.mode_set(mode='OBJECT')

        def calculateAngle(self,height0,height1):
             deltaHeight=height1-height0
             angle= degrees(atan(deltaHeight/self.distanceBetweenVertices)) #distance SHOULD never be 0, so no exception or if needed.
             return  angle

class createForest():
    def __init__ (self, obj, heightMap,angleMap,obstacleMap = None,useGameOfLife = False, forestLimits = [0.1,0.6], angle = 90, steps = 5, minHeight = 0.5, startPercent = 20.0):
        self.size           = len(heightMap)
        self.steps          = steps
        self.minWeight      = minHeight
        self.useGameOfLife  = useGameOfLife
        self.angleMap       = angleMap
        self.terrainObject  = obj
        self.heightMap      = heightMap
        self.angle          = angle
        self.forestLimits   = forestLimits
        self.startPercent   = startPercent
        self.forestDistGroup = self.terrainObject.vertex_groups.new("Tree distrib.: " + str(self.forestLimits[0]) + " to " + str(self.forestLimits[1]))
        self.forestHeightGroup = self.terrainObject.vertex_groups.new("Tree height: " + str(self.forestLimits[0]) + " to " + str(self.forestLimits[1]))

        self.blenderSizeZ = self.terrainObject.dimensions.z
        self.forestLimits = [((self.forestLimits[0] /self.blenderSizeZ)-0.5 * self.blenderSizeZ),
                            ((self.forestLimits[1] /self.blenderSizeZ)-self.blenderSizeZ * 0.5)]#-0.5*self.blenderSizeZ because half of the height of the mesh is below its origin, thus negative.

        print(self.forestLimits)
        if obstacleMap == None:
            self.obstacleMap = [x[:] for x in [[0]*self.size]*self.size]

        self.createRandomForestMap()

        self.tempForestMap = [x[:] for x in [[0]*self.size]*self.size]

        if useGameOfLife :
            for i in range (self.steps):
                self.step()
        else:
            self.forestMap = [x[:] for x in [[1]*self.size]*self.size] # Forest everywhere.

        self.createForestVertexGroups()

    def step (self):
        for x in range (self.size):
          for y in range(self.size):
               n= numberOfMoorNeighbours(x,y,self.forestMap)
               if (n==0):
                    self.tempForestMap[x][y]=1#0
               if (n==1):
                    self.tempForestMap[x][y]=1#0
               if (n==2):
                    self.tempForestMap[x][y]=1#0
               if (n==3):
                    self.tempForestMap[x][y]=1
               if (n==4):
                   if self.Feld[a][b]==1:
                       self.tempForestMap[x][y]=1
                   else:
                       self.tempForestMap[x][y]=1#0
               if (n==5):
                    self.tempForestMap[x][y]=1
               if (n==6):
                    self.tempForestMap[x][y]=1
               if (n==7):
                    self.tempForestMap[x][y]=1
               if (n==8):
                    self.tempForestMap[x][y]=1

        self.forestMap = self.tempForestMap

    def createRandomForestMap(self):
        self.forestMap     = [x[:] for x in [[0]*self.size]*self.size]
        for x in range(self.size):
            for y in range(self.size):
                if randint(0,100) < self.startPercent:
                    self.forestMap[x][y] = 1

    def createForestVertexGroups(self):

        i = 0
        deltaLimits = abs(self.forestLimits[1]- self.forestLimits[0])
        for x in range (-1,self.size):
            for y in range (-1,self.size):
                if getArrayValue(x,y,self.forestMap) == 1 and getArrayValue(x,y,self.obstacleMap) == 0  and getArrayValue(x,y,self.angleMap) < self.angle and getArrayValue(x,y,self.heightMap) < self.forestLimits[1] and getArrayValue(x,y,self.heightMap) > self.forestLimits[0]:#inFloatRange(self.heightMap[x][y],self.forestLimits[0],self.forestLimits[1]):
                    self.forestDistGroup.add([i],1,'ADD')
                    deltaToHigherLimit = abs(self.forestLimits[1]-self.heightMap[x][y])
                    weight = self.minWeight+deltaToHigherLimit
                    self.forestHeightGroup.add([i],weight,'ADD')

                i+=1

    def blenderOutputRiver(self,objname, curvename, list):

        curvedata = bpy.data.curves.new(name=curvename, type='CURVE')
        curvedata.dimensions = '3D'
        curvedata.bevel_depth = 0.0
        origin = terrainObject.location
        objectdata = bpy.data.objects.new(objname, curvedata)
        objectdata.location = (origin) #object origin
        bpy.context.scene.objects.link(objectdata)
        polyline = curvedata.splines.new('POLY')
        polyline.points.add(len(list)-1)
        for i in range(len(list)):
            x, y, z = list[i]
            polyline.points[i].co = (x, y, z, 1)

    def carveRivers ():
        i=0
        for scene in bpy.data.scenes:
            scene.tool_settings.proportional_edit
        for x in range (self.size):
            for y in range(self.size):
                if self.riverMap[x][y] != 0:
                    bpy.ops.mesh.select_all(action='DESELECT')
                    vertexHeight = terrainObject.data.vertices[i].co[2]
                    self.terrainObject.data.vertices[i].select = True
                    bpy.ops.transform.translate(value=(0.0, 0.0, - self.riverMap[x][y] * self.carveDepth), constraint_orientation='GLOBAL', proportional='CONNECTED', proportional_edit_falloff='SHARP', proportional_size=1.0, release_confirm=True)

                i+=1

class diamondSquare():

    def __init__(self,size=64,pseudoH=1.75,minLift=-20,maxLift=20,seedValue=19,gaussianBlurSteps=1,startVerts=[]):
        """self,size=64,pseudoH=1.75,minLift=-20,maxLift=20,seedValue=19,gaussianBlurSteps=1,startVerts=[]"""

        self.size           =   size
        self.stepsize       =   size
        self.halfstepSize   =   self.stepsize//2
        self.pseudoH        =   pseudoH
        self.blurSteps      =   gaussianBlurSteps
        self.minLift        =   minLift ## There was a version, where the user was able to set these values seperatly. I found there was no gain in it, so now the user can only set the maximal total height.
        self.maxLift        =   maxLift
        self.step           =   0

        seed(seedValue)

        if (startVerts==[]):
            self.verts=[x[:] for x in [[float(0)]*self.size]*self.size] #[x[:] for x in ARRAY] is needed because else  [[0]*size]*size] would create lists, which will stay always the same.)
        else:
            self.verts=self.toFullArray(startVerts)

        self.diamondSquareAlgorithm()

        myGaussianBlur(self.verts,self.blurSteps)


    def roughness(self):
        r=uniform(self.minLift,self.maxLift)/(self.pseudoH**self.step)
        return r

    def initiateStart(self):
        for x in range(0,self.size):
            for y in range (0,self.size):
                self.setVert(x,y,roughness())

    def getVert (self,x,y):
        x=x%self.size
        y=y%self.size
        return(self.verts[x][y])

    def setVert (self,x,y,value):
        x= x%self.size
        y = y%self.size
        self.verts[x][y]=value

    def diamond (self,x,y):

        v1 = self.getVert (x-self.halfstepSize,y)
        v2 = self.getVert (x,y-self.halfstepSize)
        v3 = self.getVert (x,y+self.halfstepSize)
        v4 = self.getVert (x+self.halfstepSize,y)

        self.setVert(x,y,(v1+v2+v3+v4)/4+self.roughness())

    def square (self,x,y):

        v1 = self.getVert (x-self.halfstepSize,y-self.halfstepSize)
        v2 = self.getVert (x-self.halfstepSize,y+self.halfstepSize)
        v3 = self.getVert (x+self.halfstepSize,y+self.halfstepSize)
        v4 = self.getVert (x+self.halfstepSize,y-self.halfstepSize)

        self.setVert(x,y,(v1+v2+v3+v4)/4+self.roughness())

    def diamondSquareStep(self):

        for y in range (self.halfstepSize,self.size+self.halfstepSize,self.stepsize):
            for x in range (self.halfstepSize,self.size+self.halfstepSize,self.stepsize):
                self.square(x,y)

        for y in range (0,self.size,self.stepsize):
            for x in range (0,self.size,self.stepsize):
                #Two times diamond because
                self.diamond(x+self.halfstepSize,y)
                self.diamond(x,y+self.halfstepSize)

    def diamondSquareAlgorithm(self):

        while (self.stepsize>1):
            self.stepsize = self.stepsize//2
            self.halfstepSize=self.halfstepSize//2
            self.diamondSquareStep()
            self.step+=1


class thermalErosion():
    def __init__ (self,twoDimensionalHeightArray,erosionValue=0.1,steps=5,angle=50,inverseErosion=True):
        """twoDimensionalHeightArray,steps,angle (distance between cells always set at 1, not the distance they have in blender),inverseErosion (flats flat areas and maintains cliffs)"""
        self.verts=twoDimensionalHeightArray
        self.sizeX  = len(self.verts)
        self.sizeY  = len(self.verts[0])
        self.size   = self.sizeX
        self.angle  = angle
        self.erosionValue = erosionValue
        self.steps = steps
        self.inverseErosion = inverseErosion

        for n in range (self.steps):
            self.erosionStep()


    def erosionStep (self):
         for x in range (self.size):
            for y in range (self.size):
                for i in range (0,4):
                    if (i==0):
                        xOut,yOut=x,y-1
                    if (i==1):
                        xOut,yOut=x+1,y
                    if (i==2):
                        xOut,yOut=x,y+1
                    if (i==3):
                        xOut,yOut=x-1,y
                    t=self.calculateAngle(getArrayValue(x,y,self.verts),getArrayValue(xOut,yOut,self.verts)) #if t >= 0, the other field is higher than the field we are looking from.
                    if (t > self.angle) and (self.inverseErosion==False): #for the inversed Erosion model, t between the defined angle and zero, material should be moved.
                        setArrayValue(x,y, getArrayValue(x,y,self.verts)-self.erosionValue,self.verts)
                        setArrayValue(xOut,yOut,getArrayValue(x,y,self.verts) + self.erosionValue,self.verts)
                    if (t < self.angle) and (t>0) and (self.inverseErosion==True):#for the normal Erosion model material should only be moved, if the terrain is steeper than the angle.
                        setArrayValue(x,y, getArrayValue(x,y,self.verts) - self.erosionValue,self.verts)
                        setArrayValue(xOut,yOut,getArrayValue(x,y,self.verts) + self.erosionValue,self.verts)


    def calculateAngle (self,height0,height1):
        """height 0: Origin height,height1 other height. Angle negative -> other is lower."""
        return degrees(atan(height1-height0))


    def flow (self):
        #where should water flow?
        for x in range (self.size):
            for y in range (self.size):
                terrain=self.terrainHeight
                water = self.waterMap
                startPoint=getArrayValue(x,y,water)+getArrayValue(x,y,terrain)
                lowerNeighbours = [] #list of Lower Cells
                #if the neighbour Cell is lower, it's poition is appended to the list.
                if startPoint > getArrayValue(x-1,y,terrain)+getArrayValue(x-1,y,water): lowerNeighbours.append([x-1,y])
                if startPoint > getArrayValue(x,y-1,terrain)+getArrayValue(x,y-1,water): lowerNeighbours.append([x,y-1])
                if startPoint > getArrayValue(x+1,y,terrain)+getArrayValue(x+1,y,water): lowerNeighbours.append([x+1,y])
                if startPoint > getArrayValue(x,y+1,terrain)+getArrayValue(x,y+1,water): lowerNeighbours.append([x,y+1])
                #Now I can easily Acces the lower Cells ( "for i in range (numberOfLowerNeighbours): print (getArrayValue(lowerNeigbours[i][0],lowerNeigbours[i][1],terrain)" would print all the terrain heights, which are lower than the middle one.
                numberOfLowerNeighbours = len(lowerNeighbours)
                if numberOfLowerNeighbours == 0: #no more checks needed, since there will be no flow from this field.
                    continue

                waterToEachCell = water[x][y]/(numberOfLowerNeighbours+1) #The water amount, which is distributed to each of the lower neighbours.
                # +1 because the "active" cell itself has to be counted aswell, because I want to even out the water.
                #so the amount "Water to each cell" remains at the active cell.
                #First the cells get the water, which would be higher if all the water was added.
                #This way the rest can be easily distributed in a second for-loop.
                evenedOutCells = 0

                for i in range (numberOfLowerNeighbours):
                    lowerWaterHeight = getArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],water)
                    lowerCellHeight  = getArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],terrain)+getArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],water)
                    if lowerCellHeight+waterToEachCell < water[x][y]+terrain[x][y]:
                            setArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],lowerWaterHeight+waterToEachCell,water)
                            water[x][y]-=waterToEachCell
                            self.waterFlowMap[x][y] = waterToEachCell

                waterToEachCell = water[x][y]/(numberOfLowerNeighbours-evenedOutCells+1) #has to be recalculated, since there's now a different amount of lower Cells and a different amount of water on the active cell.

                for i in range (numberOfLowerNeighbours):
                    lowerWaterHeight = getArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],water)
                    lowerCellHeight  = getArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],terrain)+getArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],water)
                    if lowerCellHeight+waterToEachCell > water[x][y]+terrain[x][y]:
                            waterDifference=startPoint-(lowerWaterHeight+lowerCellHeight)
                            movedWater=waterDifference/2
                            setArrayValue(lowerNeighbours[i][0],lowerNeighbours[i][1],lowerWaterHeight+movedWater,water)
                            water[x][y]-=movedWater
                            self.waterFlowMap[x][y]=movedWater

                            evenedOutCells+=1 #one Neighbour more is now as high as the active cell.

    def dissolve (self):
        for x in range (self.size):
            for y in range (self.size):
                self.waterMap[x][y]-= self.evaporationAmount

    def waterStep(self):
       self.rain()
       self.flow()
       self.dissolve()


#    USER INTERFACE

modes = [('0', 'Terrain & Erosion', 'Create your basic terrain.'),
     ('1', 'Water', 'Add water (basic rivers and seas).'),
     ('2', 'Forest', 'Generate vertex group for the distribution and height of trees (or other objects).')]


class MESH_OT_primitive_landscape_add(bpy.types.Operator):
    '''Add a Landscape'''
    bl_idname = "mesh.primitive_landscape_add"
    bl_label = "Add Landscape"
    bl_options = {'REGISTER', 'UNDO'}

    mode = EnumProperty(name = "Mode",description = "Mode", items = modes)

    ##UPDATES

    update_Erosion = BoolProperty(name="Erosion",
            description ="Should the erosion be updated?",
            default=True)

    update_Seas = BoolProperty(name="Seas",
            description ="Should the watersimulation be updated?",
            default=True)

    update_Forest = BoolProperty(name="Forest",
            description ="Should the forest-vertex-group creator be updated?",
            default=True)

    ##DIAMOND SQUARE
    seed = IntProperty(name="Seed",
            description ="The Seed for the pseudo random number generator",
            default=0)

    subdivisions = IntProperty(name="Subdivisions",
            description ="Number of vertices on one edge will be (2^n)+1. \n WARNING: Values above 8 might slow down everything and cause your os to think Blender crashed (it probably won't)",
            default=6, min=2, max=10)

    blenderSize = FloatProperty(name = "Size", description = "The size in x and y direction",
            default = 5)

    height = FloatProperty(name="Height",
            description ="The maximal height of the Terrain",
            default=1.0)

    randomness = FloatProperty(name="Randomness",
            default=1.75, min=0.5, max=5.0)


    smoothAmount = IntProperty(name="Smoothness",
            description="The amount of cycles of the smoothing function",
            default=2, min=0)

    ##EROSION

    erosionAngle = FloatProperty(name="Angle",
            description = "Critical angle for erosion",
            default=4.0, min=0.0, max=180.0)

    erosionAmount = FloatProperty(name="Amount",
            description="How much material is transported per step and vertex",
            default=0.001)


    erosionIsInverted = BoolProperty(name = "Inverse erosion",
            description = "Moves material, if angle is lower than the specified one.",
            default = True)


    erosionSteps = IntProperty(name="Steps",
            description="How many steps of erosion",
            default=0, min=0, max=256)

    smoothnessAfterErosion = IntProperty(name = "Smoothness After Erosion",
            description = "The amount of cycles of the smoothing function, after the erosion is applied", default = 0, min=0)
    ##FOREST
    minTreeHeight = FloatProperty(name="Min. height of trees",
            description="The lowest Weight of the \" Tree height\" vertex group (which \"simulates\" the decline in size of trees up to the tree limit).",
            default=0.4, min=0, max=1)

    forestAngle = FloatProperty (name = "Critical angle",
            description = "Up to this angle trees should grow",
            default = 50, min = 0, max = 90)

    golSteps = IntProperty(name="steps",
            description="How many steps of the game of life will be processed",
            default=8, min=0, max=256)

    useGameOfLife = BoolProperty(name = "Use game of life",
            description = "Uses an altered version of the game of life to determine where trees grow.",default = True)

    lowerForestLimit = FloatProperty (name = "Lower forest limit",
            description = "The lower limit of the forest.",
            default = 0.0, min= 0.0, max = 1.0)

    higherForestLimit = FloatProperty (name = "Higher forest limit",
            description = "The upper limit of the forest.",
            default = 0.5, min= 0.0, max = 1.0)

    startPercent = FloatProperty (name = "Percent",
            description = "The Amount of forest coverage at the start.",
            default = 22.0, min= 0.0, max = 100.0)

    ##SEAS

    waterSteps = IntProperty(name="steps",
            description="How many steps of the water simulation be processed",
            default=8, min=0)

    rainAmount = FloatProperty(name = "Amount of Rain",
            description = "How much water will be added each Step", default = 0.3)

    evapAmount = FloatProperty(name = "Amount of evaporation",
            description = "How much water will be removed each Step", default = 0.5)

    waterSmoothing = IntProperty(name="Smoothing",
            description="How many steps the water will be smoothed processed",
            default=8, min=0)

    #Gui arrangement

    def draw (self,context):

         layout = self.layout
         layout.prop(self,'mode')

         if self.mode == '0':

            #if self.selfCreatedTerrain == True:
            layout.label("Grid size:")
            box = layout.box()
            split = box.split()
            col = split.column()
            col.prop(self,'subdivisions')
            col = split.column()
            verticesPerEdge = 2**self.subdivisions+1
            col.label(": %s vertices per Edge" %verticesPerEdge)
            col.label(": %s vertices total" %verticesPerEdge**2)
            split = box.split()
            col = split.column()
            col.prop(self,'blenderSize')

            split = box.split()
            col = split.column()
            col.prop(self,'height')

            layout.label("Terrain:")
            box = layout.box()
            split = box.split()
            col = split.column()
            col.prop(self,'seed')
            col.prop(self,'smoothAmount')
            col = split.column()
            col.prop(self,'randomness')

            layout.label("Erosion:")
            box = layout.box()
            split = box.split()
            col = split.column()
            col.prop(self,'erosionSteps')
            col.prop(self,'erosionAngle')
            col=split.column()
            col.prop(self,'erosionIsInverted')
            col.prop(self,'erosionAmount')
            split = box.split()
            col = split.column()
            col.prop(self,'smoothnessAfterErosion')

         if self.mode == '1':

            layout.label("Seas:")
            box = layout.box()
            split = box.split()
            col = split.column()
            col.prop(self,'rainAmount')
            col.prop(self,'waterSteps')
            col = split.column()
            col.prop(self,'evapAmount')
            col.prop(self,'waterSmoothing')

         if self.mode == '2':

            layout.label("Forest:")
            box = layout.box()
            split = box.split()
            col = split.column()
            col.prop(self,'lowerForestLimit')
            col.prop(self,'minTreeHeight')
            col.prop(self,'useGameOfLife')
            col.prop(self,'startPercent')
            col = split.column()
            col.prop(self,'higherForestLimit')
            col.prop(self,'forestAngle')
            col.prop(self,'golSteps')

         layout.label("Updates:")
         box = layout.box()
         split = box.split()
         col = split.column()
         col.prop(self,'update_Erosion')
         col.prop(self,'update_Seas')
         col.prop(self,'update_Forest')

    @classmethod
    def poll (cls,context):
        if bpy.context.active_object != None:
            return bpy.context.active_object.mode == 'OBJECT' or bpy.context.active_object.mode == 'EDIT'
        else: return True

    def createTerrain (self):
         self.terrainVerts=diamondSquare(2**self.subdivisions,self.randomness,self.height/-2,self.height/2,self.seed,self.smoothAmount).verts
         self.terrainObject = blenderOutput(self.terrainVerts,"Terrain",self.blenderSize)
         self.selfCreatedTerrain = True
         angleAndHeightMap = createAngleAndHeightMapOfTerrain(self.terrainObject)
         self.angleMap = angleAndHeightMap.angleMap
         self.heightMap = angleAndHeightMap.heightMap

    def adoptTerrain (self,obj):
         bpy.ops.object.mode_set(mode = 'OBJECT')
         self.terrainObject = obj
         self.selfCreatedTerrain = False
         angleAndHeightMap = createAngleAndHeightMapOfTerrain(self.terrainObject)
         self.angleMap = angleAndHeightMap.angleMap
         self.terrainVerts = angleAndHeightMap.heightMap
         bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')

    def invoke(self, context,event):
        self.subdivisions = 6 #Resets everytime the script launches.
        self.update_Terrain = True #Must be calculated, else other things don't work.
        self.size = 2**self.subdivisions+1
        self.seaMap = [x[:] for x in [[int(0)]*self.size]*self.size]
        obj = bpy.context.active_object
        if obj == None:
           self.createTerrain()
        else:
            if bpy.context.active_object.mode == 'EDIT':
                self.adoptTerrain(obj)
            else:
                self.createTerrain()

        if len(self.terrainObject.data.materials) < 1:
            self.terrainMaterial = createCyclesTerrainMaterial()
            self.terrainObject.data.materials.append(self.terrainMaterial)
        bpy.context.space_data.viewport_shade = 'MATERIAL'

        if self.update_Seas:
            seas = createSeas(self.terrainObject,self.terrainVerts,self.waterSteps,self.rainAmount,self.evapAmount,self.waterSmoothing)
            self.waterObject =  seas.waterObject
            self.seaMap = seas.seaMap

            if len(self.waterObject.data.materials) < 1:
                self.waterMaterial = createCyclesWaterMaterial()
                self.waterObject.data.materials.append(self.waterMaterial)

        if self.update_Forest:
            self.forestLimits = [self.lowerForestLimit,self.higherForestLimit]
            createForest(self.terrainObject, self.terrainVerts, self.angleMap,None,self.useGameOfLife, self.forestLimits, self.forestAngle, self.golSteps, self.minTreeHeight, self.startPercent)

        if self.mode == 2:
            bpy.ops.object.mode_set(mode = 'VERTEX_PAINT')
        else:
            bpy.ops.object.mode_set(mode = 'OBJECT')

        return {'FINISHED'}

    def execute(self,context):
        #bpy.ops.object.mode_set(mode="OBJECT")
        self.size = 2**self.subdivisions+1
        self.riverMap = [x[:] for x in [[int(0)]*self.size]*self.size]
        self.seaMap = [x[:] for x in [[int(0)]*self.size]*self.size]

        for item in bpy.data.objects:
            if item.name[0:7] == "Terrain":
                self.terrainObject = item

        self.terrainVerts=diamondSquare(2**self.subdivisions,self.randomness,self.height/-2,self.height/2,self.seed,self.smoothAmount).verts

        if self.update_Erosion:
            erosion = thermalErosion(self.terrainVerts,self.erosionAmount,self.erosionSteps,self.erosionAngle,self.erosionIsInverted)
            self.terrainVerts = erosion.verts
            myGaussianBlur(self.terrainVerts,self.smoothnessAfterErosion)

        self.terrainObject = blenderOutput(self.terrainVerts,"Terrain",self.blenderSize)
        angleAndHeightMap = createAngleAndHeightMapOfTerrain(self.terrainObject)
        self.angleMap = angleAndHeightMap.angleMap
        #self.terrainObject.data.materials.append(self.terrainMaterial)

        if self.update_Seas:
            seas = createSeas(self.terrainObject,self.terrainVerts,self.waterSteps,self.rainAmount,self.evapAmount,self.waterSmoothing)
            self.seaMap = seas.seaMap

        if self.update_Forest:
            self.obstacleMap = [x[:] for x in [[int(0)]*self.size]*self.size]
            for x in range(len(self.seaMap)):
                for y in range(len(self.seaMap)):
                    self.obstacleMap[x][y] = self.seaMap[x][y]+self.riverMap[x][y]
            createForest(self.terrainObject, self.terrainVerts, self.angleMap,None,self.useGameOfLife, self.forestLimits, self.forestAngle, self.golSteps, self.minTreeHeight, self.startPercent)

        return {'FINISHED'}

#
#    Registration and so on.
#

def menu_func(self, context):
    self.layout.operator("mesh.primitive_landscape_add",
        text="Landscape",
        icon='RNDCURVE')

def register():
   bpy.utils.register_module(__name__)
   bpy.types.INFO_MT_mesh_add.prepend(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
