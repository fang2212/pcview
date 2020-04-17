# !/usr/bin/python
# -*- coding:utf8 -*-

import socket
import time
import json
from threading import Thread
from queue import Queue

import numpy as np
import cv2


BUF_SIZE = 1280*720*20

class TcpSink(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.cache = []
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.connect((self.ip, self.port))

    def read_msg(self):
        buf = self.read(4)
        size = int.from_bytes(buf, byteorder="big", signed=False)
        buf = self.read(size)
        return buf

    def read(self, need_len):
        res = b''
        while need_len:
            if not self.cache:
                self.recv()
            len0 = len(self.cache[0])
            if len0 <= need_len:
                need_len -= len0
                res += self.cache[0]
                self.cache.pop(0)
            else:
                res += self.cache[0][0:need_len]
                self.cache[0] = self.cache[0][need_len:]
                need_len = 0
        return res
    
    def recv(self):
        tmp_buf = self.s.recv(BUF_SIZE)
        if not tmp_buf:
            print('remote close')
            self.s.close()
            return
        self.cache.append(tmp_buf)

    def run(self):
        while True:
            buf = self.read_msg()
            print(len(buf))
            time.sleep(0.01)

    def pkg_json(self, msg):
        res = json.loads(msg)
        frame_id = res['frame_id']
        #print('json', res)
        return frame_id, res

    def pkg_camera(self, msg):
        # frame_id = int.from_bytes(msg[16:20], byteorder="little", signed=False)
        # frame_id = int.from_bytes(msg[0:4], byteorder="little", signed=False)
        frame_id = 0
        # data = msg[4:]
        image = cv2.imdecode(np.fromstring(msg, np.uint8), cv2.IMREAD_COLOR)
        '''
        if self.pre_id and frame_id-self.pre_id != 1:
            print('jump: ', frame_id-self.pre_id)
        self.pre_id = frame_id
        '''
        return frame_id, image


if __name__ == '__main__':
    tcp_sink = TcpSink(ip='127.0.0.1', port=12032) #从nanomsg接收图像
    tcp_sink.run()