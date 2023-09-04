import os
import time
import datetime
import glob
import shutil

def Log(txt):
    file.write("[" + str(time.time()) + "]:" + txt + '\n')
    file.flush()
    os.fsync(file.fileno())

file = open("log.txt", "a")
Log("Log Started at " + str(datetime.datetime.now()))

def LoadInput():
    flag = 0
    if(os.path.exists("Input.txt") == False):
        print("Input.txt does not exist.")
        Log("Input not detected.")
        flag = 1
    folderName = open("Input.txt", "r").readlines()
    jpg = folderName[0].split('=')[1].replace('\n', '')
    raw = folderName[1].split('=')[1].replace('\n', '')
    Log("JPG target = " + jpg + ", RAW target = " + raw)
    return jpg, raw, flag

def GetNameOnly(jout, rout):
    jprc = []
    rprc = []
    for i in range(0, len(jout)):
        jprc.append(jout[i].split('\\')[-1].split('.')[0])
    for i in range(0, len(rout)):
        rprc.append(rout[i].split('\\')[-1].split('.')[0])
    Log("JPG total = " + str(len(jout)) + ", RAW total = " + str(len(rout)))
    return jprc, rprc
    
def main():
    if(os.path.isdir('result') == False):
        os.mkdir('result')
    jpg, raw, flag = LoadInput()
    if(flag == 1):
        return
    jout = glob.glob(jpg+'/**/*.jpg', recursive=True)
    rout = glob.glob(raw+'/**/*.raw', recursive=True)
    jprc, rprc = GetNameOnly(jout, rout)
    for i in range(0, len(rprc)):
        if((rprc[i] in jprc) == True):
            shutil.copyfile(rout[i], rout[i].replace(raw, 'result'))
            
    
    
main()
file.close()
