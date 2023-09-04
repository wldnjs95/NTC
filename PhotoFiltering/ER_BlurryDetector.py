import cv2

def GetBlurryness(img):
    return GetLaplacianVariance(cv2.imread(img))

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
