#!/usr/bin/python3
# -*- coding:utf8 -*-

import os
import cv2
from datetime import datetime
from multiprocessing import Process, Queue


def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)


class Recorder(object):
    def __init__(self, path=''):
        self._path = path
        self._writer = None

        if not os.path.exists(self._path):
            os.makedirs(self._path)
    
    def set_writer(self):
        pass
    
    def write(self, data):
        self._writer.write(data)

    def release(self):
        pass


class VideoRecorder(Recorder):
    def __init__(self, path):
        Recorder.__init__(self, path)
    
    def set_writer(self, file_name):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self._writer = cv2.VideoWriter(os.path.join(self._path, file_name+'.avi'),
                                       fourcc, 10.0, (1280, 720), True)
    
    def release(self):
        self._writer.release()


class TextRecorder(Recorder):
    def __init__(self, path):
        Recorder.__init__(self, path)
        self._cnt = 0
    
    def set_writer(self, file_name):
        self._writer = open(os.path.join(self._path, file_name+'.txt'), 'w+')
        self._cnt = 0

    def write(self, data):
        self._writer.write(data)
        self._cnt += 1
        if self._cnt % 100 == 0:
            self._writer.flush()

    def release(self):
        self._writer.close()