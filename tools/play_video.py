# -*- coding: utf-8 -*-

import cv2
import os
import numpy as np


cap = cv2.VideoCapture("1.HDV")


while cap.isOpened():
    # get a frame
    ret, frame = cap.read()
    # show a frame
    cv2.imshow("capture", frame)
    cv2.waitKey(50)

cap.release()
cv2.destroyAllWindows() 
