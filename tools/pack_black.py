# -*- coding: utf-8 -*-

import cv2
import os
import numpy as np


#image_floder = "../../demo/1218siwei/20181219084633/image"
#video_path = "../../demo/1218siwei/20181219084633/1.avi"

#image_floder = "../../demo/1218siwei/20181218211304/image"
#video_path = "../../demo/1218siwei/20181218211304/1.avi"

video_path = "1.mp4"

img = np.zeros((720, 1280, 3), np.uint8)
fourcc = cv2.VideoWriter_fourcc(*'XVID')

video_writer = cv2.VideoWriter(video_path,
                               fourcc, 20.0, (1280, 720), True)
for index in range(1000):
    video_writer.write(img)

video_writer.release()
