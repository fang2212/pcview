# -*- coding: utf-8 -*-

import cv2
import os
import numpy as np


#image_floder = "../../demo/1218siwei/20181219084633/image"
#video_path = "../../demo/1218siwei/20181219084633/1.avi"

#image_floder = "../../demo/1218siwei/20181218211304/image"
#video_path = "../../demo/1218siwei/20181218211304/1.avi"

image_floder = "../../demo/1218siwei/20181218211304/update/image"
video_path = "../../demo/1218siwei/20181218211304/2.avi"

frame_id = None

pack = os.path.join
image_list = os.listdir(image_floder)
def cmp(elem):
    return int(elem[0:-4])
image_list.sort(key=cmp)
print(image_list)

fourcc = cv2.VideoWriter_fourcc(*'XVID')

video_writer = cv2.VideoWriter(video_path,
                               fourcc, 20.0, (1280, 720), True)
for image_file in image_list:
    image = cv2.imread(pack(image_floder, image_file))
    cv2.imshow("test", image)
    cv2.waitKey(1)
    video_writer.write(image)

video_writer.release()
