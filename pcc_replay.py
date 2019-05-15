import os
import sched
import struct
from multiprocessing import Process, Queue, freeze_support
from collections import deque
import shutil
import numpy as np
import cv2
from pcc import PCC
import time
from parsers.parser import parsers_dict
from sink.hub import Hub


class JpegExtractor(object):
    def __init__(self, video_file=None):
        self.video_fp = None
        if video_file is not None:
            self.video_fp = open(video_file, 'rb')
        self.output_path = None
        self.buf = b''
        self.buf_len = int(2 * 1024 * 1024)
        self.done = True

    def open(self, file_name):
        self.video_fp = open(file_name, 'rb')
        self.done = False

    def release(self):
        self.video_fp.close()
        self.video_fp = None
        self.done = True

    def read(self):
        if not self.video_fp:
            return
        a = self.buf.find(b'\xff\xd8')
        b = self.buf.find(b'\xff\xd9')
        while a == -1 or b == -1:
            read = self.video_fp.read(self.buf_len)
            if len(read) == 0:
                self.release()
                return
            self.buf += read
            a = self.buf.find(b'\xff\xd8')
            b = self.buf.find(b'\xff\xd9')

        jpg = self.buf[a:b + 2]
        self.buf = self.buf[b+2:]

        return jpg


class LogPlayer(Hub):
    def __init__(self, log_path, configs=None):
        Hub.__init__(self)
        # self.daemon = False
        self.log_path = log_path
        # self.pub_addr = pub_addr
        self.socks = {}
        self.sched = sched.scheduler(time.time, time.sleep)
        self.t0 = 0
        self.last_frame = 0
        self.video_files = os.listdir(os.path.dirname(log_path)+'/video')
        self.jpeg_extractor = JpegExtractor()
        self.base_dir = os.path.dirname(self.log_path)
        self.msg_queue = Queue()
        self.cam_queue = Queue()
        self.cache = {}
        self.msg_cnt = {}
        self.msg_cnt['frame'] = 0
        self.parser = {}
        self.can_types = {"can0": configs[0].can_types.can0,
                          "can1": configs[0].can_types.can1,
                          "can2": configs[1].can_types.can0,
                          "can3": configs[1].can_types.can1}
        for can in self.can_types:
            # print(can)
            self.parser[can] = []
            for type in parsers_dict:
                if type in self.can_types[can]:
                    self.parser[can].append(parsers_dict[type])
            if len(self.parser[can]) == 0:
                self.parser[can] = [parsers_dict["default"]]

        # for msg_type in [x for x in self.can_types]:
        #     self.cache[msg_type] = []
        #     self.msg_cnt[msg_type] = {
        #         'rev': 0,
        #         'show': 0,
        #         'fix': 0,
        #     }
        self.cache['can'] = []

    # def init_socket(self):
    #     self.socks['camera'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
    #     nanomsg.wrapper.nn_bind(self.socks['camera'], "tcp://%s:1200" % self.pub_addr)
    #     self.socks['CAN0'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
    #     nanomsg.wrapper.nn_bind(self.socks['CAN0'], "tcp://%s:1207" % self.pub_addr)
    #     self.socks['CAN1'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
    #     nanomsg.wrapper.nn_bind(self.socks['CAN1'], "tcp://%s:1208" % self.pub_addr)
    #     self.socks['Gsensor'] = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.PUB)
    #     nanomsg.wrapper.nn_bind(self.socks['Gsensor'], "tcp://%s:1209" % self.pub_addr)

    def pop_simple(self):
        res = {
            'frame_id': None,
            'img': None,
            'vehicle': {},
            'lane': {},
            'ped': {},
            'tsr': {},
            'can': {},
            # 'can0': {},
            # 'can1': {},
            # 'can2': {},
            # 'can3': {},
            'extra': {}
        }
        if not self.cam_queue.empty():
            frame_id, data, msg_type = self.cam_queue.get()
            res['img'] = cv2.imdecode(np.fromstring(data['img'], np.uint8), cv2.IMREAD_COLOR)
            res['frame_id'] = frame_id
            if res['img'] is not None:
                for key in list(self.cache):
                    res[key] = self.cache[key]
                    self.cache[key] = []
                self.msg_cnt['frame'] += 1
                return res
            else:
                print('error decode img', frame_id, len(data))
        if not self.msg_queue.empty():
            frame_id, msg_data, msg_type = self.msg_queue.get()
            # res[msg_type] = msg_data
            # res['frame_id'] = frame_id
            if isinstance(msg_data, list):
                # print('msg data list')
                self.cache[msg_type].extend(msg_data)
            elif isinstance(msg_data, dict):
                self.cache[msg_type].append(msg_data)
            # self.msg_cnt[msg_type]['rev'] += 1
            # self.msg_cnt[msg_type]['show'] += 1

    def run(self):
        # self.init_socket()
        lcnt = 0
        rf = open(self.log_path)
        line0 = rf.readline().split(' ')
        self.t0 = int(line0[0]) + int(line0[1]) / 1000000
        self.t0 = time.time() - self.t0
        # with open(self.log_path) as rf:
        for line in rf:
            lcnt += 1
            # print('line {}'.format(cnt))
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if cols[2] == 'camera':
                frame_id = int(cols[3])
                if self.jpeg_extractor.done:
                    if len(self.video_files) == 0:
                        print("End of video file(s).")
                        break
                    else:
                        video_dir = os.path.join(self.base_dir, 'video')
                        self.jpeg_extractor.open(os.path.join(video_dir, self.video_files[0]))
                # jpg = open(os.path.join(self.base_dir, 'video/jpeg_split/camera_%08d.jpg' % idx), 'rb').read()
                jpg = self.jpeg_extractor.read()
                dt = self.t0 + ts - time.time()
                # print(len(jpg))
                if jpg is None:
                    continue

                # if dt > 0.05+0.01:
                #     dt = 0.05
                # nanomsg.wrapper.nn_send(self.sock_img, b'0' * 16 + jpg, 0)
                r = {'ts': ts, 'img': jpg}

                # msg = b'0' * 4 + frame_id.to_bytes(4, 'little', signed=False) + struct.pack('<d', ts) + jpg
                if dt > 0.1:
                    print('----dt {}----'.format(dt))

                if dt <= 0.001:
                    # nanomsg.wrapper.nn_send(self.socks['camera'], msg, 0)
                    self.cam_queue.put((frame_id, r, 'camera'))
                elif dt > 0.2 * (frame_id - self.last_frame):
                    self.t0 += dt
                    # nanomsg.wrapper.nn_send(self.socks['camera'], msg, 0)
                    self.cam_queue.put((frame_id, r, 'camera'))
                else:
                    # self.sched.enter(dt, 1, nanomsg.wrapper.nn_send,
                    #                  argument=(self.socks['camera'], msg, 0))
                    self.sched.enter(dt, 1, self.cam_queue.put, argument=((frame_id, r, 'camera'),))
                self.last_frame = frame_id

                print('sent img {} size {} dt {}'.format(cols[3].strip(), len(jpg), dt))
                # time.sleep(0.01)

            if cols[2] == 'CAN0' or cols[2] == 'CAN1' or cols[2] == 'CAN2' or cols[2] == 'CAN3':
                msg_type = cols[2].lower()
                can_id = int(cols[3], 16).to_bytes(4, 'little')
                data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                msg = b'0000' + can_id + struct.pack('<d', ts) + data

                # print(cols[2], '0x{:03x}'.format(int(cols[3], 16)), ts)
                for parser in self.parser[msg_type]:
                    # print("0x%x" % can_id, parser)
                    r = parser(int(cols[3], 16), data)
                    if r is not None:
                        break
                if r is None:
                    continue
                if isinstance(r, list):
                    # print('r is list')
                    for obs in r:
                        obs['ts'] = ts
                        obs['source'] = ' '.join(self.can_types[msg_type])
                else:
                    # print('r is not list')
                    r['ts'] = ts
                    r['source'] = ' '.join(self.can_types[msg_type])

                # print(r['source'])
                # print(r)
                # self.msg_queue.put((can_id, r, msg_type))
                # nanomsg.wrapper.nn_send(self.sock_can0, msg, 0)r
                dt = self.t0 + ts - time.time()
                # if dt <= 0.001:
                # nanomsg.wrapper.nn_send(self.socks[cols[2]], msg, 0)
                # else:
                # self.msg_queue.put()
                # self.sched.enter(dt, 1, nanomsg.wrapper.nn_send, argument=(self.socks[cols[2]], msg, 0))
                self.sched.enter(dt, 1, self.msg_queue.put, argument=((can_id, r, 'can'),))

            if cols[2] == 'Gsensor':
                data = [int(x) for x in cols[3:9]]
                msg = struct.pack('<BBhIdhhhhhhhq', 0, 0, 0, 0, ts, data[3], data[4], data[5], data[0], data[1], data[2],
                                  int((float(cols[9]) - 36.53) * 340), 0)
                dt = self.t0 + ts - time.time()
                # self.sched.enter(dt, 1, nanomsg.wrapper.nn_send, argument=(self.socks[cols[2]], msg, 0))
                # nanomsg.wrapper.nn_send(self.socks[cols[2]], msg, 0)

            self.sched.run()

        rf.close()


def time_sort(file_name, sort_itv=8000):
    """
    sort the log lines according to timestamp.
    :param file_name: path of the log file
    :param sort_itv:
    :return: sorted file path

    """
    # rev_lines = []
    past_lines = deque(maxlen=2 * sort_itv)
    wf = open('log_sort.txt', 'w')
    idx = 0
    with open(file_name) as rf:
        for idx, line in enumerate(rf):
            cols = line.split(' ')
            tv_s = int(cols[0])
            tv_us = int(cols[1])
            ts = tv_s * 1000000 + tv_us
            past_lines.append([ts, line])
            # print(len(past_lines))
            if len(past_lines) < 2 * sort_itv:
                continue
            if (idx + 1) % sort_itv == 0:
                # print(len(past_lines))
                past_lines = sorted(past_lines, key=lambda x: x[0])
                wf.writelines([x[1] for x in past_lines[:sort_itv]])
                past_lines = deque(past_lines, maxlen=2 * sort_itv)
            # if len(past_lines) > 300:  # max lines to search forward.
            #     wf.write(past_lines.popleft()[1])
    past_lines = sorted(past_lines, key=lambda x: x[0])
    wf.writelines([x[1] for x in past_lines[sort_itv - ((idx + 1) % sort_itv):]])

    wf.close()
    return os.path.abspath('log_sort.txt')


if __name__ == "__main__":
    from config.config import *

    freeze_support()
    source = '/home/cao/文档/data_temp/20190319_fusion_q3_new_version/20190319173018/log.txt'
    r_sort = os.path.join(os.path.dirname(source), 'log_sort.txt')
    if not os.path.exists(r_sort):
        sort_src = time_sort(source)
        shutil.copy2(sort_src, os.path.dirname(source))
        os.remove(sort_src)

    config_path = os.path.join(os.path.dirname(source), 'config.json')
    install_path = os.path.join(os.path.dirname(source), 'installation.json')

    if os.path.exists(config_path):
        print("using configs:", config_path)
        load_config(config_path)
    if os.path.exists(install_path):
        print("using installation:", install_path)
        load_installation(install_path)

    print(install['video'])
    player = LogPlayer(r_sort, configs)
    # player.start()
    pc_viewer = PCC(player)
    pc_viewer.start()

