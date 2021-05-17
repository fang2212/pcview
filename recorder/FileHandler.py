#!/usr/bin/python
# -*- coding:utf8 -*-
import json
import os
import time
from queue import Empty
from datetime import datetime
from multiprocessing import Queue, Process, Array, Manager, Value

from turbojpeg import TurboJPEG

from tools.video_writer import MJPEGWriter
import cv2
import numpy as np

# 限制为单线程，防止竞争占用资源
cv2.setNumThreads(0)
jpeg = TurboJPEG()


class FileHandler(Process):
    """
    日志记录进程，对视频进行录像、记录各种传感器的数据
    """
    def __init__(self, redirect=False, uniconf=None):
        super(FileHandler, self).__init__()
        self.ctrl_queue = Queue()                   # 控制事件队列
        self.log_queue = Queue(maxsize=200000)      # 记录数据队列
        self.running = True                         # 是否运行

        self._max_cnt = 1200
        self.__path = Array('c', b'0'*100)

        self.save_path = None                       # 日志保存路径
        self.log_fp = None                          # log.txt文件对象
        self.log_fp_last_write = 0                  # log.txt最后一次记录时间
        self.other_log_fps = {}                     # 其他类型的消息类型log文件对象
        self.video_streams = dict()                 # 视频文件对象
        self.video_path = None                      # 视频保存路径

        # 通过0键来标记起点（结束）
        self.marking = Value('i', 0)
        self.__marking_start_time = Value("d", 0)

        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.recording_state = Value('i', 0)
        self.__start_time = Value("d", 0)

        self.redirect = redirect

        self.last_image = None
        self.isheadless = False
        self.uniconf = uniconf
        self.d = Manager().dict()
        self.d['installs'] = uniconf.installs

    @property
    def is_marking(self):
        """是否正在标记"""
        return self.marking.value == 1

    @property
    def start_marking_time(self):
        return self.__marking_start_time.value

    @start_marking_time.setter
    def start_marking_time(self, v):
        self.__marking_start_time.value = v

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
            return self.__path.value.decode()

    @path.setter
    def path(self, p):
        with self.__path.get_lock():
            self.__path.value = p.encode()

    def run(self):
        print(f"file handle pid:{os.getpid()}")

        while self.running:
            t0 = time.time()
            self.control_event()

            if self.is_recording and t0 - self.start_time > 600:
                self.stop_rec(clean_queue=False)
                self.start_rec()

            try:
                log_class, msg = self.log_queue.get(block=True, timeout=0.001)
            except Empty:
                time.sleep(0.001)
                continue

            # log.txt记录
            if log_class == 'raw' and self.log_fp:
                timestamp, log_type, data = msg
                tv_s = int(timestamp)
                tv_us = (timestamp - tv_s) * 1000000
                log_line = "%.10d %.6d " % (tv_s, tv_us) + log_type + ' ' + data + "\n"
                self.log_fp.write(log_line)

            # 其他类型的日志记录
            elif log_class == 'pcv':
                source = msg['source']
                buf = json.dumps(msg) + "\n"
                self.record_other_log(source, 'pcv_log.txt', buf, bin=False)
            elif log_class == 'fusion':
                source = msg['source']
                buf = msg['buf']
                self.record_other_log(source, 'fusion.txt', buf, bin=True)
            elif log_class == 'general_bin':
                source = msg['source']
                name = msg['log_name'] + '.bin'
                self.record_other_log(source, name, msg['buf'], bin=True)
            elif log_class == 'jpg' and self.save_path:
                res = msg
                frame_id = res['frame_id']
                data = res['img']
                source = res['source']
                is_main = res.get('is_main')
                if source not in self.video_streams:
                    if is_main:
                        video_path = os.path.join(self.save_path, 'video')
                    else:
                        video_path = os.path.join(self.save_path, source)
                    if not os.path.exists(video_path):
                        os.mkdir(video_path)

                    self.video_streams[source] = {
                        'video_path': video_path,
                        'frame_cnt': 0,
                        'frame_reset': True,
                        'video_writer': None
                    }

                if self.video_streams[source]['frame_cnt'] % self._max_cnt == 0 or self.video_streams[source]['frame_reset']:
                    self.video_streams[source]['frame_reset'] = False
                    self.video_streams[source]['frame_cnt'] = 0
                    video_path = os.path.join(self.video_streams[source]['video_path'],
                                              'camera_{:08d}.avi'.format(frame_id))
                    img = jpeg.decode(np.fromstring(data, np.uint8))
                    h, w, c = img.shape
                    now_fps = 20
                    if 'cv22' in source:
                        now_fps = 30
                    if self.video_streams[source].get('video_writer'):
                        self.video_streams[source]['video_writer'].finish_video()
                    self.video_streams[source]['video_writer'] = MJPEGWriter(video_path, w, h, now_fps)
                    self.video_streams[source]['video_writer'].write_header()
                    print("video start over.", self.video_streams[source]['frame_cnt'], video_path)

                self.video_streams[source]['video_writer'].write_frame(data)
                self.video_streams[source]['frame_cnt'] += 1
                self.record_video_log(msg)
            elif log_class == 'video' and self.save_path:
                res = msg
                frame_id = res['frame_id']
                data = res['img']
                source = res['source']
                if source not in self.video_streams:
                    video_path = os.path.join(self.save_path, source)
                    if not os.path.exists(video_path):
                        os.mkdir(video_path)
                    self.video_streams[source] = {
                        'video_path': video_path,
                        'frame_cnt': 0,
                        'frame_reset': True,
                        'video_writer': None
                    }

                h, w, c = data.shape
                if self.video_streams[source]['frame_cnt'] % self._max_cnt == 0 or self.video_streams[source]['frame_reset']:
                    self.video_streams[source]['frame_reset'] = False
                    self.video_streams[source]['frame_cnt'] = 0
                    vpath = os.path.join(self.video_streams[source]['video_path'], 'camera_{:08d}.avi'.format(frame_id))
                    print("video start over.", self.video_streams[source]['frame_cnt'], vpath)
                    if self.video_streams[source]['video_writer']:
                        if not self.isheadless:
                            self.video_streams[source]['video_writer'].release()
                        else:
                            self.video_streams[source]['video_writer'].flush()
                            self.video_streams[source]['video_writer'].close()

                    if not self.isheadless:
                        self.video_streams[source]['video_writer'] = cv2.VideoWriter(vpath, self.fourcc, 20.0, (w, h), True)
                    else:
                        self.video_streams[source]['video_writer'] = open(vpath, 'wb')

                self.video_streams[source]['video_writer'].write(data)
                self.video_streams[source]['frame_cnt'] += 1
                self.record_video_log(msg)

            # 写入到log.txt文件的间隔时间
            if t0 - self.log_fp_last_write > 1 and self.log_fp:
                self.log_fp.flush()
                self.log_fp_last_write = time.time()

    def record_other_log(self, source, name, msg, bin=False):
        """记录其他类型的消息日志"""
        if not self.save_path:
            return
        log_dir = os.path.join(self.save_path, source)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        if source not in self.other_log_fps:
            self.other_log_fps[source] = {}
        if not self.other_log_fps[source].get(name):
            open_mode = 'wb' if bin else 'w+'
            self.other_log_fps[source][name] = open(os.path.join(log_dir, name), open_mode)

        self.other_log_fps[source][name].write(msg)

    def record_video_log(self, msg):
        """记录视频数据日志"""
        ts = msg['ts']
        frame_id = msg['frame_id']
        source = msg['source']
        tv_s = int(ts)
        tv_us = (ts - tv_s) * 1000000
        kw = 'camera' if msg['is_main'] else source
        log_line = "%.10d %.6d " % (tv_s, tv_us) + kw + ' ' + '{}'.format(frame_id) + "\n"
        if self.log_fp:
            self.log_fp.write(log_line)

        if msg.get('transport') == 'libflow':
            buf = json.dumps({"frame_id": frame_id, "create_ts": int(ts * 1000000)}) + "\n"
            self.record_other_log(source, 'pcv_log.txt', buf)

    def control_event(self):
        """控制事件处理"""
        if not self.ctrl_queue.empty():
            ctrl = self.ctrl_queue.get()
            if ctrl['act'] == 'start':
                self.save_path = ctrl['path']
                self.log_fp = open(os.path.join(self.save_path, 'log.txt'), 'w+')

                # 处理间隔录制的mark
                if self.is_marking:
                    timestamp = time.time()
                    tv_s = int(timestamp)
                    tv_us = (timestamp - tv_s) * 1000000
                    log_line = "%.10d %.6d " % (tv_s, tv_us) + "mark start"
                    self.log_fp.write(log_line)
                print('start recording.')

            elif ctrl['act'] == 'stop':
                # 处理间隔录制的mark
                if self.is_marking:
                    timestamp = time.time()
                    tv_s = int(timestamp)
                    tv_us = (timestamp - tv_s) * 1000000
                    log_line = "%.10d %.6d " % (tv_s, tv_us) + "mark end"
                    self.log_fp.write(log_line)

                # 关闭文件
                self.log_fp.flush()
                self.log_fp.close()
                self.log_fp = None
                self.save_path = None

                for video in self.video_streams:
                    self.video_streams[video]['video_writer'].release()
                    self.video_streams[video]['frame_reset'] = True
                self.video_streams.clear()

                for source in self.other_log_fps:
                    for name in self.other_log_fps[source]:
                        self.other_log_fps[source][name].flush()
                        self.other_log_fps[source][name].close()
                self.other_log_fps.clear()
            elif ctrl['act'] == 'clean':
                for i in range(self.log_queue.qsize()):
                    self.log_queue.get()
            elif ctrl['act'] == 'close':
                self.running = False

    def close(self):
        self.ctrl_queue.put({'act': 'close'})

    def start_rec(self, rlog=None):
        # 初始化日志保存路径
        date_format = '%Y%m%d%H%M%S'
        date = datetime.now().strftime(date_format)
        if rlog:
            self.path = os.path.join(os.path.dirname(rlog), 'clip_' + date)
        else:
            self.path = os.path.join(self.uniconf.local_cfg.log_root, date)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # 保存配置
        self.uniconf.installs = self.d['installs']
        if not rlog:
            json.dump(self.uniconf.configs, open(os.path.join(self.path, 'config.json'), 'w+'), indent=True)
            json.dump(self.uniconf.installs, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)

        # 初始化视频保存路径
        if self.uniconf.local_cfg.save.video:
            self.video_path = os.path.join(self.path, 'video')
            if not os.path.exists(self.video_path):
                os.makedirs(self.video_path)

        self.ctrl_queue.put({'act': 'start', 'path': self.path, 'video_path': self.video_path})
        self.recording_state.value = 1
        self.start_time = time.time()
        print('start recording:', self.path)

    def stop_rec(self, clean_queue=True):
        self.ctrl_queue.put({'act': 'stop'})
        self.recording_state.value = 0
        self.start_time = 0

        # 是否清除剩余未处理的日志信号
        if clean_queue:
            self.ctrl_queue.put({'act': 'clean'})
        print('stop recording.', self.is_recording)

    def save_param(self):
        self.uniconf.installs = self.d['installs']
        json.dump(self.uniconf.installs, open(os.path.join(self.path, 'installation.json'), 'w+'), indent=True)

    def check_file(self):
        if not self.is_recording:
            return {'status': 'ok', 'info': 'not recording'}

        if not os.path.exists(os.path.join(self.path, 'log.txt')):
            return {'status': 'fail', 'info': 'creating log.txt failed!'}

        video_files = os.listdir(self.video_path)
        if len(video_files) <= 0:
            return {'status': 'fail', 'info': 'check the video folder!'}

        return {'status': 'ok'}

    def start_mark(self):
        if self.is_recording:
            self.marking.value = 1
            self.start_marking_time = time.time()
            print("start marking")
            self.log_queue.put(("raw", (time.time(), "mark", "start")))

    def end_mark(self):
        if self.is_recording:
            self.marking.value = 0
            print("end marking")
            self.log_queue.put(("raw", (time.time(), "mark", "end")))

    def insert_video(self, msg):
        self.last_image = msg
        if not self.log_queue.full() and self.is_recording:
            self.log_queue.put(('video', msg))

    def insert_jpg(self, msg):
        if self.is_recording:
            self.log_queue.put(('jpg', msg))

    def insert_raw(self, msg):
        if self.uniconf.local_cfg.save.raw and self.is_recording:
            self.log_queue.put(('raw', msg))

    def insert_pcv_raw(self, msg):
        if self.is_recording:
            self.log_queue.put(('pcv', msg))

    def insert_fusion_raw(self, msg):
        if not self.log_queue.full() and self.is_recording:
            self.log_queue.put(('fusion', msg))

    def insert_general_bin_raw(self, msg):
        if self.is_recording:
            self.log_queue.put(('general_bin', msg))

    def get_last_image(self):
        if self.last_image:
            return self.last_image[-1]

