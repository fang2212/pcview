#.!/usr/bin/python
#coding:utf-8

import numpy as np
from multiprocessing import Process, Queue
import cv2
import msgpack
from sink import aebSink
from player import aeb_player
import json


class ReplaySink(aebSink.LibFlowSink):
    def __init__(self, mess_queue, logtxt):
        aebSink.LibFlowSink.__init__(self, None, None, mess_queue)
        self.mess_queue = mess_queue
        self.logtxt = logtxt

    def run(self):
        with open(self.logtxt, 'r') as f:
            for line in f:
                self.mess_queue.put(eval(line))


def main(aeb_sink, mess_queue):

    player = aeb_player.Player()
    aeb_sync = aebSink.Sync(mess_queue)
    aeb_sink.start()
    while True:
        data_list = aeb_sync.pop_simple()
        # print(data_list)
        if not data_list:
            continue
        ipm = np.zeros([720, 480, 3], np.uint8)
        ipm[:, :] = [166, 166, 166]

        img = np.array([[x] for x in data_list[0]['image']['data']], dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        player.draw(img, ipm, data_list[1])
        # cv2.imshow(img)
        img = np.hstack((img, ipm))
        cv2.imshow("img", img)
        cv2.waitKey(1)


if __name__ == '__main__':
    url = "ws://127.0.0.1:1234"
    topic = "pcview"
    logtxt = "./aeb_log/20190516124844.txt"
    mess_queue = Queue()

    # 采集
    # aeb_sink = aebSink.LibFlowSink(url, topic, mess_queue)

    # 回放
    aeb_sink = ReplaySink(mess_queue, logtxt)
    main(aeb_sink, mess_queue)
