#!/usr/bin/python
# -*- coding:utf8 -*-

import os
import cv2
import time
import json
from datetime import datetime
from multiprocessing import Process
from multiprocessing import Queue
from etc.config import config

class FileHandler(Process):
    def __init__(self):
        Process.__init__(self)
        self.deamon = True
        self.log_queue = Queue()
        self.alert_queue = Queue()
        self.image_queue = Queue()
        self.video_queue = Queue()
        self._max_cnt = 7000
 
        FORMAT = '%Y%m%d%H%M'
        date = datetime.now().strftime(FORMAT)
        self.path = os.path.join(config.save.path, date)
        os.makedirs(self.path)
 
        if config.save.log:
            self.log_fp = open(os.path.join(self.path, 'log.json'), 'w+')
        if config.save.alert:
            self.alert_fp = open(os.path.join(self.path, 'alert.json'), 'w+')
            self.image_path = os.path.join(self.path, 'image')
            os.makedirs(self.image_path)

        if config.save.video:
            self.video_writer = None
            self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.video_path = os.path.join(self.path, 'video')
            os.makedirs(self.video_path)

    def run(self):
        cnt = 0
        while True:
            # print('---fileHandle process id----', os.getpid())
            while config.save.log and not self.log_queue.empty():
                frame_id, data = self.log_queue.get() 
                self.log_fp.write(json.dumps(data) + '\n')
                self.log_fp.flush()
 
            if config.save.alert:
                while not self.alert_queue.empty():
                    frame_id, data = self.alert_queue.get()
                    self.alert_fp.write(json.dumps(data) + '\n')
                    self.alert_fp.flush()
 
                while not self.image_queue.empty():
                    image_index, data = self.image_queue.get() 
                    cv2.imwrite(os.path.join(self.image_path, str(image_index) +
                        '.jpg'), data)
 
            while config.save.video and not self.video_queue.empty():
                frame_id, data = self.video_queue.get() 
                if cnt % self._max_cnt == 0:
                    if self.video_writer:
                        self.video_writer.release()
                    self.video_writer = cv2.VideoWriter(os.path.join(self.video_path, 
                        str(cnt)+'.avi'),
                            self.fourcc, 20.0, (1280, 720), True)
                self.video_writer.write(data)
                cnt += 1
            time.sleep(0.02)
 
    def insert_log(self, msg):
        self.log_queue.put(msg)

    def insert_alert(self, msg):
        self.alert_queue.put(msg)

    def insert_image(self, msg):
        self.image_queue.put(msg)

    def insert_video(self, msg):
        self.video_queue.put(msg)
