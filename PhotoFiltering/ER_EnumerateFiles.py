'''
source : ER_BlurryDetector.py
summary : Enumerates file following regular expression of path string
'''



import glob

def GetFiles(path):
    data = glob.glob(path)
    return data
