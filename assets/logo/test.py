import cv2
import numpy as np

img = np.zeros((100, 100, 3), np.uint8)
logo = cv2.imread('car.png')
y, x, _ = logo.shape
logo = cv2.addWeighted(img[0 : y, 0 : x], 1.0, logo, 0.5, 0.0, logo)
img[0 : y, 0 : x] = logo
cv2.imshow('img', img)
cv2.imwrite('save.png', img)
cv2.waitKey()
