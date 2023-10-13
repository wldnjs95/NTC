'''
source : Extractor.py
summary : Extracts feature with face feature detect model
'''



import ER_EnumerateFiles as a
import ER_SimilarityCheck as b
import ER_BlurryDetector as c
import ER_EyeBlinkDetector as d
import os.path
import userPLoader as loader#New

settings = loader.Load()
line = []
start = 0
isApend = 0
groupCount = 0
if(os.path.isfile("extraction") == True):
    read = open("extraction", "r")
    line = read.readlines()
    start = len(line)
    print(start)
    read.close()
    if(start != 0):
        print(line[start-1])
        groupCount = int(line[start-1].split(',')[0])
        isApend = 1
    
file = open("extraction", "a")

runCount = 0
groupSeparation=0
Threshold_similarity = 0.65
dataPath = settings[5]
data = a.GetFiles(dataPath)

for i in range(start, len(data)):

    try:
        blur = c.GetBlurryness(data[i])
        ear = d.Detect(data[i])
    
        if(isApend == 1):
            isApend = 0
            s = b.GetSimilarity(data[i-1], data[i])
            if(s < Threshold_similarity):
                print("{0}~{1}".format(groupSeparation, i))
                groupSeparation=i+1
                groupCount += 1
            file.write(str(groupCount) + ',' + data[i] + ',' + str(blur) + ',' + str(ear) + '\n')
            
        else:
            file.write(str(groupCount) + ',' + data[i] + ',' + str(blur) + ',' + str(ear) + '\n')
            s = b.GetSimilarity(data[i], data[i+1])
            print(data[i], data[i+1], s)
            if(s < Threshold_similarity):
                print("{0}~{1}".format(groupSeparation, i))
                groupSeparation=i+1
                groupCount += 1
    except:
        #It's the last photo
        #print("Except")
        #blur = c.GetBlurryness(data[i])
        #ear = d.Detect(data[i])
        #file.write(str(groupCount) + ',' + data[i] + ',' + str(blur) + ',' + str(ear) + '\n')
        file.close()
        break
        '''
        s = b.GetSimilarity(data[i-1], data[i])
        if(s < Threshold_similarity):
            print("{0}~{1}".format(groupSeparation, i))
            groupSeparation=i+1
            groupCount += 1
        file.write(str(groupCount) + ',' + data[i] + ',' + str(blur) + ',' + str(ear) + '\n')
        file.close()
        break
        '''
    
    if(runCount >= 10):
        file.close()
        print("Result Saved")
        runCount=0
        file = open("extraction", "a")
        
    runCount += 1

file.close()
