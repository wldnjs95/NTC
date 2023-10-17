'''
source : userPLoader.py
summary : Takes user preferences from "userPreferences.txt" located at the
          same path that program is running.

          <Output of Load() function>
          {
          settings[0] = pickType
          settings[1] = pickRatio(0~1)
          settings[2] = pickLimit
          *Now these three settings are meaningless since result are fixed to
           10/500/1200 images.

          
          settings[3] = blurContribute
          settings[4] = eyeContribute
          * These two settings are affecting to classification step

          
          settings[5] = targetPath (In regular expression use by glob)
          settings[6] = resultPath (name of result folder)
          }
'''



import os.path
import logging as log

log.basicConfig(filename="main.log", level=log.INFO, format='%(asctime)s %(message)s')
line=[]

def Load():
    log.info("userPLoader : Setting loaded by someone")
    if(os.path.isfile("userPreferences.txt") == True):
        read = open("userPreferences.txt", "r")
        line = read.readlines()
        read.close()
        print("User preferences Loaded Successfully :)")

        res=[]
        for i in range(0, 5):
            res.append(float(line[i].split('=')[1].replace('\n', '')))
        for i in range(5, 7):
            res.append(line[i].split('=')[1].replace('\n', ''))
        return res
    else:
        log.info("userPLoader : Cannot find setting file")
        print("Cannot find file :(")
        return None

