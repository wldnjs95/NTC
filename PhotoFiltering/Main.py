'''
source : Main.py
summary : Entry of program, every other code will be executed from here
          It will check initial state of execution environment too to
          see whether it is safe to run.
'''



import ER_EnumerateFiles as a
import userPLoader as loader#New
import glob
import os

settings = loader.Load()

'''
<Initial state check> : Is there files to process.
summary : If there is nothing, program will stop.
'''
#=======================================================
dataPath = settings[5]
data = a.GetFiles(dataPath)
if(len(data) == 0):
    print("No files to process, stopping program.")
    print("Press enter to exit...")
    input()
    exit()
#=======================================================



'''
<Initial state check> : Is there directories to save result.
summary : If there is no directories required, It will create one.
'''
#=======================================================
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
#=======================================================



'''
<Initial state check> : Is there any junk files in result folder.
summary : If there is, program will be stop and tell user to delete It manually.
'''
#=======================================================
trash = glob.glob(settings[6] + '/**/*.*', recursive=True)
if(len(trash) > 0):
    print("Please, clear files inside of " + settings[6] + " folder to avoid confusion.")
    print("Press enter to exit...")
    input()
    exit()
#=======================================================



'''
<Initial state check> : Is there any files in result folder.
summary : Since program cannot findout whether this run is for new dataset
          or continue for old dataset, It will take user input to check It.

'''
#=======================================================
if(os.path.isfile("extraction")):
    print("<Important!>================<Important!>================<Important!>================<Important!>")
    print("Saved data file has been found.")
    print("This could be progress of current classification or aborted progress from previous classification.")
    print("If you are running new classificaion, please close program, and remove 'extraction' file manually, otherwise program will cause unexpected behaviour.")
    print("By pressing enter, you are confirming that this is re-enter from previous classificaion.")
    print("<Important!>================<Important!>================<Important!>================<Important!>")
    input()
#=======================================================



'''
<Running the program>
'''
#=======================================================
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
#=======================================================



'''
<Data file clean up>
'''
#=======================================================
print("Removing data files...")
os.remove("extraction")
os.remove("elimination")
os.remove("elimination1")
os.remove("elimination2")
os.remove("classification")
#=======================================================



'''
<End of program>
'''
#=======================================================
print("Program Ended, Press enter to exit...")
input()
exit()
#=======================================================
