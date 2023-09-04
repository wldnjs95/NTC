import os.path

line=[]

pt=0
pr=0
pl=0
bc=0
ec=0

if(os.path.isfile("userPreferences.txt") == True):
    read = open("userPreferences.txt", "r")
    line = read.readlines()
    read.close()
    print("User preferences Loaded Successfully :)")
else:
    print("Cannot find file :(")
"""
for p in range(0,5):
    output = float(line[p].split('=')[1].replace('\n', ''))
    print(output)
"""
def Load():
    if(os.path.isfile("userPreferences.txt") == True):
        read = open("userPreferences.txt", "r")
        line = read.readlines()
        read.close()
        print("User preferences Loaded Successfully :)")
    else:
        print("Cannot find file :(")
    res=[]
    for i in range(0, 5):
        res.append(float(line[i].split('=')[1].replace('\n', '')))
    for i in range(5, 7):
        res.append(line[i].split('=')[1].replace('\n', ''))
    return res

