'''
source : Main.py
summary : Entry of program, every other code will be executed from here
          It will check initial state of execution environment too to
          see whether it is safe to run.
'''



import ER_EnumerateFiles as a
import userPLoader as loader
import glob
import os
import logging as log
import shutil
import datetime

log.basicConfig(filename="log\\main.log", level=log.INFO, format='%(asctime)s %(message)s')
log.info("==================================================================")
log.info("Main : Program started")

settings = loader.Load()
'''
<setting check> : check settings through logger
summary : enumerate settings and log
'''
#=======================================================
for i in range(0,6):
    log.info("Main : setting" + "[" + str(i) + "] = " + str(settings[i]))
#=======================================================



'''
<Initial state check> : Is there files to process.
summary : If there is nothing, program will stop.
'''
#=======================================================
dataPath = settings[5]
data = a.GetFiles(dataPath)
log.info("Main : Files to process = " + str(len(data)))
if(len(data) == 0):
    print("No files to process, stopping program.")
    print("Press enter to exit...")
    input()
    exit()
datn = open("datanames.txt", "w")
for i in data:
    datn.write(i + '\n')
datn.close()
#=======================================================



'''
<Initial state check> : Is there directories to save result.
summary : If there is no directories required, It will create one.
'''
#=======================================================
targetPath0 = os.path.join(settings[6], '1200')
targetPath1 = os.path.join(settings[6], '500')
targetPath2 = os.path.join(settings[6], '10')

log.info("Main : result path = " + str(targetPath0) + ", " + str(targetPath1)+ ", " + str(targetPath2))

if(os.path.isdir(settings[6]) == False):
    print("cannot find ", settings[6], " Creating...")
    log.info("Main : cannot find " + settings[6] + " Creating...")
    os.mkdir(settings[6])

if(os.path.isdir(targetPath0) == False):
    print("cannot find ", targetPath0, " Creating...")
    log.info("Main : cannot find " + targetPath0 + " Creating...")
    os.mkdir(targetPath0)

if(os.path.isdir(targetPath1) == False):
    print("cannot find ", targetPath1, " Creating...")
    log.info("Main : cannot find " + targetPath1 + " Creating...")
    os.mkdir(targetPath1)

if(os.path.isdir(targetPath2) == False):
    print("cannot find ", targetPath2, " Creating...")
    log.info("Main : cannot find " + targetPath2 + " Creating...")
    os.mkdir(targetPath2)
#=======================================================



'''
<Initial state check> : Is there any junk files in result folder.
summary : If there is, program will be stop and tell user to delete It manually.
'''
#=======================================================
trash = glob.glob(settings[6] + '/**/*.*', recursive=True)
log.info("Main : Trash found = " + str(len(trash)))
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
log.info("Main : searching for extraction file...")
if(os.path.isfile("extraction")):
    log.info("Main : extraction file found, HALT")
    print("<Important!>================<Important!>================<Important!>================<Important!>")
    print("Saved data file has been found.")
    print("This could be progress of current classification or aborted progress from previous classification.")
    print("If you are running new classificaion, please close program, and remove 'extraction' file manually, otherwise program will cause unexpected behaviour.")
    print("By pressing enter, you are confirming that this is re-enter from previous classificaion.")
    print("<Important!>================<Important!>================<Important!>================<Important!>")
    input()
    log.info("Main : resume check proceeded with consent")
else:
    log.info("Main : extraction not found")
#=======================================================


'''
<Running the program>
'''
#=======================================================
print("Extractor running...")
log.info("Main : Extractor running...")
import Extractor
print("Classifier running...")
log.info("Main : Classifier running...")
import Classifier
print("Remover running...")
log.info("Main : Remover running...")
import Remover
print("Remover1 running...")
log.info("Main : Remover1 running...")
import Remover1
print("Remover2 running...")
log.info("Main : Remover2 running...")
import Remover2
print("Picker running...")
log.info("Main : Picker running...")
import Picker
#=======================================================



'''
<Log collection>
'''
#=======================================================
print("Collecting logs...")
log.info("Main : Collecting logs...")
if(os.path.isdir("log") == False):
    os.mkdir("log")
shutil.copy("main.log", "log\\main.log")
shutil.copy("extraction", "log\\extraction")
shutil.copy("classification", "log\\classification")
shutil.copy("elimination", "log\\elimination")
shutil.copy("elimination1", "log\\elimination1")
shutil.copy("elimination2", "log\\elimination2")
shutil.copy("datanames.txt", "log\\datanames.txt")
shutil.make_archive("Log_" + str(datetime.datetime.now()).replace(':', '_'), "zip", "log")
#=======================================================




'''
<Data file clean up>
'''
#=======================================================
print("Removing data files...")
log.info("Main : Removing data files...")
os.remove("extraction")
os.remove("elimination")
os.remove("elimination1")
os.remove("elimination2")
os.remove("classification")
os.remove("datanames.txt")
#=======================================================



'''
<End of program>
'''
#=======================================================
print("Program Ended, Press enter to exit...")
log.info("Main : Program Ended, wait for user input")
input()
exit()
#=======================================================
