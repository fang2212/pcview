
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

BUF_SIZE = 1280*720*20

def get_all_file(path):
    files = os.listdir(path)
    res = []
    for file in files:
        file_path = pack(path, file)
        if os.path.isfile(file_path):
            res.append(file_path)
        elif os.path.isdir(file_path):
            res += get_all_file(file_path)
    return res
        
def read_lines(path):
    with open(path, 'r') as fp:
        return fp.readlines()

class FlowReader(object):
    def __init__(self, path):
        self.files = get_all_file(path)
        self.videos = []
        self.time_log = {}
        self.gen = None
        self.init()

    def init(self):
        for file in self.files:
            if file.endswith('.mp4') or file.endswith('.avi'):
                self.videos.append(file)
        self.videos.sort()
        self.gen = self.gen_output()

    def gen_output(self):
        for video in self.videos:
            cap = cv2.VideoCapture(video)
            log_path = video[:-3]+'txt'
            log = []
            if os.path.exists(log_path):
                log = read_lines(log_path)
            index = 0
            log_len = len(log)

            while cap.isOpened():
                ret, frame = cap.read()
                if index < log_len:
                    msg = json.loads(log[index])
                else:
                    msg = {}
                index += 1
                if not ret:
                    break
                yield True, frame, msg
            cap.release()
        yield False, -1, -1

    def output(self):
        val0, val1, val2 = next(self.gen)
        if not val0:
            self.gen = self.gen_output()
        return val0, val1, val2