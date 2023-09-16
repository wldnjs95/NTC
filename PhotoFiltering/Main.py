import userPLoader as loader#New
import glob
import os

settings = loader.Load()

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

trash = glob.glob(settings[6] + '/**/*.*', recursive=True)
if(len(trash) > 0):
    print("Please, clear files inside of " + settings[6] + " folder to avoid confusion.")
    print("Press enter to exit...")
    input()
    exit()

print("Extractor running...")
import Extractor
print("Classifier running...")
import Classifier
print("Remover running...")
import Remover
print("Remover1 running...")
import Remover1
print("Remover2 running...")
import Remover2
print("Picker running...")
import Picker

os.remove("extraction")
os.remove("elimination")
os.remove("elimination1")
os.remove("elimination2")
os.remove("classification")

