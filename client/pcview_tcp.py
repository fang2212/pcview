#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import socket
import sys
import logging
import time
import nanomsg
import msgpack
import json
from datetime import datetime
from multiprocessing import Process, Queue, Value

import asyncio
import numpy as np
import cv2

from .draw import Player
from etc.config import config

from .file_handler import FileHandler
pack = os.path.join
logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')  # logging.basicConfig函数对日志的输出格式及方式做相关配置

def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):      return data.decode('ascii')
    if isinstance(data, dict):       return dict(map(convert, data.items()))
    if isinstance(data, tuple):      return tuple(map(convert, data))
    if isinstance(data, list):       return list(map(convert, data))
    if isinstance(data, set):        return set(map(convert, data))
    return data

buf_size = 1280*720*20

class TcpSink(Process):
    def __init__(self, ip, port, mess_queue):
        Process.__init__(self)
        self.deamon = True
        self.ip = ip
        self.port = port
        self.cache = []
        self.queue = mess_queue
        self.s = None
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.connect((self.ip, self.port))

    def read_msg(self):
        buf = self.read(4)
        size = int.from_bytes(buf, byteorder="big", signed=False)
        # print('read size', size)
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
        self.cache.append(self.s.recv(buf_size))

    def run(self):
        while True:
            res = {
                'frame_id': None,
                'img': None,
                'vehicle': {},
                'lane': {},
                'ped': {},
                'tsr': {},
                'cali': {},
                'can': {},
                'extra': {}
            }
            for msg_type in ['camera', 'lane', 'vehicle', 'tsr', 'ped']:
                buf = self.read_msg()
                if len(buf) > 5:
                    if msg_type == 'camera':
                        frame_id, data = self.pkg_camera(buf)
                        res['img'] = data
                    else:
                        frame_id, data = self.pkg_alg(buf)
                        res[msg_type] = data
                    res['frame_id'] = frame_id
            # print('frame_id', res['frame_id'])
            self.queue.put(res)

    def pkg_alg(self, msg):
        data = msgpack.loads(msg)
        # print(msg)
        # data = msgpack.unpackb(msg)
        res = convert(data)
        # print(res)
        frame_id = res['frame_id']
        return frame_id, res

    def pkg_camera(self, msg):
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        data = msg[24:]
        image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
        # cv2.imshow('UI', image)
        # cv2.waitKey(1)
        # print('camera', frame_id)
        return frame_id, image


class PCView(object):
    
    def __init__(self):
        self.res_queue = Queue()    #处理结果，绘图数据队列

        self.tcp_sink = TcpSink(ip='127.0.0.1', port=20001, mess_queue=self.res_queue) #从nanomsg接收图像
        
        self.pc_draw = PCDraw(mess_queue=self.res_queue) #绘图进程

    def go(self):
        self.tcp_sink.start()
        self.pc_draw.start()

class PCDraw(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        print('init draw')
        self.player = Player()

    def run(self):
        print('run abcdef')
        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                print('draw process', mess['frame_id'])
                img = Player().draw(mess)
                cv2.imshow('UI', img)
                cv2.waitKey(1)
            time.sleep(0.01)
        #cv2.destroyAllWindows()