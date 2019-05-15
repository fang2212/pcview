#!/usr/bin/python3
# -*- coding:utf8 -*-

import os
import cv2
from datetime import datetime
from multiprocessing import Process, Queue


def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

def get_video_str():
    now = datetime.now()
    FORMAT = 'rec_%Y%m%d%H%M_'
    return now.strftime(FORMAT) + str(now.microsecond).zfill(6)

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


pack = os.path.join
class Collector(object):
    def __init__(self, path, period=9000, fps=30, w=720, h=480, type='.avi'):
        self.fps = fps
        self.w = w
        self.h = h
        self.period = period
        self.path = path
        self.type = type
        if type == '.mp4':
            self.fourcc = cv2.VideoWriter_fourcc(*'H264')
        else:
            self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.inc = 0
        self.log_fp = open(pack(path, 'log.txt'), 'w+') 
        self.video_fp = None

    def write(self, data):
        if 'camera' in data:
            image = data['camera']['image']
            ts = int(data['camera']['create_ts'])
            ta = ts // 1000000
            tb = str(ts % 1000000).zfill(6)
            if self.inc % self.period == 0:
                if self.video_fp:
                    self.video_fp.release()
                self.video_name = get_video_str()+self.type
                self.video_fp = cv2.VideoWriter(pack(self.path, self.video_name),
                                                self.fourcc, self.fps, (self.w, self.h), True)
            if 'speed' in data:
                str_ = '{} {} speed {}'.format(ta, tb, data.get('speed'))
                print(str_, file=self.log_fp)
            if 'turnlamp' in data:
                str_ = '{} {} turnlamp {}'.format(ta, tb, data.get('turnlamp'))
                print(str_, file=self.log_fp)
            str_ = '{} {} cam_frame {} {}'.format(ta, tb, self.video_name,
                                                 self.inc % self.period)
            print(str_, file=self.log_fp)
            print('--- write log ---')
            if self.inc % 100 == 0:
                self.log_fp.flush()
                print('****'*10, 'write log flush', '****'*10)
            self.video_fp.write(image)
            self.inc += 1
                

    
class VideoRecorder(Recorder):
    def __init__(self, path, fps=10):
        Recorder.__init__(self, path)
        self.fps = fps
    
    def set_writer(self, file_name, w=1280, h=720):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self._writer = cv2.VideoWriter(os.path.join(self._path, file_name+'.avi'),
                                       fourcc, self.fps, (w, h), True)
    
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