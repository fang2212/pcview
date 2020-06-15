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
from parsers import ublox
from recorder.convert import *
from collections import deque
import shutil
import os
from config.config import CVECfg, load_config, load_installation
from parsers.parser import parsers_dict
from config.config import *
from tools.log_info import *
# from numba import jit


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
        line = self.x1_fp.readline()
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


class LogPlayer(Process):

    def __init__(self, log_path, uniconf=None, start_frame=0, ratio=1.0, loop=False):
        super(LogPlayer, self).__init__()
        # self.daemon = False
        self.time_aligned = True
        self.log_path = log_path
        self.start_frame = start_frame
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
        self.context = {}
        self.ratio = ratio
        self.ctrl_q = Queue()
        self.type_roles = {}
        self.cfg = uniconf
        # self.pcv_cache = deque(maxlen=500)

        self.last_time = 0
        self.hz = 20
        self.loop = loop

        self.last_ts = 0

        self.buf = []
        self.replay_speed = 2  # 2x speed replay
        self.now_frame_id = 0
        self.pause_state = False
        self.paused_t = 0
        # self.init_env()

    def init_env(self):
        self.shared['replay_sync'] = True
        while not self.msg_queue.empty():
            self.msg_queue.get()
        self.jpeg_extractor = jpeg_extractor(os.path.dirname(self.log_path) + '/video')
        # self.x1_fp = None
        # self.shared['t0'] = 0
        self.main_idx = get_main_index(self.log_path)
        main_dev = get_main_dev(self.log_path)
        x1_log = os.path.dirname(self.log_path) + '/pcv_log.txt'
        if main_dev and main_dev['type'] == 'x1_algo' and os.path.exists(x1_log):
            self.x1_parser = PcvParser(open(x1_log))
        else:
            self.x1_parser = None

        # if os.path.exists(self.x1_log):
        #     self.x1_fp = open(self.x1_log, 'r')

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
                for mtype in cfg['msg_types']:
                    self.msg_types.append(mtype)
                    if 'can0' in cfg['ports']:
                        self.can_types['CAN' + '{:01d}'.format(idx * 2)] = cfg['ports']['can0']['topic']
                    if 'can1' in cfg['ports']:
                        self.can_types['CAN' + '{:01d}'.format(idx * 2 + 1)] = cfg['ports']['can1']['topic']
                # if cfg.get('is_main'):
                #     self.jpeg_extractor = jpeg_extractor(os.path.dirname(log_path) + '/video.{}'.format(cfg.get('idx')))
        print('msgtypes:', self.msg_types)

        self.msg_types = [x if len(x) > 0 else '' for x in list(self.can_types.values()) if len(x) > 2]

        for can in self.can_types:
            # print(can)
            self.parser[can] = []
            self.context[can] = {}
            for type in parsers_dict:
                if type in self.can_types[can]:
                    print('----', can, type)
                    self.parser[can].append(parsers_dict[type])
            if len(self.parser[can]) == 0:
                self.parser[can] = [parsers_dict['default']]
        self.cache['can'] = []

        self.shared['t0'] = time.time()
        print('t0 set to', self.shared['t0'])
        with open(self.log_path) as rf:
            cols = rf.readline().split(' ')
            self.shared['ts0'] = float(cols[0]) + float(cols[1]) / 1000000
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
            # print(data)
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
            if dt > 0.0002:  # smallest interval that sleep can actually delay
                # print('sleep', dt)
                # print(data)
                pass
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
                # self.init_env()
                # print(self.shared['ts0'], self.shared['t0'])
        self._do_replay()

    # @jit(nopython=True)
    def _do_replay(self):
        self.init_env()
        last_fid = 0
        frame_lost = 0
        total_frame = 0
        rtk_dec = False
        lcnt = 0
        fid_forward = 0
        # pcv = PcvParser(self.x1_fp)
        rf = open(self.log_path)
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

            while self.msg_queue.full():
                # print('msg queue full, sleep 0.01')
                time.sleep(0.01)

            # if 'replay_speed' in self.d:
            #     self.replay_speed = self.d['replay_speed']

            # if self.cam_queue.qsize() > 20:  # if cache longer than 1s then slow down the log reading
            #     time.sleep(0.01)
                # print('replay camque', self.cam_queue.qsize())

            # print('line {}'.format(cnt))
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000

            if cols[2] == 'camera':
                frame_id = int(cols[3])
                if last_fid == 0:
                    last_fid = frame_id - 1
                frame_lost += frame_id - last_fid - 1
                total_frame += 1
                last_fid = frame_id

                try:
                    if frame_id >= fid_forward:
                        fid, jpg = next(self.jpeg_extractor)
                    else:
                        fid = fid_forward
                        jpg = None
                except StopIteration:
                    print('images run out.')
                    return
                if fid and fid != frame_id:
                    print(bcl.FAIL+'raw fid differs from log:'+bcl.ENDC, fid, frame_id)
                    if fid < frame_id:
                        for i in range(frame_id - fid):
                            _, jpg = next(self.jpeg_extractor)
                    else:
                        fid_forward = fid
                lcnt += 1
                if jpg is None or lcnt % self.replay_speed != 0 or self.now_frame_id < self.start_frame:
                    self.now_frame_id = frame_id
                    continue

                self.now_frame_id = frame_id
                # print(lcnt, frame_id, self.replay_speed)
                r = {'ts': ts, 'img': jpg}
                r['is_main'] = True
                r['source'] = 'video'
                r['type'] = 'video'
                self.msg_queue.put((frame_id, r, 'camera'))

                if self.x1_parser:
                    res = self.x1_parser.get_frame(frame_id)
                    if res:
                        res['ts'] = ts
                        res['source'] = 'x1_data.{}'.format(self.main_idx)
                        # print(res)
                        self.msg_queue.put((frame_id, res, res['source']))
                # self.cache.clear()
                # self.cache['can'] = []
                # print('sent img {} size {}'.format(cols[3].strip(), len(jpg)), self.cam_queue.qsize())

            if self.now_frame_id < self.start_frame:
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

            elif 'rtk' in cols[2]:  # new ub482
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

            elif 'NMEA' in cols[2] or 'gps' in cols[2]:
                r = ublox.decode_nmea(cols[3])
                r['source'] = cols[2]
                # self.cache['can'].append(r.copy())
                self.msg_queue.put((0x00, r, cols[2]))
        print(bcl.OKBL+'log.txt reached the end.'+bcl.ENDC)
        rf.close()
        return
        # cp.disable()
        # cp.print_stats()


def prep_replay(source, ns=False):
    if os.path.isdir(source):
        loglist = sorted(os.listdir(source), reverse=True)
        source = os.path.join(os.path.join(source, loglist[0]), 'log.txt')

    r_sort = os.path.join(os.path.dirname(source), 'log_sort.txt')

    if os.path.exists(r_sort):
        pass
    else:
        if ns:
            r_sort = source
        else:
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

    # return source
    return r_sort, uniconf


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
    parser.add_argument('-v', '--virtual', action="store_true")

    args = parser.parse_args()
    source = args.input_path
    if args.render:
        if args.output:
            odir = args.output
        else:
            odir = os.path.dirname(source)
    else:
        odir = None

    freeze_support()
    # source = sys.argv[1]
    print(source)
    # source = local_cfg.log_root  # 这个是为了采集的时候，直接看最后一个视频

    from tools import mytools
    ns = args.nosort
    r_sort, cfg = prep_replay(source, ns=ns)
    from pcc import PCC

    replayer = LogPlayer(r_sort, cfg, ratio=0.2, start_frame=0, loop=args.loop)
    if args.web:
        from video_server import PccServer
        server = PccServer()
        server.start()
        pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, save_replay_video=odir, uniconf=cfg, to_web=server)
        print(os.getpid())
        replayer.start()
        pcc.start()
        while True:
            time.sleep(1)
    else:
        pcc = PCC(replayer, replay=True, rlog=r_sort, ipm=True, save_replay_video=odir, uniconf=cfg)
        replayer.start()
        pcc.start()



