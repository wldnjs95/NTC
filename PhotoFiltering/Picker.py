'''
source : Picker.py
summary : Copies pictures by result of removers
'''



import os.path
import shutil
import userPLoader as loader#New
import logging as log #New

log.basicConfig(filename="main.log", level=log.INFO, format='%(asctime)s %(message)s')

def Read(file):
    line=[]
    if(os.path.isfile(file) == True):
        read = open(file, "r")
        line = read.readlines()
        read.close()
        print("<Picker>Loaded Successfully :)")
        log.info("Picker : " + str(file) + " found")
    else:
        print("<Picker>Cannot find file :(")
        log.info("Picker : classification found")
        log.info("Picker : " + str(file) + " not found")
    return line

settings = loader.Load()

l0 = Read("elimination")
l1 = Read("elimination1")
l2 = Read("elimination2")

targetPath0 = os.path.join(settings[6], '1200')
targetPath1 = os.path.join(settings[6], '500')
targetPath2 = os.path.join(settings[6], '10')

'''
freeze in picking 1200 detected
-> elimination had duplication
-> classification had duplication, causing every data that are created after this had duplication
-> possibly program started several times while copying, causing duplication in classification fil
=> every data file except 'extraction' will be written with property 'w', not 'a'

-> possibly there was not enough data storage, causing program stop.
=> picker checks left storage before copy
'''

print("<Picker>Checking system storage...")
totalSize = 0
for i in range(0, len(l0)):
    totalSize += os.path.getsize(l0[i].split(',')[1])
for i in range(0, len(l1)):
    totalSize += os.path.getsize(l1[i].split(',')[1])
for i in range(0, len(l2)):
    totalSize += os.path.getsize(l2[i].split(',')[1])
total, used, free = shutil.disk_usage("/")
if(free < totalSize):
    log.info("Picker : Not enough storage space to copy files")
    print("Not enough space in paste path...")
    print("Press enter to exit...")
    input()
    exit()
log.info("Picker : Storage space check passed")
    
print("Picking 1200 images...")
for i in range(0, len(l0)):
    data = l0[i].split(',')
    path = data[1]
    name = path.split('\\')[len(path.split('\\'))-1]
    shutil.copyfile(path, targetPath0 + '\\' + name)
log.info("Picker : 1200 copied")

print("Picking 500 images...")
for i in range(0, len(l1)):
    data = l1[i].split(',')
    path = data[1]
    name = path.split('\\')[len(path.split('\\'))-1]
    shutil.copyfile(path, targetPath1 + '\\' + name)
log.info("Picker : 500 copied")

print("Picking 10 images...")
for i in range(0, len(l2)):
    data = l2[i].split(',')
    path = data[1]
    name = path.split('\\')[len(path.split('\\'))-1]
    shutil.copyfile(path, targetPath2 + '\\' + name)
log.info("Picker : 10 copied")

print("Picking done")
log.info("Picker : Picking done")
