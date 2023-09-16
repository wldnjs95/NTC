import os.path
import userPLoader as loader #New
import random

def Ten():
    pas = -1
    selected = random.sample(range(0, gl), 10)
    for i in range(0, len(line)):
        data = line[i].split(',')
        if(int(data[0]) in selected and int(data[0])!=pas):
            pas = int(data[0])
            file.write(line[i])

def TenLowGroup(num):
    f = 0
    pas = num - 1
    for i in range(0, len(line)+1):
        b = len(line) - 1 - i
        data = line[b].split(',')
        if(int(data[0]) == pas):
            pas -= 1
            if(f == 0):
                f = 1
                file.write(line[b] + "\n")
            else:
                file.write(line[b])
            line.remove(line[b])
    sel = random.sample(line, 11-num)
    for i in sel:
        file.write(i)

def LowGroupNoTen():
    for i in range(0, len(line)):
        file.write(line[i])

line=[]
if(os.path.isfile("elimination1") == True):
    read = open("elimination1", "r")
    line = read.readlines()
    read.close()
    print("<Remover2>Loaded Successfully :)")
else:
    print("<Remover2>Cannot find file :(")
    
file = open("elimination2", "w")

if(len(line)>=10):
    gl = int(line[len(line)-1].split(',')[0]) + 1
    if(gl>=10):
        Ten()
    else:
        TenLowGroup(gl)
else:
    LowGroupNoTen()
    

file.close()
