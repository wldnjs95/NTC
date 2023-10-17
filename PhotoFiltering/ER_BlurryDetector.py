'''
source : ER_BlurryDetector.py
summary : Find relative blurryness based on laplacian variance.
          Note that this values are very sensitive to environmental noise,
          value will be useless on two different photos, but for similar two
          images, It is pretty meaningful :)
'''



import cv2
import numpy as np

#cv2 cannot handle unicode file name...2023/10/17 fixed
def imread_korean_path(path):
    with open(path, "rb") as fp:
        numpy_array = np.asarray(bytearray(fp.read()), dtype=np.uint8)
        return cv2.imdecode(numpy_array, cv2.IMREAD_UNCHANGED)

def GetBlurryness(img):
    return GetLaplacianVariance(imread_korean_path(img))
    #return GetLaplacianVariance(cv2.imread(img))

def GetLaplacianVariance(img):
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #cv2.imshow('greyscaled', grey)
    #cv2.waitKey(0)

    #Histogram Equalizer makes it weirder
    #hseq = cv2.equalizeHist(grey)
    #cv2.imshow('equalized', hseq)
    #cv2.waitKey(0)
    
    lpFiltered = cv2.Laplacian(grey, cv2.CV_64F)
    #cv2.imshow('filtered', lpFiltered)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return lpFiltered.var()
