#EnumerateFile
import glob

def GetFiles(path):
    data = glob.glob(path)
    return data
