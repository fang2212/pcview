# -*- coding: utf-8 -*-

import cv2
import os
import sys
import numpy as np


#image_floder = "../../demo/1218siwei/20181219084633/image"
#video_path = "../../demo/1218siwei/20181219084633/1.avi"

#image_floder = "../../demo/1218siwei/20181218211304/image"
#video_path = "../../demo/1218siwei/20181218211304/1.avi"

print(sys.path)
video_path = os.path.join(sys.path[0], "1.mp4")
video_path = 'D:\\test\\1.mp4'
print(video_path)

with open(video_path+'.txt', 'w+') as fp:
    fp.write('hello')

img = np.zeros((720, 1280, 3), np.uint8)
fourcc = cv2.VideoWriter_fourcc(*'XVID')

video_writer = cv2.VideoWriter(video_path,
                               fourcc, 20.0, (1280, 720), True)
for index in range(100):
    cv2.imshow('hello', img)
    cv2.waitKey(10)
    video_writer.write(img)


video_writer.release()
