import os.path
import shutil
import userPLoader as loader#New

def Read(file):
    line=[]
    if(os.path.isfile(file) == True):
        read = open(file, "r")
        line = read.readlines()
        read.close()
        print("Loaded Successfully :)")
    else:
        print("Cannot find file :(")
    return line

settings = loader.Load()

l0 = Read("elimination")
l1 = Read("elimination1")
l2 = Read("elimination2")

targetPath0 = os.path.join(settings[6], '1200')
targetPath1 = os.path.join(settings[6], '500')
targetPath2 = os.path.join(settings[6], '10')

if(os.path.isdir(settings[6]) == False):
    print("cannot find ", settings[6], " Creating...")
    os.mkdir(settings[6])

if(os.path.isdir(targetPath0) == False):
    print("cannot find ", targetPath0, " Creating...")
    os.mkdir(targetPath0)

if(os.path.isdir(targetPath1) == False):
    print("cannot find ", targetPath1, " Creating...")
    os.mkdir(targetPath1)

if(os.path.isdir(targetPath2) == False):
    print("cannot find ", targetPath2, " Creating...")
    os.mkdir(targetPath2)

for i in range(0, len(l0)):
    data = l0[i].split(',')
    path = data[1]
    name = path.split('\\')[len(path.split('\\'))-1]
    shutil.copyfile(path, targetPath0 + '\\' + name)

for i in range(0, len(l1)):
    data = l1[i].split(',')
    path = data[1]
    name = path.split('\\')[len(path.split('\\'))-1]
    shutil.copyfile(path, targetPath1 + '\\' + name)

for i in range(0, len(l2)):
    data = l2[i].split(',')
    path = data[1]
    name = path.split('\\')[len(path.split('\\'))-1]
    shutil.copyfile(path, targetPath2 + '\\' + name)
    

print("Picking done")
