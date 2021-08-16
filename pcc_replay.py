#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/11/2
# @Author  : simon.xu
# @File    : replay.py
# @Desc    : log replayer for collected data

import struct
import time
from multiprocessing import Process, Queue, Manager, freeze_support
import json
from threading import Thread

import cv2
import numpy as np
from tqdm import tqdm
from turbojpeg import TurboJPEG

from parsers import ublox
from recorder.convert import *
from collections import deque
import shutil
import os
from config.config import CVECfg, load_config, load_installation
from parsers.parser import parsers_dict
from config.config import *
from tools.log_info import *
from parsers.novatel import parse_novatel
from parsers.pim222 import parse_pim222
# from numba import jit
from tools import mytools

jpeg = TurboJPEG()

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
        fcnt = 0
        fid = int(file.split('.')[0].split('_')[1])
        with open(os.path.join(video_dir, file), 'rb') as vf:
            while True:
                a = buf.find(b'\xff\xd8')
                b = buf.find(b'\xff\xd9')
                while a == -1 or b == -1:
                    read = vf.read(buf_len)
                    if len(read) == 0:
                        file_done = True
                        buf = b''
                        print('video file {} comes to an end. {} frames extracted'.format(file, fcnt))
                        break
                    buf += read
                    a = buf.find(b'\xff\xd8')
                    b = buf.find(b'\xff\xd9')

                if file_done:
                    break
                jpg = buf[a:b + 2]
                buf = buf[b + 2:]
                fcnt += 1
                jfid = int.from_bytes(jpg[24:28], byteorder="little")
                if not jpg:
                    print('extracted empty frame:', fid)

                yield fid, jpg
                if fid is not None:
                    fid = None


class PcvParser(object):
    def __init__(self, x1_fp):
        super(PcvParser, self).__init__()
        self.x1_fp = x1_fp
        # self.cache = deque(maxlen=3000)
        self.cache = {}
        self.req_fid = 0
        self.cur_fid = 0
        # self.start()

    def read(self):
        try:
            line = self.x1_fp.readline()
        except Exception as e:
            print(e)
            return
        if not line:
            return -1

        try:
            line = line.strip()
            data = json.loads(line)
            if 'ultrasonic' in data:
                self.cache[self.cur_fid].append(data)
                return self.cur_fid
            else:
                self.cur_fid = data['frame_id']
            # print(data['frame_id'])
            if data['frame_id'] not in self.cache:
                self.cache[data['frame_id']] = {'type': 'pcv_data'}
            for key in data:
                self.cache[data['frame_id']][key] = data[key]
            # self.cache[data['frame_id']].append(data)

            if len(self.cache) > 1000:
                for fid in range(data['frame_id']-1000, data['frame_id']-600):
                    if fid in self.cache:
                        del self.cache[fid]
        except Exception as e:
            print('pcv decode error', e)
            print(line)
            return

        return data['frame_id']

    def get_frame(self, fid):
        max_search = 500
        for i in range(max_search):
            rfid = self.read()
            if rfid == -1:
                return
            if fid not in self.cache:
                rfid = self.read()
            elif rfid and rfid > fid+50:
                break

        res = self.cache.get(fid)

        return res


def list_recorded_data(log_path='~/data/pcc'):
    dirs = os.listdir(log_path)
    recorded_data = list()
    for dir in dirs:
        path = os.path.join(log_path, dir)
        recorded_data.append({'name': dir, 'path': path})

    return recorded_data


class ThreadGateway(Thread):
    def __init__(self, name=None, group=None, target=None, args=(), kwargs=None, *, daemon=None):
        super(ThreadGateway, self).__init__(target=target)
        self.received = 0
        self.sent = 0
        self.last_update = 0.0
        self.setName(name)
        self.info = None


# from nanomsg import Socket, PUB
import nnpy
class NNSender(ThreadGateway):
    def __init__(self, port=5010, name='NNSender'):
        super(NNSender, self).__init__(name)
        addr = 'tcp://0.0.0.0:{}'.format(port)
        self.port = port
        self.sndq = Queue()
        self.addr = addr

    def run(self):
        with nnpy.Socket(nnpy.AF_SP, nnpy.PUB) as spub:
            spub.bind(self.addr)
            print('started NN PUB server on', self.addr)
            while True:
                if not self.sndq.empty():
                    data = self.sndq.get()
                    self.received += len(data)
                    spub.send(data)
                    self.sent += len(data)
                    self.last_update = time.ctime()
                else:
                    time.sleep(0.1)


class sched_nn_sender(Process):
    def __init__(self):
        super(sched_nn_sender, self).__init__()

# def generate_dev_conf(log, opath):
#     ports_topics = get_ports_topics(log)
#     cfg = {}
#     cfg
#

class LogPlayer(Process):

    def __init__(self, log_path, uniconf=None, start_frame=0, end_frame=None, start_time=0, end_time=None, ratio=1.0,
                 loop=False, nnsend=False, nosort=False, real_interval=False, chmain=None):
        super(LogPlayer, self).__init__()
        self.start_frame = int(start_frame) if start_frame else 0
        self.end_frame = int(end_frame) if end_frame else 9999999999999
        self.start_time = int(start_time) if start_time else 0
        self.end_time = int(end_time) if end_time else 9999999999999
        # self.daemon = False
        self.time_aligned = True
        self.log_path = log_path
        self.socks = {}
        self.shared = Manager().dict()
        self.shared['t0'] = 0  # time when start replaying
        self.shared['ts0'] = 0  # start ts of log
        self.last_frame = 0
        self.jpeg_extractor = None
        self.base_dir = os.path.dirname(self.log_path)
        self.msg_queue = Queue(maxsize=50)
        # self.cam_queue = Queue()
        self.cache = {}
        self.msg_cnt = {}
        self.msg_cnt['frame'] = 0
        self.parser = {}
        self.can_types = {}
        self.msg_types = []
        # self.configs_valid = {}
        self.context = {}
        self.ratio = ratio
        self.ctrl_q = Queue()
        self.type_roles = {}
        self.cfg = uniconf
        self.real_interval = real_interval
        # self.pcv_cache = deque(maxlen=500)

        self.last_time = 0
        self.hz = 20
        self.loop = loop

        self.last_ts = 0

        self.buf = []
        self.replay_speed = 1  # 2x speed replay
        self.now_frame_id = 0
        self.pause_state = False
        self.paused_t = 0
        # self.init_env()
        self.nosort = nosort
        self.nnsend = nnsend
        if nnsend:
            self.senders = {}
            port_start = 6000
            p_t = get_ports_topics(log_path)
            # print(p_t)
            for idx, key in enumerate(p_t):
                port_num = port_start + idx
                print(port_num, key, p_t.get(key))
                self.senders[key] = NNSender(port_num)
                self.senders[key].start()

        self.video_dir = "video"
        self.video_log_key = "camera"
        if chmain:
            self.video_dir = chmain
            self.video_log_key = chmain
        self.chmain = chmain

    def init_env(self):
        self.shared['replay_sync'] = True
        self.shared['t0'] = time.time()
        print('t0 set to', self.shared['t0'])
        with open(self.log_path) as rf:
            done = False
            while not done:
                line = rf.readline()
                # print(line)
                try:
                    cols = line.split(' ')
                    self.shared['ts0'] = float(cols[0]) + float(cols[1]) / 1000000
                except Exception as e:
                    continue
                done = True
        while not self.msg_queue.empty():
            self.msg_queue.get()
        self.jpeg_extractor = jpeg_extractor(os.path.dirname(self.log_path) + '/' + self.video_dir)
        # self.x1_fp = None
        # self.shared['t0'] = 0
        self.main_idx = get_main_index(self.log_path)
        main_dev = get_main_dev(self.log_path)

        chmain = self.chmain
        if chmain is not None:
            idx = int(chmain.split(".")[-1])
            for f in self.cfg.configs:
                if f.get("idx") == idx:
                    main_dev = f
                    break
        x1_log = os.path.dirname(self.log_path) + "/" + main_dev['type']+"." + str(main_dev['idx']) + '/pcv_log.txt'
        print(x1_log, main_dev, main_dev['type'])
        if main_dev and "algo" in main_dev['type'] and os.path.exists(x1_log):
            print("x1_log:", x1_log)
            self.x1_parser = PcvParser(open(x1_log))
        else:
            self.x1_parser = None

        self.bin_rf = {}

        for idx, cfg in enumerate(self.cfg.configs):
            if 'can_types' in cfg:
                cantypes0 = ' '.join(cfg['can_types']['can0']) + '.{:01}'.format(idx)
                cantypes1 = ' '.join(cfg['can_types']['can1']) + '.{:01}'.format(idx)
                self.can_types['CAN' + '{:01d}'.format(idx * 2)] = cantypes0
                self.can_types['CAN' + '{:01d}'.format(idx * 2 + 1)] = cantypes1
                if len(cfg['can_types']['can0']) > 0:
                    self.msg_types.append([cantypes0])
                if len(cfg['can_types']['can1']) > 0:
                    self.msg_types.append([cantypes1])
            elif 'msg_types' in cfg:
                # print(cfg)
                if 'can0' in cfg['ports']:
                    msg_type = cfg['ports']['can0']['topic']
                    self.can_types['CAN' + '{:01d}'.format(idx * 2)] = msg_type + '.{}'.format(idx)
                if 'can1' in cfg['ports']:
                    msg_type = cfg['ports']['can1']['topic']
                    self.can_types['CAN' + '{:01d}'.format(idx * 2 + 1)] = msg_type + '.{}'.format(idx)
        # print('msgtypes:', self.msg_types)

        # self.msg_types = [x if len(x) > 0 else '' for x in list(self.can_types.values()) if len(x) > 2]

        for can in self.can_types:
            # print(can)
            self.parser[can] = []
            self.context[can] = {}
            # print(can, self.can_types[can])
            for type in parsers_dict:
                if type == self.can_types[can].split('.')[0]:
                    print('----', can, type, parsers_dict[type])
                    self.parser[can].append(parsers_dict[type])
            if len(self.parser[can]) == 0:
                self.parser[can] = [parsers_dict['default']]
        self.cache['can'] = []
        self.shared['replay_sync'] = False

    def get_veh_role(self, source):
        if not source:
            return
        if source in self.type_roles:
            return self.type_roles[source]
        for cfg in self.cfg.configs:
            msg_types = cfg.get('msg_types')
            if not msg_types:
                continue
            if source in msg_types:
                return cfg.get('veh_tag')
        return 'default'

    def pop_common(self):
        ts_n = time.time()
        # print('pop interval: {:.2f}ms'.format(1000*(ts_n-self.last_ts)))
        self.last_ts = ts_n
        # if not self.shared['t0']:
        #     self.shared['t0'] = time.time()
        #     print('t0 set to', self.shared['t0'])
        if not self.msg_queue.empty() and not self.shared['replay_sync']:
            frame_id, data, msg_type = self.msg_queue.get()
            if not data:
                return

            tsnow = data['ts'] if isinstance(data, dict) else data[0]['ts']
            # try:
            #     tsnow = data['ts'] if isinstance(data, dict) else data[0]['ts']
            # except Exception as e:
            #     print('error in pop_common:', data)
            #     return
                # raise e
            dt = (tsnow - self.shared['ts0'])/self.replay_speed - (time.time() - self.paused_t - self.shared['t0'])
            # print(tsnow, self.shared['ts0'], time.time(), self.shared['t0'])
            # print(self.msg_queue.qsize())
            if not self.nosort and dt > 0.0002:  # smallest interval that sleep can actually delay
                # print('sleep', dt)
                # print(data)
                pass
                if self.real_interval:
                    time.sleep(dt)
            # print('pop common', frame_id, len(data))
            return frame_id, data, msg_type
        else:
            # print('msg empty sleep 0.01')
            time.sleep(0.001)

    def pause(self, pause):
        if pause:
            self.pause_state = True
            self.last_pause_ts = time.time()
            self.ctrl_q.put({'action': 'pause'})
        else:
            self.pause_state = False
            self.ctrl_q.put({'action': 'resume'})

    def add_pause(self, t):
        self.paused_t += t

    def run(self):
        # self.init_socket()
        # cp = cProfile.Profile()
        # cp.enable()
        if self.loop:
            while True:
                self._do_replay()
                print('replay start over.')
                time.sleep(0.5)
                # print(self.shared['ts0'], self.shared['t0'])
        self._do_replay()
        print('exit replaying.')

    # @jit(nopython=True)
    def _do_replay(self):
        self.init_env()
        last_fid = 0
        frame_lost = 0
        total_frame = 0
        pass_forward = False
        rtk_dec = False
        lcnt = 0
        fid_forward = self.start_frame
        # pcv = PcvParser(self.x1_fp)
        rf = open(self.log_path)
        ctx = {}
        for line in rf:
            if not self.ctrl_q.empty():
                ctrl = self.ctrl_q.get()
                if ctrl.get('action') == 'pause':
                    print('replay paused.')
                    while True:
                        ctrl = self.ctrl_q.get()
                        if ctrl and ctrl.get('action') != 'pause':
                            break
                        else:
                            time.sleep(0.01)
            line = line.strip()
            if line == '':
                continue
            # print(line)
            # if 'replay_speed' in self.d:
            #     self.replay_speed = self.d['replay_speed']

            # if self.cam_queue.qsize() > 20:  # if cache longer than 1s then slow down the log reading
            #     time.sleep(0.01)
                # print('replay camque', self.cam_queue.qsize())

            # print('line {}'.format(cnt))
            cols = line.split(' ')
            try:
                ts = float(cols[0]) + float(cols[1]) / 1000000
            except Exception as e:
                continue

            if cols[2] == self.video_log_key:
                frame_id = int(cols[3])
                if last_fid == 0:
                    last_fid = frame_id - 1
                frame_lost += frame_id - last_fid - 1
                total_frame += 1
                last_fid = frame_id

                try:
                    fid, jpg = next(self.jpeg_extractor)
                except StopIteration as e:
                    print('images run out.')
                    return
                if fid and fid != frame_id:
                    print(bcl.FAIL+'raw fid differs from log:'+bcl.ENDC, fid, frame_id)
                # if fid and fid < self.start_frame:
                #     print('fid from jpeg drop backward', fid, self.start_frame)
                #     for i in range(self.start_frame-fid-1):
                #         _, jpg = next(self.jpeg_extractor)
                lcnt += 1
                if self.now_frame_id < self.start_frame:
                    print('fid from log drop backward', self.now_frame_id, self.start_frame)
                    while self.now_frame_id < self.start_frame:
                        line = rf.readline().strip()
                        if line == "":
                            continue

                        cols = line.split(' ')
                        if cols[2] == self.video_log_key:
                            self.now_frame_id = int(cols[3])
                            _, jpg = next(self.jpeg_extractor)
                    print("跳到当前帧数：", self.now_frame_id)
                if jpg is None or lcnt % self.replay_speed != 0:
                    self.now_frame_id = frame_id
                    pass_forward = True
                    continue
                pass_forward = False
                self.now_frame_id = frame_id
                # print(lcnt, frame_id, self.replay_speed)
                r = {'ts': ts, 'img': jpg}
                r['is_main'] = True
                r['source'] = 'video'
                r['type'] = 'video'
                while self.msg_queue.full():
                    # print('msg queue full, sleep 0.01')
                    time.sleep(0.01)
                self.msg_queue.put((frame_id, r, 'camera'))

                if self.x1_parser:
                    res = self.x1_parser.get_frame(frame_id)

                    if res:
                        res['ts'] = ts
                        res['source'] = 'x1_data'
                        self.msg_queue.put((frame_id, res, res['source']))

                if self.nnsend:
                    msg = b'0000' + frame_id.to_bytes(4, 'little') + struct.pack('<d', ts) + jpg
                    sender = self.senders.get(cols[2])
                    if sender:
                        # print('sending frame', frame_id)
                        sender.sndq.put(msg)
                # self.cache.clear()
                # self.cache['can'] = []
                # print('sent img {} size {}'.format(cols[3].strip(), len(jpg)), self.cam_queue.qsize())

            if pass_forward:
                continue
            if self.now_frame_id >= self.end_frame:
                print('log player reached the end frame:', self.end_frame)
                break

            if 'CAN' in cols[2]:
                msg_type = cols[2]
                can_id = int(cols[3], 16).to_bytes(4, 'little')
                if int(cols[3], 16) == 0xc7 and rtk_dec:
                    continue
                if len(cols[4]) > 2:
                    data = bytes().fromhex(cols[4])
                else:
                    data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                if self.nnsend:
                    msg = b'0000' + can_id + struct.pack('<d', ts) + data
                    sender = self.senders.get(cols[2])
                    if sender:
                        sender.sndq.put(msg)

                # print(cols[2], '0x{:03x}'.format(int(cols[3], 16)), ts)
                if msg_type not in self.parser:
                    continue

                for parser in self.parser[msg_type]:
                    # print("0x%x" % can_id, parser)
                    r = parser(int(cols[3], 16), data, self.context[msg_type])
                    if r is not None:
                        # print(parser, r)
                        break
                if r is None:
                    continue

                if isinstance(r, list):
                    # print('r is list')
                    for idx, obs in enumerate(r):
                        r[idx]['ts'] = ts
                        # obs['source'] = self.msg_types[int(msg_type[3])]
                        r[idx]['source'] = self.can_types[msg_type]
                        # print(r[idx])

                else:
                    # print('r is not list')
                    r['ts'] = ts
                    # r['source'] = self.msg_types[int(msg_type[3])]
                    r['source'] = self.can_types[msg_type]
                # print(r)
                self.msg_queue.put((can_id, r.copy(), self.can_types[msg_type]))

                # if isinstance(r, list):
                #     # print('msg data list')
                #     self.cache['can'].extend(r.copy())
                # elif isinstance(r, dict):
                #     self.cache['can'].append(r.copy())
            elif "can" in cols[2]:
                if not self.parser.get(cols[2]):
                    msg_type = cols[2].split(".")[-1]
                    idx = cols[2].split(".")[1]
                    self.parser[cols[2]] = parsers_dict[msg_type] if parsers_dict.get(msg_type) else parsers_dict["default"]
                    self.context[cols[2]] = {"source": "{}.{}".format(msg_type, idx)}
                can_id = int(cols[3], 16).to_bytes(4, 'little')
                data = bytes().fromhex(cols[4])

                r = self.parser[cols[2]](int(cols[3], 16), data, self.context[cols[2]])
                if r is None:
                    continue
                if isinstance(r, list):
                    for idx, obs in enumerate(r):
                        r[idx]['ts'] = ts
                else:
                    r['ts'] = ts
                self.msg_queue.put((can_id, r.copy(), self.context[cols[2]]["source"]))

            elif cols[2] == 'Gsensor':
                data = [int(x) for x in cols[3:9]]
                msg = struct.pack('<BBhIdhhhhhhhq', 0, 0, 0, 0, ts, data[3], data[4], data[5], data[0], data[1], data[2],
                                  int((float(cols[9]) - 36.53) * 340), 0)

            elif 'rtk' in cols[2] and 'sol' in cols[2]:  # old d-rtk
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
                # self.cache['can'].extend([r, vehstate])
                # print(r)
                self.msg_queue.put((0xc7, [r, vehstate], source))

            # if 'rtk.target' in cols[2]:
            #     range = float(cols[3])
            #     angle = float(cols[4])
            #     height = float(cols[5])
            #     r = {'source': cols[2], 'type': cols[2], 'ts': ts, 'range': range, 'angle': angle, 'height': height}
            #     self.cache['can'].append(r.copy())

            elif 'pinpoint' in cols[2]:  # new ub482
                kw = cols[2].split('.')[-1]
                source = '.'.join(cols[2].split('.')[0:2])
                if kw in ub482_defs:
                    r = decode_with_def(ub482_defs, line)
                    if not r:
                        continue
                    r['ts'] = ts
                    r['type'] = kw
                    r['source'] = '.'.join(cols[2].split('.')[:2])
                    # self.cache['can'].append(r.copy())
                    self.msg_queue.put((0xc7, r, source))

                    if self.nnsend:
                        msg = json.dumps(r)
                        sender = self.senders.get('.'.join(cols[2].split('.')[:2]))
                        if sender:
                            sender.sndq.put(msg)

            elif 'NMEA' in cols[2] or 'gps' in cols[2]:
                r = ublox.decode_nmea(cols[3])
                r['source'] = cols[2]
                # self.cache['can'].append(r.copy())
                self.msg_queue.put((0x00, r, cols[2]))
                if self.nnsend:
                    msg = json.dumps(r)
                    sender = self.senders.get('.'.join(cols[2].split('.')[:2]))
                    if sender:
                        sender.sndq.put(msg)
            elif 'inspva' in cols[2]:
                try:
                    r = parse_novatel(None, cols[3], None)
                    r['source'] = '.'.join(cols[2].split('.')[0:2])
                    self.msg_queue.put((0x00, r, r['source']))
                except Exception as e:
                    print(line)
                    raise e
            elif 'imu_data_corrected' in cols[2]:
                pass

            elif 'pim222' in cols[2]:
                r = parse_pim222(None, cols[3], ctx)
                # print(r)
                if r:
                    r['source'] = cols[2]
                    self.msg_queue.put((0x00, r, r['source']))

            elif 'q4_100' in cols[2]:
                if cols[2] not in self.bin_rf:
                    self.bin_rf[cols[2]] = open(os.path.join(os.path.dirname(self.log_path), cols[2], cols[2] + ".bin"), "rb")
                sz = int(cols[3])
                bts = self.bin_rf[cols[2]].read(sz)
                ret = parsers_dict.get("q4_100", "default")(0, bts)
                if ret is None:
                    continue
                if type(ret) != list:
                    ret = [ret]

                for obs in ret:
                    obs['ts'] = ts
                    obs['source'] = cols[2]
                self.msg_queue.put(("q4_100", ret.copy(), cols[2]))

        print(bcl.OKBL+'log.txt reached the end.'+bcl.ENDC)
        rf.close()
        return
        # cp.disable()
        # cp.print_stats()


def prep_replay(source, ns=False, chmain=None):
    print("source:", source, "ns:", ns)
    if os.path.isdir(source):
        loglist = sorted(os.listdir(source), reverse=True)
        source = os.path.join(os.path.join(source, loglist[0]), 'log.txt')

    if ns:
        r_sort = source
    else:
        r_sort = os.path.join(os.path.dirname(source), 'log_sort.txt')
        if not os.path.exists(r_sort):
            r_sort = mytools.sort_big_file(source)



    config_path = os.path.join(os.path.dirname(source), 'config.json')
    install_path = os.path.join(os.path.dirname(source), 'installation.json')
    uniconf = CVECfg()
    if os.path.exists(config_path):
        print("using configs:", config_path)
        uniconf.configs = load_config(config_path)
    if os.path.exists(install_path):
        print("using installation:", install_path)
        uniconf.installs = load_installation(install_path)

    # parm copy
    if chmain:
        if chmain in uniconf.installs:
            uniconf.installs['video'] = uniconf.installs[chmain]
        else:
            print("no", chmain, "installation")
    # return source
    return r_sort, uniconf


def start_replay(source_path, args, show_video=True):
    from pcc import PCC
    if args.render:
        if args.output:
            odir = args.output
        else:
            odir = os.path.dirname(source_path)
    else:
        odir = None
    ns = args.nosort
    chmain = args.chmain
    r_sort, cfg = prep_replay(source_path, ns=ns, chmain=chmain)

    replayer = LogPlayer(r_sort, cfg, ratio=0.2, start_frame=args.start_frame, end_frame=args.end_frame,
                         start_time=args.start_time, end_time=args.end_time, loop=args.loop, nnsend=args.send,
                         real_interval=args.real_interval, chmain=chmain)

    if args.web:
        if not show_video:
            return
        from video_server import PccServer
        server = PccServer()
        server.start()
        pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, ipm_bg=args.show_ipm_bg, save_replay_video=odir, uniconf=cfg, to_web=server)
        replayer.start()
        pcc.start()
        while True:
            time.sleep(1)
    else:
        pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, ipm_bg=args.show_ipm_bg, save_replay_video=odir, uniconf=cfg, show_video=show_video)
        replayer.start()
        pcc.start()
        replayer.join()
        pcc.control(ord('q'))


if __name__ == "__main__":
    import argparse

    local_path = os.path.split(os.path.realpath(__file__))[0]
    # print('local_path:', local_path)
    os.chdir(local_path)

    parser = argparse.ArgumentParser(description="Replay CVE log.")

    log = '/home/nan/data/20191122154341_ramp_in/log.txt'

    parser.add_argument('input_path', nargs='?', default=log)
    parser.add_argument('-o', '--output', default=False)
    parser.add_argument('-r', '--render', action='store_true')
    parser.add_argument('-ns', '--nosort', action="store_true")
    parser.add_argument('-l', '--loop', action="store_true")
    parser.add_argument('-w', '--web', action="store_true")
    parser.add_argument('-s', '--send', action="store_true")
    parser.add_argument('-sib', "--show_ipm_bg", action="store_true")
    parser.add_argument('-sf', '--start_frame', default=0)
    parser.add_argument('-ef', '--end_frame', default=None)
    parser.add_argument('-st', '--start_time', default=0)
    parser.add_argument('-et', '--end_time', default=None)
    parser.add_argument('-ri', '--real_interval', action="store_true")
    parser.add_argument('-chmain', default=None, help="change main video")

    args = parser.parse_args()
    source = args.input_path

    freeze_support()

    if os.path.isdir(source):
        dirs = [os.path.join(source, d) for d in os.listdir(source) if os.path.isdir(os.path.join(source, d))]
        for d in tqdm(dirs):
            start_replay(os.path.join(d, "log.txt"), args, show_video=False)
    else:
        start_replay(source, args)

