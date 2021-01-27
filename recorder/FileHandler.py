#!/usr/bin/python
# -*- coding:utf8 -*-
import json
import os
import sys
import time
from datetime import datetime
from multiprocessing import Queue, Value, Process, Array
from multiprocessing.dummy import Process as Thread
from collections import deque
from tools.video_writer import MJPEGWriter
import cv2
import numpy as np
from ctypes import c_char_p
# from config.config import local_cfg, configs, install


class FileHandler(Process):
    def __init__(self, redirect=False, uniconf=None):
        super(FileHandler, self).__init__()
        self.deamon = True
        # self.setName('file_handler_thread')
        # self.log_queue = Queue()
        self.ctrl_queue = Queue()
        # self.image_queue = Queue()
        # self.video_queue = Queue(maxsize=40)
        # self.jpg_queue = Queue(maxsize=50)
        # self.raw_queue = Queue(maxsize=90000)
        # self.pcv_queue = Queue(maxsize=5000)
        # self.fusion_queue = Queue(maxsize=5000)

        self.log_q = Queue(maxsize=200000)

        # self.can_raw_queue = kqueue(maxsize=100)
        self._max_cnt = 1200
        # self.__path = Value(c_char_p, b"")
        self.__path = Array('c', b'0'*100)
        self.image_path = None
        self.raw_fp = None
        self.log_fp = None
        self.alert_fp = None
        self.video_writer = None
        self.video_path = None
        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.recording_state = Value('i', 0)
        self.__start_time = Value("d", 0)

        self.frame_cnt = 0
        self.frame_reset = True
        self.redirect = redirect

        self.last_image = None

        self.isheadless = False
        self.uniconf = uniconf

        # print('outer id:', os.getpid())

    @property
    def is_recording(self):
        return self.recording_state.value == 1

    @property
    def start_time(self):
        return self.__start_time.value

    @start_time.setter
    def start_time(self, v):
        self.__start_time.value = v

    @property
    def path(self):
        with self.__path.get_lock():
            # print(self.__path.value)
            return self.__path.value.decode()

    @path.setter
    def path(self, p):
        with self.__path.get_lock():
            # print(p)
            self.__path.value = p.encode()

    def run(self):
        # cnt = 0
        raw_fp = None
        # pcv_fp = None
        # fusion_fp = None
        other_log_fps = {}

        video_streams = dict()
        path = None
        exit = False

        # video_path = None
        # frame_cnt = 0
        # frame_reset = True
        # video_writer = None
        # can_queue = deque(maxlen=2000)
        # print('inner id:', os.getpid())
        state = 'stop'
        # origin_stdout = sys.stdout
        # key_msg_cache = deque(maxlen=50)

        def write_log(source, name, msg, bin=False):
            if not path:
                return
            dir = os.path.join(path, source)
            if not os.path.exists(dir):
                os.mkdir(dir)
            if source not in other_log_fps:
                other_log_fps[source] = {}
            if not other_log_fps[source].get(name):
                ftype = 'wb' if bin else 'w+'
                other_log_fps[source][name] = open(os.path.join(dir, name), ftype)

            other_log_fps[source][name].write(msg)

        while not exit:
            raw_write = 0
            pcv_write = False
            fusion_write = False
            video_write = False
            t0 = time.time()
            # print('now time', t0)
            if self.is_recording and t0 - self.start_time > 600:
                self.stop_rec()
                self.start_rec()
                self.start_time = t0

            if not self.ctrl_queue.empty():
                ctrl = self.ctrl_queue.get()
                if ctrl['act'] == 'start':

                    path = ctrl['path']

                    video_path = ctrl['video_path']

                    raw_fp = open(os.path.join(path, 'log.txt'), 'w+')

                    # stdout_fp = open(os.path.join(path, 'stdout.txt'), 'w+')
                    # sys.stdout = stdout_fp
                    state = 'start'

                    # while not self.raw_queue.empty():
                    #     self.raw_queue.get()
                    #
                    # while not self.video_queue.empty():
                    #     self.video_queue.get()
                    #
                    # while not self.pcv_queue.empty():
                    #     self.pcv_queue.get()
                    #
                    # while not self.fusion_queue.empty():
                    #     self.fusion_queue.get()
                    print('rec now start.')

                elif ctrl['act'] == 'stop':
                    raw_fp.flush()
                    raw_fp.close()
                    path = None
                    raw_fp = None
                    for video in video_streams:
                        video_streams[video]['video_writer'].release()
                        video_streams[video]['frame_reset'] = True
                    video_streams.clear()

                    for source in other_log_fps:
                        for name in other_log_fps[source]:
                            other_log_fps[source][name].flush()
                            other_log_fps[source][name].close()
                    other_log_fps.clear()

                    # video_writer.flush()
                    # video_writer.close()

                    # pcv_fp.flush()
                    # pcv_fp.close()
                    # pcv_fp = None
                    #
                    # fusion_fp.flush()
                    # fusion_fp.close()
                    # fusion_fp = None
                    #

                    # sys.stdout = origin_stdout
                    state = 'stop'

                    for i in range(self.log_q.qsize()):
                        self.log_q.get()
                elif ctrl['act'] == 'close':
                    exit = True


            t1 = time.time()

            # print(self.video_path)
            # print('---fileHandle process id----', os.getpid())
            # print(config.save.raw, raw_fp)
            while not self.log_q.empty():
                log_class, msg = self.log_q.get()
            # if self.uniconf.local_cfg.save.raw and raw_fp:
                if log_class == 'raw' and raw_fp:
                    timestamp, log_type, data = msg
                    tv_s = int(timestamp)
                    tv_us = (timestamp - tv_s) * 1000000
                    log_line = "%.10d %.6d " % (tv_s, tv_us) + log_type + ' ' + data + "\n"
                    # print(log_line, end='')
                    # print(log_line)
                    raw_fp.write(log_line)
                    raw_write += 1
                    # raw_fp.flush()
                    # print('end ............')

                elif log_class == 'pcv':
                    source = msg['source']
                    # dir = os.path.join(path, source)
                    # if not other_log_fps.get(source):
                    #     other_log_fps[source] = {}
                    # if not os.path.exists(dir):
                    #     os.mkdir(dir)
                    # if not other_log_fps[source].get(log_class):
                    #     other_log_fps[source][log_class] = open(os.path.join(dir, 'pcv_log.txt'), 'w+')
                    # data = self.pcv_queue.get()
                    buf = json.dumps(msg) + "\n"
                    # other_log_fps[source].write(buf + "\n")
                    write_log(source, 'pcv_log.txt', buf, bin=False)
                    # pcv_fp.flush()
                    # pcv_write = True
                elif log_class == 'fusion':
                    source = msg['source']
                    # dir = os.path.join(path, source)
                    # if not other_log_fps.get(source):
                    #     other_log_fps[source] = {}
                    # if not os.path.exists(dir):
                    #     os.mkdir(dir)
                    # if not other_log_fps[source].get(log_class):
                    #     other_log_fps[source][log_class] = open(os.path.join(dir, 'fusion.txt'), 'wb')
                    # data = self.fusion_queue.get()
                    buf = msg['buf']
                    # other_log_fps[source].write(buf)
                    write_log(source, 'fusion.txt', buf, bin=True)
                    # fusion_write = True
                    # fusion_fp.flush()
                    # t2 = time.time()
            # print('filehandler...', video_path, self.video_queue.qsize())
            # while self.uniconf.local_cfg.save.video and not self.jpg_queue.empty() and path:
                elif log_class == 'general_bin':
                    source = msg['source']
                    name = msg['log_name'] + '.bin'
                    # dir = os.path.join(path, source)
                    # if not other_log_fps.get(source):
                    #     other_log_fps[source] = {}
                    # if not os.path.exists(dir):
                    #     os.mkdir(dir)
                    # if not other_log_fps[source].get(name):
                    #     other_log_fps[source] = open(os.path.join(dir, '{}.bin'.format(name)), 'wb')
                    write_log(source, name, msg['buf'], bin=True)
                elif log_class == 'jpg' and path:
                    res = msg
                    ts = res['ts']
                    frame_id = res['frame_id']
                    data = res['img']
                    source = res['source']
                    is_main = res.get('is_main')
                    if source not in video_streams:
                        if is_main:
                            vpath = os.path.join(path, 'video')
                        else:
                            vpath = os.path.join(path, source)
                        if not os.path.exists(vpath):
                            os.mkdir(vpath)
                        video_streams[source] = {'video_path': vpath, 'frame_cnt': 0, 'frame_reset': True,
                                                 'video_writer': None}

                    if video_streams[source]['frame_cnt'] % self._max_cnt == 0 or video_streams[source]['frame_reset']:
                        video_streams[source]['frame_reset'] = False
                        video_streams[source]['frame_cnt'] = 0
                        vpath = os.path.join(video_streams[source]['video_path'], 'camera_{:08d}.avi'.format(frame_id))
                        print("video start over.", video_streams[source]['frame_cnt'], vpath)
                        img = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
                        h, w, c = img.shape
                        if video_streams[source]['video_writer']:
                            # video_streams[source]['video_writer'].flush()
                            video_streams[source]['video_writer'].finish_video()
                        video_streams[source]['video_writer'] = MJPEGWriter(vpath, w, h, 30)
                        video_streams[source]['video_writer'].write_header()
                    video_streams[source]['video_writer'].write_frame(data)
                    tv_s = int(ts)
                    tv_us = (ts - tv_s) * 1000000
                    kw = 'camera' if is_main else source
                    log_line = "%.10d %.6d " % (tv_s, tv_us) + kw + ' ' + '{}'.format(frame_id) + "\n"
                    if raw_fp:
                        raw_fp.write(log_line)
                        raw_write += 1

                    # if other_log_fps.get(source) and other_log_fps[source].get('pcv'):
                    #     other_log_fps[source]['pcv'].write(json.dumps({"frame_id": frame_id, "create_ts": int(ts * 1000000)}) + "\n")
                    if res.get('transport') == 'libflow':
                        buf = json.dumps({"frame_id": frame_id, "create_ts": int(ts * 1000000)}) + "\n"
                        write_log(source, 'pcv_log.txt', buf)

                    video_streams[source]['frame_cnt'] += 1

            # while self.uniconf.local_cfg.save.video and not self.video_queue.empty() and path:
                elif log_class == 'video' and path:
                    res = msg
                    ts = res['ts']
                    frame_id = res['frame_id']
                    data = res['img']
                    source = res['source']
                    if source not in video_streams:
                        vpath = os.path.join(path, source)
                        if not os.path.exists(vpath):
                            os.mkdir(vpath)
                        video_streams[source] = {'video_path': vpath, 'frame_cnt': 0, 'frame_reset': True,
                                                 'video_writer': None}

                    h, w, c = data.shape
                    # print(self.frame_cnt)
                    if video_streams[source]['frame_cnt'] % self._max_cnt == 0 or video_streams[source]['frame_reset']:
                        video_streams[source]['frame_reset'] = False
                        video_streams[source]['frame_cnt'] = 0
                        vpath = os.path.join(video_streams[source]['video_path'], 'camera_{:08d}.avi'.format(frame_id))
                        print("video start over.", video_streams[source]['frame_cnt'], vpath)
                        if video_streams[source]['video_writer']:
                            if not self.isheadless:
                                video_streams[source]['video_writer'].release()
                            else:
                                video_streams[source]['video_writer'].flush()
                                video_streams[source]['video_writer'].close()

                        if not self.isheadless:
                            video_streams[source]['video_writer'] = cv2.VideoWriter(vpath, self.fourcc, 20.0, (w, h), True)
                        else:
                            video_streams[source]['video_writer'] = open(vpath, 'wb')

                    video_streams[source]['video_writer'].write(data)
                    # video_write = True
                    tv_s = int(ts)
                    tv_us = (ts - tv_s) * 1000000
                    kw = 'camera' if source == 'video' else source
                    log_line = "%.10d %.6d " % (tv_s, tv_us) + kw + ' ' + '{}'.format(frame_id) + "\n"
                    if raw_fp:
                        raw_fp.write(log_line)
                        raw_write += 1

                    # if other_log_fps.get(source):
                    #     other_log_fps[source].write(json.dumps({"frame_id": frame_id, "create_ts": int(ts * 1000000)}) + "\n")
                    if res.get('transport') == 'libflow':
                        buf = json.dumps({"frame_id": frame_id, "create_ts": int(ts * 1000000)}) + "\n"
                        write_log(source, 'pcv_log.txt', buf)

                    video_streams[source]['frame_cnt'] += 1
            t3 = time.time()
            if t3 - t0 < 0.001:
                time.sleep(0.001)
            # else:
            if raw_write > 2000:
                raw_write = 0
                raw_fp.flush()
            # if pcv_write:
            #     pcv_fp.flush()
            # if fusion_write:
            #     fusion_fp.flush()
            # if video_write:
            #     video_writer.flush()
            # print('filehandler dt:{:.1f} ctrl:{:.1f} raw:{:.1f} video:{:.1f}'.format(1000*(t3-t0), 1000*(t1-t0), 1000*(t2-t1), 1000*(t3-t2)))
            # time.sleep(0.01)

    def close(self):
        self.ctrl_queue.put({'act': 'close'})

    def start_rec(self, rlog=None):
        FORMAT = '%Y%m%d%H%M%S'
        date = datetime.now().strftime(FORMAT)
        if rlog:
            self.path = os.path.join(os.path.dirname(rlog), 'clip_' + date)
        else:
            self.path = os.path.join(self.uniconf.local_cfg.log_root, date)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if not rlog:
            json.dump(self.uniconf.configs, open(os.path.join(self.path, 'config.json'), 'w+'), indent=True)
            # json.dump(install, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)
            # shutil.copy('etc/installation.json', os.path.join(self.path, 'installation.json'))
            json.dump(self.uniconf.installs, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)

        if self.uniconf.local_cfg.save.video:
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
        self.recording_state.value = 1
        self.start_time = time.time()
        print('start recording.', self.is_recording, self.path)
        # self.start()

    def stop_rec(self):
        self.ctrl_queue.put({'act': 'stop'})
        self.recording_state.value = 0

        self.start_time = 0
        self.frame_reset = True
        print('stop recording.', self.is_recording, self.frame_cnt)

    def save_param(self):
        json.dump(self.uniconf.installs, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)

    def check_file(self):
        if not self.is_recording:
            return {'status': 'ok', 'info': 'oj8k'}

        if not os.path.exists(os.path.join(self.path, 'log.txt')):
            return {'status': 'fail', 'info': 'creating log.txt failed!'}

        videofiles = os.listdir(self.video_path)
        if len(videofiles) <= 0:
            return {'status': 'fail', 'info': 'check the video folder!'}

        return {'status': 'ok'}

    def insert_video(self, msg):
        # print(self.is_recording, 'video recording----')

        self.last_image = msg
        # print('data img ', msg)

        # if self.video_queue.full():
        #     self.video_queue.get()
        #
        # # print('insert', self.last_image)
        # if local_cfg.save.video:
        #     self.video_queue.put(msg)
        # print('------------------')
        if not self.log_q.full() and self.is_recording:
            self.log_q.put(('video', msg))

    def insert_jpg(self, msg):
        if not self.log_q.full() and self.is_recording:
            self.log_q.put(('jpg', msg))

    def insert_raw(self, msg):
        # print(self.is_recording, 'log recording----')
        # print(self.is_recording)
        # timestamp, log_type, data = msg

        if self.uniconf.local_cfg.save.raw and self.is_recording and not self.log_q.full():
            self.log_q.put(('raw', msg))
        # else:
        #     print('discard raw:', log_type)

    def insert_pcv_raw(self, msg):
        if not self.log_q.full() and self.is_recording:
            self.log_q.put(('pcv', msg))

    def insert_fusion_raw(self, msg):
        if not self.log_q.full() and self.is_recording:
            self.log_q.put(('fusion', msg))

    def insert_general_bin_raw(self, msg):
        if not self.log_q.full() and self.is_recording:
            self.log_q.put(('general_bin', msg))

    # def insert_can(self, msg):
    #     if not self.can_raw_queue.full():
    #         self.can_raw_queue.put(msg)

    def get_last_image(self):
        # print('last', self.last_image)
        if self.last_image:
            return self.last_image[-1]

    # def insert_resolved(self, r):
    #     if config.save.raw and self.is_recording:

    # self.raw_queue.put(msg)
