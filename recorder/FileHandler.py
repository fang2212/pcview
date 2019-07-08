#!/usr/bin/python
# -*- coding:utf8 -*-
import os
import cv2
import time
from datetime import datetime
from multiprocessing.dummy import Process as Thread
from multiprocessing import Queue, Process
from config.config import local_cfg, configs, install
import sys
import json
import numpy as np


class FileHandler(Thread):
    def __init__(self, redirect=False):
        super(FileHandler, self).__init__()
        self.deamon = True
        # self.log_queue = Queue()
        self.ctrl_queue = Queue()
        # self.image_queue = Queue()
        self.video_queue = Queue(maxsize=40)
        self.raw_queue = Queue(maxsize=5000)
        self.pcv_queue = Queue(maxsize=5000)

        # self.can_raw_queue = kqueue(maxsize=100)
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
        self.redirect = redirect

        self.last_image_q = Queue(maxsize=5)


        print('outer id:', os.getpid())

    def run(self):
        # cnt = 0
        raw_fp = None
        pcv_fp = None

        path = None
        video_path = None
        frame_cnt = 0
        frame_reset = True
        video_writer = None
        # can_queue = deque(maxlen=2000)
        print('inner id:', os.getpid())
        state = 'stop'
        origin_stdout = sys.stdout


        while True:
            now_time = time.time()
            if self.recording and now_time - self.start_time > 600:
                self.stop_rec()
                self.start_rec()
                self.start_time = now_time

            if not self.ctrl_queue.empty():
                ctrl = self.ctrl_queue.get()
                if ctrl['act'] == 'start':

                    path = ctrl['path']
                    video_path = ctrl['video_path']
                    raw_fp = open(os.path.join(path, 'log.txt'), 'w+')
                    pcv_fp = open(os.path.join(path, 'pcv_log.txt'), 'w+')

                    stdout_fp = open(os.path.join(path, 'stdout.txt'), 'w+')
                    sys.stdout = stdout_fp
                    state = 'start'

                    while not self.raw_queue.empty():
                        self.raw_queue.get()

                    while not self.video_queue.empty():
                        self.video_queue.get()

                    while not self.pcv_queue.empty():
                        self.pcv_queue.get()

                elif ctrl['act'] == 'stop':
                    raw_fp.flush()
                    raw_fp.close()
                    raw_fp = None

                    pcv_fp.flush()
                    pcv_fp.close()
                    pcv_fp = None

                    frame_reset = True
                    sys.stdout = origin_stdout
                    state = 'stop'
                    while not self.video_queue.empty():
                        self.video_queue.get()

                    while not self.raw_queue.empty():
                        self.raw_queue.get()

                    while not self.pcv_queue.empty():
                        self.pcv_queue.get()


            # print(self.video_path)
            # print('---fileHandle process id----', os.getpid())
            # print(config.save.raw, raw_fp)
            if local_cfg.save.raw and raw_fp:
                while not self.raw_queue.empty():
                    timestamp, log_type, data = self.raw_queue.get()
                    tv_s = int(timestamp)
                    tv_us = (timestamp - tv_s) * 1000000
                    log_line = "%.10d %.6d " % (tv_s, tv_us) + log_type + ' ' + data + "\n"
                    # print(log_line, end='')
                    # print(log_line)
                    raw_fp.write(log_line)
                    raw_fp.flush()
                    # print('end ............')

                while not self.pcv_queue.empty():
                    data = self.pcv_queue.get()
                    pcv_fp.write(data)
                    pcv_fp.flush()


            # print('filehandler...', video_path, self.video_queue.qsize())
            while local_cfg.save.video and not self.video_queue.empty() and video_path:
                ts, frame_id, data = self.video_queue.get()
                # print(self.frame_cnt)
                if frame_cnt % self._max_cnt == 0 or frame_reset:
                    frame_reset = False
                    frame_cnt = 0
                    vpath = os.path.join(video_path, 'camera_{:08d}.avi'.format(frame_id))
                    print("video start over.", frame_cnt, vpath)
                    if video_writer:
                        video_writer.release()

                    video_writer = cv2.VideoWriter(vpath,
                                                   self.fourcc, 20.0, (1280, 720), True)
                img = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
                video_writer.write(img)
                tv_s = int(ts)
                tv_us = (ts - tv_s) * 1000000
                log_line = "%.10d %.6d " % (tv_s, tv_us) + 'camera' + ' ' + '{}'.format(frame_id) + "\n"
                if raw_fp:
                    raw_fp.write(log_line)

                frame_cnt += 1
            time.sleep(0.01)


    def start_rec(self, rlog=None):
        FORMAT = '%Y%m%d%H%M%S'
        date = datetime.now().strftime(FORMAT)
        if rlog:
            self.path = os.path.join(os.path.dirname(rlog), 'clip_' + date)
        else:
            self.path = os.path.join(local_cfg.log_root, date)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if not rlog:
            json.dump(configs, open(os.path.join(self.path, 'config.json'), 'w+'), indent=True)
            # json.dump(install, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)
            # shutil.copy('etc/installation.json', os.path.join(self.path, 'installation.json'))
            json.dump(install, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)

        if local_cfg.save.video:
            # self.video_writer = None
            self.video_path = os.path.join(self.path, 'video')
            if not os.path.exists(self.video_path):
                os.makedirs(self.video_path)

        self.ctrl_queue.put({'act': 'start',
                             'path': self.path,
                             'video_path': self.video_path})
        # self.video_writer = cv2.VideoWriter(os.path.join(self.video_path, '0' + '.avi'),
        #                                     self.fourcc, 20.0, (1280, 720), True)
        # print(self.video_path)
        self.recording = True
        self.start_time = time.time()
        print('start recording.', self.recording)
        # self.start()

    def stop_rec(self):
        self.ctrl_queue.put({'act': 'stop'})
        self.recording = False

        self.start_time = None
        self.frame_reset = True
        print('stop recording.', self.recording, self.frame_cnt)

    def save_param(self):
        json.dump(install, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)

    def check_file(self):
        if not self.recording:
            return {'status': 'ok', 'info': 'oj8k'}

        if not os.path.exists(os.path.join(self.path, 'log.txt')):
            return {'status': 'fail', 'info': 'creating log.txt failed!'}

        videofiles = os.listdir(self.video_path)
        if len(videofiles) <= 0:
            return {'status': 'fail', 'info': 'check the video folder!'}

        return {'status': 'ok'}

    def insert_video(self, msg):
        # print(self.recording, 'video recording----')

        if self.last_image_q.full():
            self.last_image_q.get()
        self.last_image_q.put(msg)

        # if self.video_queue.full():
        #     self.video_queue.get()
        #
        # # print('insert', self.last_image)
        # if local_cfg.save.video:
        #     self.video_queue.put(msg)

    def insert_video_main(self):
        while True:
            while not self.last_image_q.empty():
                if local_cfg.save.video and self.recording:
                    msg = self.last_image_q.get()
                    self.video_queue.put(msg)
            time.sleep(0.1)

    def insert_raw(self, msg):
        # print(self.recording, 'log recording----')
        # print(self.recording)
        timestamp, log_type, data = msg

        # if self.raw_queue.full():
        #     self.raw_queue.get()

        if local_cfg.save.raw and not self.raw_queue.full():
            # print('hahaha222')
            # print(log_type)
            self.raw_queue.put(msg)
        # else:
        #     print('discard raw:', log_type)

    def insert_pcv_raw(self, msg):
        if not self.pcv_queue.full():
            self.pcv_queue.put(msg)

    def insert_can(self, msg):
        if not self.can_raw_queue.full():
            self.can_raw_queue.put(msg)

    def get_last_image(self):
        # print('last', self.last_image)
        if self.last_image_q.empty():
            return None
        return self.last_image_q.get()[-1]

    # def insert_resolved(self, r):
    #     if config.save.raw and self.recording:

    # self.raw_queue.put(msg)
