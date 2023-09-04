import sys
import os
import dlib
import glob
import math

import cv2

def Dist(p1, p2):
    return math.sqrt(math.pow(p1.x-p2.x, 2) + math.pow(p1.y-p2.y, 2))

def Detect(f):
    predictor_path = "shape_predictor_68_face_landmarks.dat"
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    print("Processing file: {}".format(f))
    #img = dlib.load_rgb_image(f)
    img = cv2.imread(f)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Ask the detector to find the bounding boxes of each face. The 1 in the
    # second argument indicates that we should upsample the image 1 time. This
    # will make everything bigger and allow us to detect more faces.
    dets = detector(img, 1)
    print("Number of faces detected: {}".format(len(dets)))
    minEAR = 0
    for k, d in enumerate(dets):
        print("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(
            k, d.left(), d.top(), d.right(), d.bottom()))
        # Get the landmarks/parts for the face in box d.
        shape = predictor(img, d)
        LhZ = Dist(shape.part(36), shape.part(39))#LeftEyeFromViewerPerspective
        LvL = Dist(shape.part(37), shape.part(41))
        LvR = Dist(shape.part(38), shape.part(40))
        LEAR = (LvL+LvR)/LhZ
        #print(LEAR)

        RhZ = Dist(shape.part(42), shape.part(45))#RightEyeFromViewerPerspective
        RvL = Dist(shape.part(43), shape.part(47))
        RvR = Dist(shape.part(44), shape.part(46))
        REAR = (RvL+RvR)/RhZ
        #print(REAR)

        if(LEAR > REAR):
            minEAR = REAR
        else:
            minEAR = LEAR
    return minEAR
