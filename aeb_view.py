#.!/usr/bin/python
#coding:utf-8

import numpy as np
from multiprocessing import Process, Queue
import cv2

from sink import aebSink
from player import aeb_player


def main(saved_path=None):
    mess_queue = Queue()
    aeb_sink = aebSink.LibFlowSink(url, topic, mess_queue)
    player = aeb_player.Player()
    aeb_sync = aebSink.Sync(mess_queue)
    aeb_sink.start()
    while True:
        data_list = aeb_sync.pop_simple()
        # print(data_list)
        if not data_list:
            continue
        ipm = np.zeros([720, 480, 3], np.uint8)
        img = np.zeros([720, 1280, 3], np.uint8)
        player.draw(img, ipm, data_list)
        # cv2.imshow(img)
        img = np.hstack((img, ipm))
        cv2.imshow("img", img)
        cv2.waitKey(1)

def replay():
    pass


if __name__ == '__main__':
    url = "ws://127.0.0.1:1234"
    topic = "pcview"
    main()
