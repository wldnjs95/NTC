'''
source : Classifier.py
summary : from extracted feature, It creates normalized scalar for order photos by total score(per Group)
'''



import os.path
import userPLoader as loader#New
import logging as log #New

log.basicConfig(filename="main.log", level=log.INFO, format='%(asctime)s %(message)s')

line=[]
if(os.path.isfile("extraction") == True):
    read = open("extraction", "r")
    line = read.readlines()
    read.close()
    print("<Classifier>Loaded Successfully :)")
    log.info("Classifier : extraction file found")
else:
    print("<Classifier>Cannot find file :(")
    log.info("Classifier : extraction file not found")

print("<Classifier>" + str(len(line)) + " of photoes are going to be processed")
log.info("Classifier : data length = " + str(len(line)))

file = open("classification", "w")
curGroup = '0'
groups = []
maxVar=0
maxEar=0
memCount=0

settings = loader.Load()#New
blurCont = settings[3]#0.5
earCont = settings[4]

for i in range(0, len(line)):
    data = line[i].split(',')
    group = data[0]
    path = data[1]
    blur = float(data[2])
    ear = float(data[3])
    
    #print("%s, %s"%(group, curGroup))
    if(curGroup == group):
        groups.append(line[i])
        memCount+=1
        maxVar+=blur
        maxEar+=ear
        #print("Svaed")
    else:
        #print("G:%s, MC:%s, maxV:%f, maxE:%f"%(curGroup, memCount, maxVar, maxEar))
        for j in range(0, len(groups)):
            #print(groups[j])
            data1 = groups[j].split(',')
            group1 = data1[0]
            path1 = data1[1]
            blur1 = float(data1[2])
            ear1 = float(data1[3])
            normalizedBlur=0
            normalizedEar=1
            if(maxVar != 0):
                normalizedBlur = 1-blur1/maxVar
            if(maxEar != 0):
                normalizedEar = ear1/maxEar
            file.write(group1 + ',' + path1 + ',' + str(normalizedBlur) + ',' + str(normalizedEar) + ',' + str(blurCont * normalizedBlur + earCont * normalizedEar) + '\n')

        #reset
        curGroup = group
        groups.clear()
        groups.append(line[i])
        maxVar=blur
        maxEar=ear
        memCount=0

#print("G:%s, MC:%s, maxV:%f, maxE:%f"%(curGroup, memCount, maxVar, maxEar))
for j in range(0, len(groups)):
    #print(groups[j])
    data1 = groups[j].split(',')
    group1 = data1[0]
    path1 = data1[1]
    blur1 = float(data1[2])
    ear1 = float(data1[3])
    normalizedBlur=0
    normalizedEar=0
    if(maxVar != 0):
        normalizedBlur = 1-blur1/maxVar
    if(maxEar != 0):
        normalizedEar = ear1/maxEar
    file.write(group1 + ',' + path1 + ',' + str(normalizedBlur) + ',' + str(normalizedEar) + ',' + str(blurCont * normalizedBlur + earCont * normalizedEar) + '\n')
file.close()
