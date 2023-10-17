'''
source : ER_BlurryDetector.py
summary : Enumerates file following regular expression of path string
'''



import glob
import logging as log #New

log.basicConfig(filename="main.log", level=log.INFO, format='%(asctime)s %(message)s')

def GetFiles(path):
    data = glob.glob(path)
    log.info("ER_EnumerateFiles : GetFiles() called at " + str(path))
    log.info("ER_EnumerateFiles : results length = " + str(len(data)))
    return data
