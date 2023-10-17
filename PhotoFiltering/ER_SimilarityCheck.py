'''
source : ER_SimilarityCheck.py
summary : Using histogram comparison, results similarity between two images,
          since It is sequence sensitive, and bigger value is meaningless,
          function will return smaller number.
'''



import cv2
import numpy as np
import matplotlib.pylab as plt

#cv2 cannot handle unicode file name...2023/10/17 fixed
def imread_korean_path(path):
    with open(path, "rb") as fp:
        numpy_array = np.asarray(bytearray(fp.read()), dtype=np.uint8)
        return cv2.imdecode(numpy_array, cv2.IMREAD_UNCHANGED)

def GetSimilaritySeqSens(img1, img2):
    
    imgs = []
    #imgs.append(cv2.imread('C:/Users/soo/Desktop/test_Portrait.jpg'))
    #imgs.append(cv2.imread('C:/Users/soo/Desktop/test_ClosedEyes.jpg'))
    #imgs.append(cv2.imread('C:/Users/soo/Desktop/test_Portrait_Blurred.jpg'))
    imgs.append(imread_korean_path(img1))
    imgs.append(imread_korean_path(img2))

    if(imgs[0].shape != imgs[1].shape):
        return -1
    
    hists = []

    for img in imgs:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX) 
        hists.append(hist)

    method = 2
    query = hists[0]
    ret = cv2.compareHist(query, hists[1], method)

    if method == cv2.HISTCMP_INTERSECT:
        ret = ret/np.sum(query)   

    return ret

def GetSimilarity(img1, img2):
    a = GetSimilaritySeqSens(img1, img2)
    b = GetSimilaritySeqSens(img2, img1)
    if(a<b):
        return a
    else:
        return b
