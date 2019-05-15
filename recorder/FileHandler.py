#!/usr/bin/python
# -*- coding:utf8 -*-

import os
import cv2
import time
from datetime import datetime
from multiprocessing.dummy import Process
from multiprocessing.dummy import Queue
from config.config import *
import shutil


class FileHandler(Process):
    def __init__(self):
        Process.__init__(self)
        self.deamon = True
        self.log_queue = Queue()
        self.alert_queue = Queue()
        self.image_queue = Queue()
        self.video_queue = Queue()
        self.raw_queue = Queue()
        self._max_cnt = 6000
        self.path = None
        self.image_path = None
        self.raw_fp = None
        self.log_fp = None
        self.alert_fp = None
        self.video_writer = None
        self.video_path = None
        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.recording = False
        self.start_time = None
        self.frame_cnt = 0
        self.frame_reset = True

    def run(self):
        # cnt = 0
        while True:
            # print(self.video_path)
            # print('---fileHandle process id----', os.getpid())
            if config.save.raw and self.raw_fp:
                while not self.raw_queue.empty():
                    # print('hahaha111')
                    timestamp, log_type, data = self.raw_queue.get()
                    tv_s = int(timestamp)
                    tv_us = (timestamp - tv_s) * 1000000
                    log_line = "%.10d %.6d " % (tv_s, tv_us) + log_type + ' ' + data + "\n"
                    # print(log_line, end='')
                    self.raw_fp.write(log_line)
                    self.raw_fp.flush()
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
 
            while config.save.video and not self.video_queue.empty() and self.video_path:
                frame_id, data = self.video_queue.get()
                # print(self.frame_cnt)
                if self.frame_cnt % self._max_cnt == 0 or self.frame_reset:
                    self.frame_reset = False
                    self.frame_cnt = 0
                    print("video start over.", self.frame_cnt)
                    if self.video_writer:
                        self.video_writer.release()
                    # self.video_writer.open(os.path.join(self.video_path, str(frame_id)+'.avi'), self.fourcc, 20.0, (1280, 720), True)
                    # else:
                    self.video_writer = cv2.VideoWriter(os.path.join(self.video_path, 'camera_{:08d}.avi'.format(frame_id)),
                            self.fourcc, 20.0, (1280, 720), True)
                self.video_writer.write(data)
                self.frame_cnt += 1
            time.sleep(0.01)

    def start_rec(self):
        FORMAT = '%Y%m%d%H%M%S'
        date = datetime.now().strftime(FORMAT)
        self.path = os.path.join(config.save.path, date)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        json.dump([collector0, collector1], open(os.path.join(self.path, 'config.json'), 'w+'), indent=True)
        # json.dump(install, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)
        shutil.copy('config/installation.json', os.path.join(self.path, 'installation.json'))

        if config.save.raw:
            self.raw_fp = open(os.path.join(self.path, 'log.txt'), 'w+')

        if config.save.log:
            self.log_fp = open(os.path.join(self.path, 'log.json'), 'w+')
        if config.save.alert:
            self.alert_fp = open(os.path.join(self.path, 'alert.json'), 'w+')
            self.image_path = os.path.join(self.path, 'image')
            if not os.path.exists(self.image_path):
                os.makedirs(self.image_path)

        if config.save.video:
            # self.video_writer = None
            self.video_path = os.path.join(self.path, 'video')
            if not os.path.exists(self.video_path):
                os.makedirs(self.video_path)
            # self.video_writer = cv2.VideoWriter(os.path.join(self.video_path, '0' + '.avi'),
            #                                     self.fourcc, 20.0, (1280, 720), True)
            # print(self.video_path)
        self.recording = True
        self.start_time = time.time()
        print('start recording.', self.recording)
        # self.start()

    def stop_rec(self):
        self.recording = False
        while not self.log_queue.empty():
            self.log_queue.get()
        while not self.raw_queue.empty():
            self.raw_queue.get()
        while not self.alert_queue.empty():
            self.alert_queue.get()
        while not self.video_queue.empty():
            self.video_queue.get()
        while not self.image_queue.empty():
            self.image_queue.get()
        if self.log_fp:
            self.log_fp.close()
        if self.raw_fp:
            self.raw_fp.close()
        if self.alert_fp:
            self.alert_fp.close()
        self.log_fp = None
        self.raw_fp = None
        self.alert_fp = None
        self.video_path = None
        self.start_time = None
        self.frame_reset = True
        print('stop recording.', self.recording, self.frame_cnt)

    def insert_log(self, msg):
        if config.save.log and self.recording:
            self.log_queue.put(msg)

    def insert_alert(self, msg):
        if config.save.alert and self.recording:
            self.alert_queue.put(msg)

    def insert_image(self, msg):
        if self.recording:
            self.image_queue.put(msg)

    def insert_video(self, msg):
        if config.save.video and self.recording:
            self.video_queue.put(msg)

    def insert_raw(self, msg):
        # print(self.recording)
        if config.save.raw and self.recording:
            # print('hahaha222')
            self.raw_queue.put(msg)

    # def insert_resolved(self, r):
    #     if config.save.raw and self.recording:

            # self.raw_queue.put(msg)

#
# class RawLogger(Process):
#     def __init__(self):
#         Process.__init__(self)
#         self.deamon = True
#         self.q = Queue()
#
#
