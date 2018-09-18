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
    def __init__(self, file_queue):
        Process.__init__(self)
        self.deamon = True
        self.file_queue = file_queue
        self._max_cnt = 6000
 
        FORMAT = '%Y%m%d%H%M%S'
        date_str = datetime.now().strftime(FORMAT)

        if config.save.result_path:
            self.path = config.save.result_path
        else:
            self.path = os.path.join(config.save.path, date_str)
            #self.path = config.save.path + date_str

        if not os.path.exists(self.path):
            os.makedirs(self.path)
 
        if config.save.log:
            self.log_fp = open(os.path.join(self.path, 'log.json'), 'w+')

        if config.save.alert:
            self.alert_fp = open(os.path.join(self.path, 'alert.json'), 'w+')
            self.image_path = os.path.join(self.path, 'image')
            if not os.path.exists(self.image_path):
                os.makedirs(self.image_path)

        if config.save.video:
            self.video_writer = None
            self.video_log = None
            self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_path = os.path.join(self.path, 'video')
            if not os.path.exists(self.video_path):
                os.makedirs(self.video_path)

    def run(self):
        cnt = 0
        while True:
            while not self.file_queue.empty():
                file_type, file_data = self.file_queue.get()
                if file_type == 'log':
                    self.log_fp.write(file_data + '\n')
                    if cnt % 100 == 0:
                        self.log_fp.flush()

                '''
                if file_type == 'alert':
                    while not self.alert_queue.empty():
                        frame_id, data = self.alert_queue.get()
                        self.alert_fp.write(json.dumps(data) + '\n')
                        self.alert_fp.flush()
    
                    while not self.image_queue.empty():
                        image_index, data = self.image_queue.get() 
                        cv2.imwrite(os.path.join(self.image_path, str(image_index) +
                            '.jpg'), data)
                '''
                
                if file_type == 'video':
                    frame_id, data = file_data 
                    if cnt % self._max_cnt == 0:
                        FORMAT = '%Y%m%d%H%M%S'
                        date_str = datetime.now().strftime(FORMAT)
                        if self.video_writer:
                            self.video_writer.release()
                        if self.video_log:
                            self.video_log.close()
                        self.video_writer = cv2.VideoWriter(os.path.join(self.video_path, date_str+'.avi'),
                                                            self.fourcc, 20.0, (1280, 720), True)
                        self.video_log = open(os.path.join(self.video_path, date_str+'.txt'), 'w+')
                    self.video_writer.write(data)
                    self.video_log.write(str(frame_id)+'\n')
                    if cnt % 100 == 0:
                        self.video_log.flush()
                    cnt += 1
            time.sleep(0.01)
 