#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/11/2
# @Author  : simon.xu
# @File    : replay.py
# @Desc    : log replayer for collected data

import os
import sched
import struct
from multiprocessing import Process, Queue, freeze_support, Value
from collections import deque
import time
import shutil
import cProfile


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


def jpeg_extractor(video_dir):
    """
    This generator extract jpg from each of the video files in the directory.
    :param video_dir:
    :return: frame_id: rolling counter of the frame from FPGA (if valid, synced with video name)
             jpg: raw jpg bytes
    """
    buf = b''
    buf_len = int(2 * 1024 * 1024)
    file_done = False
    video_files = sorted([x for x in os.listdir(video_dir) if x.endswith('.avi')])
    for file in video_files:
        file_done = False
        fid = int(file.split('.')[0].split('_')[1])
        with open(os.path.join(video_dir, file), 'rb') as vf:
            while True:
                a = buf.find(b'\xff\xd8')
                b = buf.find(b'\xff\xd9')
                while a == -1 or b == -1:
                    read = vf.read(buf_len)
                    if len(read) == 0:
                        file_done = True
                        break
                    buf += read
                    a = buf.find(b'\xff\xd8')
                    b = buf.find(b'\xff\xd9')
                if file_done:
                    break
                jpg = buf[a:b + 2]
                buf = buf[b + 2:]
                # fid = int.from_bytes(jpg[24:28], byteorder="little")
                yield fid, jpg
                if fid is not None:
                    fid = None


class LogPlayer(Process):
    def __init__(self, log_path, configs=None, start_frame=0, ratio=1.0):
        Process.__init__(self)
        # self.daemon = False
        self.time_aligned = True
        self.log_path = log_path
        self.start_frame = start_frame
        # self.forwarding = False
        # self.pub_addr = pub_addr
        self.socks = {}
        self.sched = sched.scheduler(time.time, time.sleep)
        self.t0 = 0
        self.last_frame = 0
        # files = os.listdir(os.path.dirname(log_path)+'/video')
        # files = [x for x in files if x.endswith('.avi')]
        # self.video_files = sorted(files)
        # self.jpeg_extractor = JpegExtractor()
        self.jpeg_extractor = jpeg_extractor(os.path.dirname(log_path) + '/video')
        self.base_dir = os.path.dirname(self.log_path)
        self.msg_queue = Queue()
        self.cam_queue = Queue()
        self.cache = {}
        self.msg_cnt = {}
        self.msg_cnt['frame'] = 0
        self.parser = {}
        self.can_types = {}
        self.msg_types = []
        self.context = {}
        self.ratio = ratio
        self.ctrl_q = Queue()
        # self.snapshot = {}
        # self.can_types = {"can0": configs[0]['can_types']['can0'],
        #                   "can1": configs[0]['can_types']['can1'],
        #                   "can2": configs[1]['can_types']['can0'],
        #                   "can3": configs[1]['can_types']['can1']}
        # print(self.can_types)
        for idx, cfg in enumerate(configs):
            cantypes0 = ' '.join(cfg['can_types']['can0']) + '.{:01}'.format(idx)
            cantypes1 = ' '.join(cfg['can_types']['can1']) + '.{:01}'.format(idx)
            self.can_types['CAN' + '{:01d}'.format(idx * 2)] = cantypes0
            self.can_types['CAN' + '{:01d}'.format(idx * 2 + 1)] = cantypes1
            if len(cfg['can_types']['can0']) > 0:
                self.msg_types.append([cantypes0])
            if len(cfg['can_types']['can1']) > 0:
                self.msg_types.append([cantypes1])
        print('msgtypes:', self.msg_types)

        self.msg_types = [x if len(x) > 0 else '' for x in list(self.can_types.values()) if len(x) > 2]

        for can in self.can_types:
            # print(can)
            self.parser[can] = []
            self.context[can] = {}
            for type in parsers_dict:
                if type in self.can_types[can]:
                    print(can, type)
                    self.parser[can].append(parsers_dict[type])
            if len(self.parser[can]) == 0:
                self.parser[can] = [parsers_dict['default']]
        # print(self.parser)

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

    def pop_simple(self, pause=False):
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
            # print(frame_id, msg_type)
            res['ts'] = data['ts']
            res['img'] = data['img']
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
        else:
            time.sleep(0.001)

    def pause(self, pause):
        if pause:
            self.ctrl_q.put({'action': 'pause'})
        else:
            self.ctrl_q.put({'action': 'resume'})

    def run(self):
        # self.init_socket()
        # cp = cProfile.Profile()
        # cp.enable()
        rtk_dec = False
        lcnt = 0
        rf = open(self.log_path)
        line0 = rf.readline().split(' ')
        self.t0 = int(line0[0]) + int(line0[1]) / 1000000
        self.t0 = time.time() - self.t0
        # with open(self.log_path) as rf:
        forwarding = False
        stop_frame = 84000
        frame_id = 0

        for line in rf:
            if not self.ctrl_q.empty():
                ctrl = self.ctrl_q.get()
                if ctrl.get('action') == 'pause':
                    print('replay paused.')
                    t_pause = time.time()
                    while True:
                        ctrl = self.ctrl_q.get()
                        if ctrl and ctrl.get('action') != 'pause':
                            self.t0 += time.time() - t_pause
                            break
                        else:
                            time.sleep(0.05)
            lcnt += 1
            # print('line {}'.format(cnt))
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if cols[2] == 'camera':
                frame_id = int(cols[3])
                # if frame_id >= stop_frame:
                #     break
                # if self.jpeg_extractor.done:
                #     if len(self.video_files) == 0:
                #         print("End of video file(s).")
                #         break
                #     else:
                #         video_dir = os.path.join(self.base_dir, 'video')
                #         self.jpeg_extractor.open(os.path.join(video_dir, self.video_files.pop(0)))
                # jpg = self.jpeg_extractor.read()
                fid, jpg = next(self.jpeg_extractor)
                dt = self.t0 + ts - time.time()
                # print(len(jpg))
                if jpg is None:
                    continue

                if frame_id < self.start_frame:
                    forwarding = True
                    self.t0 = time.time() - ts
                    # print('skipping frame', frame_id)
                    continue
                else:
                    forwarding = False

                r = {'ts': ts, 'img': jpg}

                # msg = b'0' * 4 + frame_id.to_bytes(4, 'little', signed=False) + struct.pack('<d', ts) + jpg
                if dt > 0.1:
                    print('----dt {}----'.format(dt))

                if dt <= 0.001:
                    # nanomsg.wrapper.nn_send(self.socks['camera'], msg, 0)
                    self.cam_queue.put((frame_id, r, 'camera'))
                    # print('sent img {} size {} dt {}'.format(cols[3].strip(), len(jpg), dt), self.cam_queue.qsize())
                elif dt > 0.2 * (frame_id - self.last_frame) or dt > 1.0:
                    self.t0 += dt
                    # nanomsg.wrapper.nn_send(self.socks['camera'], msg, 0)
                    self.cam_queue.put((frame_id, r, 'camera'))
                    # print('sent img {} size {} dt {}'.format(cols[3].strip(), len(jpg), dt), self.cam_queue.qsize())
                else:
                    # self.sched.enter(dt, 1, nanomsg.wrapper.nn_send,
                    #                  argument=(self.socks['camera'], msg, 0))
                    # print('sent img {} size {} dt {}'.format(cols[3].strip(), len(jpg), dt), self.cam_queue.qsize())
                    self.sched.enter(dt, 1, self.cam_queue.put, argument=((frame_id, r, 'camera'),))
                self.last_frame = frame_id

                print('sent img {} size {} dt {:.6f}'.format(cols[3].strip(), len(jpg), dt), self.cam_queue.qsize())
                # time.sleep(0.01)
            if forwarding:
                print('\rnow frame {},forwarding to {}...'.format(frame_id, self.start_frame), end='')
                continue

            if 'CAN' in cols[2]:
                msg_type = cols[2]
                can_id = int(cols[3], 16).to_bytes(4, 'little')
                if int(cols[3], 16) == 0xc7 and rtk_dec:
                    continue
                data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                msg = b'0000' + can_id + struct.pack('<d', ts) + data

                # print(cols[2], '0x{:03x}'.format(int(cols[3], 16)), ts)
                for parser in self.parser[msg_type]:
                    # print("0x%x" % can_id, parser)
                    r = parser(int(cols[3], 16), data, self.context[msg_type])
                    if r is not None:
                        break
                if r is None:
                    continue
                if isinstance(r, list):
                    # print('r is list')
                    for obs in r:
                        obs['ts'] = ts
                        # obs['source'] = self.msg_types[int(msg_type[3])]
                        obs['source'] = self.can_types[msg_type]
                else:
                    # print('r is not list')
                    r['ts'] = ts
                    # r['source'] = self.msg_types[int(msg_type[3])]
                    r['source'] = self.can_types[msg_type]
                    # if 'rtk' in r['source']:
                    #     print(r['source'])
                # if self.can_types[msg_type] == 'rtk.3':
                #     continue

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

            if 'rtk' in cols[2] and 'sol' in cols[2]:
                rtk_dec = True
                source = '.'.join(cols[2].split('.')[0:2])
                r = {'type': 'rtk', 'source': source, 'ts': ts, 'ts_origin': ts}
                r['rtkst'], r['orist'], r['lat'], r['lon'], r['hgt'], r['velN'], r['velE'], \
                r['velD'], r['yaw'], r['pitch'], r['length'] = \
                (float(x) for x in cols[3:14])
                r['rtkst'] = int(r['rtkst'])
                r['orist'] = int(r['orist'])

                if r['orist'] > 34:
                    vehstate = {'type': 'vehicle_state', 'pitch': r['pitch'], 'yaw': r['yaw'], 'ts': ts}
                else:
                    vehstate = None

                dt = self.t0 + ts - time.time()

                self.sched.enter(dt, 1, self.msg_queue.put, argument=((0xc7, [r, vehstate], 'can'),))

            if 'rtk.target' in cols[2]:
                range = float(cols[3])
                angle = float(cols[4])
                height = float(cols[5])
                r = {'source': cols[2], 'type': cols[2], 'ts': ts, 'range': range, 'angle': angle, 'height': height}

                dt = self.t0 + ts - time.time()

                self.sched.enter(dt, 1, self.msg_queue.put, argument=((0xc7, r, 'can'),))

            if 'rtk' in cols[2] and 'bestpos' in cols[2]:
                r = dict()
                r['ts'] = ts
                r['type'] = 'bestpos'
                r['source'] = '.'.join(cols[2].split('.')[:2])

                fields = cols[3:]

                r['sol_stat'] = fields[0]
                r['pos_type'] = fields[1]
                r['lat'] = float(fields[2])
                r['lon'] = float(fields[3])
                r['hgt'] = float(fields[4])
                r['undulation'] = float(fields[5])
                r['datum'] = fields[6]
                r['lat_sgm'] = float(fields[7])
                r['lon_sgm'] = float(fields[8])
                r['hgt_sgm'] = float(fields[9])
                # r['station_id'] = fields[10]
                r['diff_age'] = float(fields[10])
                r['sol_age'] = float(fields[11])
                r['#SVs'] = int(fields[12])
                r['#solSVs'] = int(fields[13])
                # r['rsv1'] = int(fields[15])
                # r['rsv2'] = int(fields[16])
                # r['rsv3'] = int(fields[17])
                r['ext_sol_stat'] = int(fields[14], 16)
                # r['rsv4'] = int(fields[19])
                # r['sig_mask'] = int(fields[20], 16)

                dt = self.t0 + ts - time.time()

                self.sched.enter(dt, 1, self.msg_queue.put, argument=((0xc7, r, 'can'),))

            if 'rtk' in cols[2] and 'heading' in cols[2]:
                r = dict()
                r['ts'] = ts
                r['type'] = 'heading'
                r['source'] = '.'.join(cols[2].split('.')[:2])

                fields = cols[3:]
                # r = dict()
                r['ts'] = ts
                r['type'] = 'heading'
                r['sol_stat'] = fields[0]
                r['pos_type'] = fields[1]
                r['length'] = float(fields[2])
                r['yaw'] = float(fields[3])
                r['pitch'] = float(fields[4])
                # r['rsv1'] = fields[5]
                r['hdgstddev'] = float(fields[5])
                r['ptchstddev'] = float(fields[6])
                # r['station_id'] = fields[8]
                r['#SVs'] = int(fields[7])
                r['#solSVs'] = int(fields[8])
                r['#obs'] = int(fields[9])
                r['#multi'] = int(fields[10])
                # r['rsv2'] = fields[13]
                r['ext_sol_stat'] = int(fields[11], 16)
                # r['rsv4'] = int(fields[15])
                # r['sig_mask'] = int(fields[16], 16)

                dt = self.t0 + ts - time.time()

                self.sched.enter(dt, 1, self.msg_queue.put, argument=((0xc7, r, 'can'),))

            self.sched.run()

        rf.close()
        # cp.disable()
        # cp.print_stats()


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


def prep_replay(source):
    if os.path.isdir(source):
        loglist = sorted(os.listdir(source), reverse=True)
        source = os.path.join(os.path.join(source, loglist[0]), 'log.txt')

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

    return r_sort

if __name__ == "__main__":
    from config.config import *

    freeze_support()
    # source = '/home/yj/bak/data/AEB/AEB_X1_test/20190412121015_CCRS_40kmh/log.txt'
    source = '/home/yj/bak/data/J1242/20190524-J1242-x1-esr-suzhou/pcc/20190524191405-case3/log.txt'
    # source = local_cfg.log_root  # 这个是为了采集的时候，直接看最后一个视频
    r_sort = prep_replay(source)

    from pcc import PCC
    from parsers.parser import parsers_dict

    # print(install['video'])
    replayer = LogPlayer(r_sort, configs, start_frame=0, ratio=0.2)

    # replayer.start()
    pc_viewer = PCC(replayer, replay=True, rlog=r_sort, ipm=True)
    pc_viewer.start()

    # while True:
    #     replayer.pop_simple()
