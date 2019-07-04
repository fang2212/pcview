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
from multiprocessing import Process, Queue, freeze_support


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
        self.buf = self.buf[b + 2:]

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
        self.socks = {}
        self.t0 = 0
        self.last_frame = 0
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

        self.last_time = 0
        self.hz = 20

        self.buf = []
        self.replay_speed = 1
        self.now_frame_id = 0

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
                    print('----', can, type)
                    self.parser[can].append(parsers_dict[type])
            if len(self.parser[can]) == 0:
                self.parser[can] = [parsers_dict['default']]
        self.cache['can'] = []

    def pop_simple(self, pause=False):
        res = {
            'frame_id': None,
            'img': None,
            'vehicle': {},
            'lane': {},
            'ped': {},
            'tsr': {},
            'can': {},
            'extra': {}
        }

        if not self.cam_queue.empty():
            frame_id, data, msg_type, cache = self.cam_queue.get()
            # print(frame_id, msg_type)
            res['ts'] = data['ts']
            res['img'] = data['img']
            res['frame_id'] = frame_id

            if res['img'] is not None:
                for key in list(cache):
                    res[key] = cache[key].copy()
                    # print(key, cache[key])
                    cache[key] = []
                self.msg_cnt['frame'] += 1
                # print('res can', res['can'])
                now = time.time()
                if now - self.last_time < 1.0 / self.hz:
                    time.sleep(1.0 / self.hz + self.last_time - now)
                self.last_time = time.time()
                return res
            else:
                print('error decode img', frame_id, len(data))
        # if not self.msg_queue.empty():
        #     frame_id, msg_data, msg_type = self.msg_queue.get()
        #     # res[msg_type] = msg_data
        #     # res['frame_id'] = frame_id
        #     if isinstance(msg_data, list):
        #         # print('msg data list')
        #         self.cache[msg_type].extend(msg_data)
        #     elif isinstance(msg_data, dict):
        #         self.cache[msg_type].append(msg_data)
        #     # self.msg_cnt[msg_type]['rev'] += 1
        #     # self.msg_cnt[msg_type]['show'] += 1
        # else:
        #     time.sleep(0.001)

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

            if 'replay_speed' in self.d:
                self.replay_speed = self.d['replay_speed']

            # print('line {}'.format(cnt))
            cols = line.split(' ')
            ts = float(cols[0]) + float(cols[1]) / 1000000
            if cols[2] == 'camera':
                frame_id = int(cols[3])
                fid, jpg = next(self.jpeg_extractor)
                lcnt += 1
                if jpg is None or lcnt % self.replay_speed != 0 or self.now_frame_id < self.start_frame:
                    self.now_frame_id = frame_id
                    continue

                self.now_frame_id = frame_id
                # print(lcnt, frame_id, self.replay_speed)
                r = {'ts': ts, 'img': jpg}
                self.cam_queue.put((frame_id, r, 'camera', self.cache.copy()))
                self.cache.clear()
                self.cache['can'] = []
                # print('sent img {} size {}'.format(cols[3].strip(), len(jpg)), self.cam_queue.qsize())

            if lcnt % self.replay_speed != 0 or self.now_frame_id < self.start_frame:
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

                # self.msg_queue.put((can_id, r, 'can'))

                if isinstance(r, list):
                    # print('msg data list')
                    self.cache['can'].extend(r.copy())
                elif isinstance(r, dict):
                    self.cache['can'].append(r.copy())

            if cols[2] == 'Gsensor':
                data = [int(x) for x in cols[3:9]]
                msg = struct.pack('<BBhIdhhhhhhhq', 0, 0, 0, 0, ts, data[3], data[4], data[5], data[0], data[1], data[2],
                                  int((float(cols[9]) - 36.53) * 340), 0)

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
                self.cache['can'].extend([r, vehstate])
                # self.msg_queue.put((0xc7, [r, vehstate], 'can'))

            if 'rtk.target' in cols[2]:
                range = float(cols[3])
                angle = float(cols[4])
                height = float(cols[5])
                r = {'source': cols[2], 'type': cols[2], 'ts': ts, 'range': range, 'angle': angle, 'height': height}
                self.cache['can'].append(r.copy())

            if 'rtk' in cols[2] and 'bestpos' in cols[2]:
                # print('----------------rtk best pos')
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
                # self.msg_queue.put((0xc7, r, 'can'))
                self.cache['can'].append(r.copy())

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
                # self.msg_queue.put((0xc7, r, 'can'))
                self.cache['can'].append(r.copy())
        rf.close()
        # cp.disable()
        # cp.print_stats()


def prep_replay(source):
    if os.path.isdir(source):
        loglist = sorted(os.listdir(source), reverse=True)
        source = os.path.join(os.path.join(source, loglist[0]), 'log.txt')

    r_sort = os.path.join(os.path.dirname(source), 'log_sort.txt')
    if not os.path.exists(r_sort):
        r_sort = mytools.sort_big_file(source)

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
    import sys

    sys.argv.append('/home/cao/pc-collect/20190614173921/log.txt')

    freeze_support()
    source = sys.argv[1]
    print(source)
    # source = local_cfg.log_root  # 这个是为了采集的时候，直接看最后一个视频
    from tools import mytools
    r_sort = prep_replay(source)

    from pcc import PCC
    from parsers.parser import parsers_dict

    replayer = LogPlayer(r_sort, configs, ratio=0.2, start_frame=0)
    # replayer.start()
    pc_viewer = PCC(replayer, replay=True, rlog=r_sort, ipm=True)
    pc_viewer.start()
