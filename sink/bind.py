
#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import socket
import logging
import time
import msgpack
import json
from datetime import datetime

import asyncio
import websockets
import numpy as np
import cv2

from .sync import Sync

pack = os.path.join


class SinkError:
    Closed = 32


BUF_SIZE = 1280*720*20

def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):  return data.decode('ascii')
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return tuple(map(convert, data))
    if isinstance(data, list):   return list(map(convert, data))
    if isinstance(data, set):    return set(map(convert, data))
    return data

class TcpSink(object):
    '''
    '''
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
        # print(tmp_buf)
        if not tmp_buf:
            print('remote close')
            self.s.close()
            return
        self.cache.append(tmp_buf)

    def pkg_alg(self, msg):
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        return frame_id, res

    def pkg_camera(self, msg):
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        data = msg[24:]
        image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
        return frame_id, image
    '''
    def run(self):
        new_pack = {}
        new_id = -1
        sync = Sync(4)
        while True:
            data = self.read_msg()
            msg = msgpack.unpackb(data, use_list=False)
            topic = msg[b'topic'].decode('ascii')
            mp_header = (msg[b'data'][0:2] == b'\x82\xa8' or msg[b'data'][0:2] == b'\x83\xab')
            # print(mp_header, msg[b'data'][0:2])
            if mp_header:
                data = msgpack.unpackb(msg[b'data'], use_list=False)
            else:
                data = msg[b'data']
            if b'image_frame_id' in data:
                image = cv2.imdecode(np.fromstring(data[b'image'], np.uint8), cv2.IMREAD_COLOR)
                data = {
                    'camera': {
                        'image': image,
                        'create_ts': data[b'camera_time']
                    },
                    'frame_id': data[b'image_frame_id'],
                }
            elif b'frame_id' in data:
                data = convert(data)
            else:
                frame_id = int.from_bytes(data[4:8], byteorder="little", signed=False)
                data = data[24:]
                image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
                data = {
                    'camera': {
                        'image': image,
                    },
                    'frame_id': frame_id
                }
            
            pops = sync.append(data)

            for data in pops:
                frame_id = data['frame_id']
                # print(frame_id)
                if new_id != frame_id:
                    self.msg_queue.put(new_pack)
                    new_pack = data
                    new_id = data['frame_id']
                elif new_id == data['frame_id']:
                    for key in data:
                        if key != 'frame_id':
                            new_pack[key] = data[key]
    '''