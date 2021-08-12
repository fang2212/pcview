#!/usr/bin/python
# -*- coding:utf8 -*-
import json
import mmap
import os
import time
from queue import Empty
from datetime import datetime
from multiprocessing import Queue, Process, Array, Manager, Value

from turbojpeg import TurboJPEG

from recorder.convert import ub482_defs, compose_from_def
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
    def __init__(self, redirect=False, uniconf=None, lock=None):
        super(FileHandler, self).__init__()
        self.ctrl_queue = Queue()                   # 控制事件队列
        self.running = True                         # 是否运行

        self.log_mm = mmap.mmap(-1, 1024 * 1024 * 1024*2, access=os.O_RDWR)         # 共享内存匿名文件对象（2G大小）
        self.__tell = Value('L', 0)                                                 # 内存文件位置
        self.log_write_index = 0                                                    # log.txt已写入位置
        self.lock = lock                                                            # mmap操作锁

        self._max_cnt = 1200
        self.__path = Array('c', b'0'*100)          # log.txt文件路径

        self.log_fp = None                          # log.txt文件对象
        self.log_fp_last_write = 0                  # log.txt最后一次记录时间
        self.other_log_fps = {}                     # 其他类型的消息类型log文件对象
        self.video_streams = dict()                 # 视频文件对象
        self.video_path = None                      # 视频保存路径

        self.control_map = {                        # 控制方法映射表
            "start": self._start,
            "close": self._close,
            "stop": self._stop
        }

        # 通过0键来标记起点（结束）
        self.marking = Value('i', 0)
        self.__marking_start_time = Value("d", 0)

        # 定位打点
        self.pinpoint = Manager().dict()

        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')           # 视频编码
        self.recording_state = Value('i', 0)                    # 录制状态
        self.__start_time = Value("d", 0)                       # 开始录制时间
        self.__fid = Value("L", 0)                              # 视频帧数

        self.redirect = redirect

        self.last_image = None
        self.isheadless = False
        self.uniconf = uniconf
        self.d = Manager().dict()
        self.d['installs'] = uniconf.installs

    @property
    def tell(self):
        return self.__tell.value

    @tell.setter
    def tell(self, v):
        self.__tell.value = v

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
    def fid(self):
        return self.__fid.value

    @fid.setter
    def fid(self, v):
        self.__fid.value = v

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

            # 写入到log.txt文件的间隔时间
            if t0 - self.log_fp_last_write > 2 and self.log_fp:
                self.write_to_txt()

            time.sleep(0.1)

    # ****************************** 数据记录方法 ******************************

    def write_to_mmap(self, content):
        """
        写入数据到mmap文件内存对象：加锁，写入
        :return:
        """
        self.lock.acquire()
        self.log_mm.seek(self.tell)
        self.log_mm.write(bytes(content, 'utf-8'))
        self.tell = self.log_mm.tell()
        self.lock.release()

    def write_to_txt(self):
        """
        将内存里面的数据存入到log.txt文件中
        :return:
        """
        print("begin write:", self.log_write_index, self.tell)
        self.lock.acquire()
        end = self.tell
        content = self.log_mm[self.log_write_index:end]
        self.lock.release()

        self.log_write_index = end
        # 写入文件
        if self.log_fp:
            self.log_fp.write(content)
            self.log_fp.flush()
            self.log_fp_last_write = time.time()

    def record_raw_log(self, msg):
        timestamp, log_type, data = msg
        tv_s = int(timestamp)
        tv_us = (timestamp - tv_s) * 1000000
        log_line = "%.10d %.6d " % (tv_s, tv_us) + log_type + ' ' + data + "\n"

        self.write_to_mmap(log_line)

    def record_pcv_log(self, msg):
        source = msg['source']
        buf = json.dumps(msg) + "\n"
        self.write_other_log(source, 'pcv_log.txt', buf, bin=False)

    def record_fusion_log(self, msg):
        source = msg['source']
        buf = msg['buf']
        self.write_other_log(source, 'fusion.txt', buf, bin=True)

    def record_general_bin_log(self, msg):
        source = msg['source']
        name = msg['log_name'] + '.bin'
        self.write_other_log(source, name, msg['buf'], bin=True)

    def record_jpg_log(self, msg):
        if self.path:
            res = msg
            frame_id = res['frame_id']
            data = res['img']
            source = res['source']
            is_main = res.get('is_main')
            if source not in self.video_streams:
                if is_main:
                    video_path = os.path.join(self.path, 'video')
                else:
                    video_path = os.path.join(self.path, source)
                if not os.path.exists(video_path):
                    os.mkdir(video_path)

                self.video_streams[source] = {
                    'video_path': video_path,
                    'frame_cnt': 0,
                    'frame_reset': True,
                    'video_writer': None
                }
                print("new video streams:", self.video_streams[source])

            if self.video_streams[source]['frame_cnt'] % self._max_cnt == 0 or self.video_streams[source]['frame_reset']:
                self.video_streams[source]['frame_reset'] = False
                self.video_streams[source]['frame_cnt'] = 0
                video_path = os.path.join(self.video_streams[source]['video_path'],
                                          'camera_{:08d}.avi'.format(frame_id))
                img = jpeg.decode(np.fromstring(data, np.uint8))
                h, w, c = img.shape
                now_fps = 20
                if self.video_streams[source].get('video_writer'):
                    self.video_streams[source]['video_writer'].finish_video()
                print("fps:", now_fps)
                self.video_streams[source]['video_writer'] = MJPEGWriter(video_path, w, h, now_fps)
                self.video_streams[source]['video_writer'].write_header()
                print("video start over.", self.video_streams[source]['frame_cnt'], video_path)

            self.video_streams[source]['video_writer'].write_frame(data)
            self.video_streams[source]['frame_cnt'] += 1
            self.write_video_log(msg)

    def record_video_log(self, msg):
        if self.path:
            res = msg
            frame_id = res['frame_id']
            data = res['img']
            source = res['source']
            if source not in self.video_streams:
                video_path = os.path.join(self.path, source)
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
            self.write_video_log(msg)

    def write_other_log(self, source, name, msg, bin=False):
        """记录其他类型的消息日志"""
        if not self.path:
            return
        log_dir = os.path.join(self.path, source)
        if not os.path.exists(log_dir):
            print("mkdir:", log_dir)
            os.mkdir(log_dir)
        if source not in self.other_log_fps:
            self.other_log_fps[source] = {}
        if not self.other_log_fps[source].get(name):
            open_mode = 'wb' if bin else 'w+'
            self.other_log_fps[source][name] = open(os.path.join(log_dir, name), open_mode)

        self.other_log_fps[source][name].write(msg)

    def write_video_log(self, msg):
        """记录视频数据日志"""
        ts = msg['ts']
        frame_id = msg['frame_id']
        source = msg['source']
        tv_s = int(ts)
        tv_us = (ts - tv_s) * 1000000
        kw = 'camera' if msg['is_main'] else source
        log_line = "%.10d %.6d " % (tv_s, tv_us) + kw + ' ' + '{}'.format(frame_id) + "\n"
        self.fid = frame_id
        # print(self.video_streams[source]['frame_cnt'])

        # 加锁 写入到内存
        self.write_to_mmap(log_line)

        if msg.get('transport') == 'libflow':
            buf = json.dumps({"frame_id": frame_id, "create_ts": int(ts * 1000000)}) + "\n"
            self.write_other_log(source, 'pcv_log.txt', buf)

    # ****************************** 操作控制方法 ******************************

    def control_event(self):
        """控制事件处理"""
        if not self.ctrl_queue.empty():
            ctrl = self.ctrl_queue.get()
            if ctrl and self.control_map.get(ctrl['act']):
                self.control_map.get(ctrl['act'])(ctrl)

    def _start(self, ctrl):
        print("start:", ctrl)
        self.tell = 0
        self.log_write_index = 0
        self.log_fp = open(os.path.join(self.path, 'log.txt'), 'w+b')
        print("start path:", self.path)

        # 处理间隔录制的mark
        if self.is_marking:
            timestamp = time.time()
            tv_s = int(timestamp)
            tv_us = (timestamp - tv_s) * 1000000
            log_line = "%.10d %.6d " % (tv_s, tv_us) + "mark start\n"
            self.write_to_mmap(log_line)
        # 初始化定位标签，防止自动分割处理的时候无法后续处理 todo：待测试效果
        if self.pinpoint:
            self.insert_raw(
                (time.time(), self.pinpoint.get('source') + '.pinpoint',
                 compose_from_def(ub482_defs, self.pinpoint)))

        self.recording_state.value = 1
        self.start_time = time.time()
        print('start recording.')

    def _close(self, ctrl):
        self.running = False

    def _stop(self, ctrl):
        # 处理间隔录制的mark
        if self.is_marking:
            timestamp = time.time()
            tv_s = int(timestamp)
            tv_us = (timestamp - tv_s) * 1000000
            log_line = "%.10d %.6d " % (tv_s, tv_us) + "mark end"

            self.write_to_mmap(log_line)

        # 关闭文件
        self.write_to_txt()
        self.log_fp.close()
        self.log_fp = None
        self.tell = 0
        self.log_write_index = 0

        for video in self.video_streams:
            self.video_streams[video]['video_writer'].release()
            self.video_streams[video]['frame_reset'] = True
        self.video_streams.clear()

        for source in self.other_log_fps:
            for name in self.other_log_fps[source]:
                self.other_log_fps[source][name].flush()
                self.other_log_fps[source][name].close()
        self.other_log_fps.clear()

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
        print('start recording:', self.path)

    def stop_rec(self):
        self.ctrl_queue.put({'act': 'stop'})
        self.recording_state.value = 0
        self.start_time = 0
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
            self.record_raw_log((time.time(), "mark", "start"))

    def end_mark(self):
        if self.is_recording:
            self.marking.value = 0
            print("end marking")
            self.record_raw_log((time.time(), "mark", "end"))

    def insert_video(self, msg):
        self.last_image = msg
        if self.is_recording:
            print("insert video")
            self.record_video_log(msg)

    def insert_jpg(self, msg):
        if self.is_recording:
            self.record_jpg_log(msg)

    def insert_raw(self, msg):
        if self.uniconf.local_cfg.save.raw and self.is_recording:
            self.record_raw_log(msg)

    def insert_pcv_raw(self, msg):
        if self.is_recording:
            self.record_pcv_log(msg)

    def insert_fusion_raw(self, msg):
        if self.is_recording:
            self.record_fusion_log(msg)

    def insert_general_bin_raw(self, msg):
        if self.is_recording:
            self.record_general_bin_log(msg)

    def get_last_image(self):
        if self.last_image:
            return self.last_image[-1]

