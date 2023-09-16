import os.path
import userPLoader as loader #New

line=[]
if(os.path.isfile("classification") == True):
    read = open("classification", "r")
    line = read.readlines()
    read.close()
    print("<Remover1>Loaded Successfully :)")
else:
    print("<Remover1>Cannot find file :(")

print("<Remover1>" + str(len(line)) + " of photoes are going to be processed")

file = open("elimination1", "w")
curGroup = '0'
groups = []

settings = loader.Load()#New
pickRatio = 500/len(line)
if(pickRatio>1):
    pickRatio=1

for i in range(0, len(line)):
    data = line[i].split(',')
    group = data[0]
    
    #print("%s, %s"%(group, curGroup))
    if(curGroup == group):
        groups.append(line[i])
        #print("Svaed")
    else:
        sortGroup=[]
        for j in range(0, len(groups)):
            data1 = groups[j].split(',')
            group1 = data1[0]
            path1 = data1[1]
            scr1 = float(data1[2])
            mem=[group1, path1, scr1]
            sortGroup.append(mem)
        sortGroup.sort(key=lambda i:i[2])
        t = round(len(sortGroup)*pickRatio)
        if(t < 1):
            t = 1
        for k in range(0, t):
            #print(sortGroup[k])
            group1 = sortGroup[k][0]
            path1 = sortGroup[k][1]
            scr1 = sortGroup[k][2]
            file.write(group1 + ',' + path1 + ',' + str(scr1) + '\n')

        #reset
        curGroup = group
        groups.clear()
        groups.append(line[i])

sortGroup=[]
for j in range(0, len(groups)):
    data1 = groups[j].split(',')
    group1 = data1[0]
    path1 = data1[1]
    scr1 = float(data1[2])
    mem=[group1, path1, scr1]
    sortGroup.append(mem)
sortGroup.sort(key=lambda i:i[2])
t = round(len(sortGroup)*pickRatio)
if(t < 1):
    t = 1
for j in range(0, t):
    group1 = sortGroup[j][0]
    path1 = sortGroup[j][1]
    scr1 = sortGroup[j][2]
    file.write(group1 + ',' + path1 + ',' + str(scr1) + '\n')


file.close()
