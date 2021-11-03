#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/11/2
# @Author  : simon.xu
# @File    : replay.py
# @Desc    : log replayer for collected data
import argparse
import logging
import os.path
import signal
from multiprocessing import Process, Manager, freeze_support, Event
from turbojpeg import TurboJPEG

from parsers import ublox
from recorder.convert import *
from pcc import PCC
from parsers.parser import parsers_dict
from config.config import *
from sink.mmap_queue import MMAPQueue
from sink.sink import can_decode, pim222_decode, q4_decode
from tools.log_info import *
from parsers.novatel import parse_novatel
from tools import mytools
from utils import logger, log_list_from_path


jpeg = TurboJPEG()
sub_processes = []


def term(sig_num, addtion):
    logger.warning('terminate process %d' % os.getpid())
    try:
        logger.warning('the processes is %s' % sub_processes)
        for p in sub_processes:
            if p:
                logger.warning('process %d terminate' % p.pid)
                p.terminate()
            # os.kill(p.pid, signal.SIGKILL)
    except Exception as e:
        logger.exception(e)


def jpeg_extractor(video_dir):
    """
    This generator extract jpg from each of the video files in the directory.
    :param video_dir:
    :return: frame_id: rolling counter of the frame from FPGA (if valid, synced with video name)
             jpg: raw jpg bytes
    """
    buf = b''
    buf_len = int(2 * 1024 * 1024)
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
                if not jpg:
                    logger.warning(f'extracted empty frame:{fid}')

                yield fid, jpg
                if fid is not None:
                    fid = None


class PcvParser(object):
    def __init__(self, x1_fp):
        super(PcvParser, self).__init__()
        self.x1_fp = x1_fp
        self.cache = {}
        self.req_fid = 0
        self.cur_fid = 0

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

            if data['frame_id'] not in self.cache:
                self.cache[data['frame_id']] = {'type': 'pcv_data'}
            self.cache[data['frame_id']].update(data)

            if len(self.cache) > 1000:
                for fid in range(data['frame_id'] - 1000, data['frame_id'] - 600):
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
            if rfid and rfid > fid + 50:
                break
            if fid not in self.cache:
                continue

        res = self.cache.get(fid)
        return res


class LogPlayer(Process):

    def __init__(self, log_path, uniconf=None, start_frame=0, end_frame=None, start_time=0, end_time=None,
                 loop=False, nosort=False, real_interval=False, chmain=None):
        super(LogPlayer, self).__init__()
        self.daemon = True
        self.exit = Event()
        self.bin_rf = {}  # bin文件对象集合
        self.start_frame = int(start_frame) if start_frame else 0
        self.end_frame = int(end_frame) if end_frame else 9999999999999
        self.start_time = int(start_time) if start_time else 0
        self.end_time = int(end_time) if end_time else 9999999999999
        self.time_aligned = True
        self.log_path = log_path
        self.jpeg_extractor = {}          # 视频图片提取生成器集合
        self.x1_parser = {}                 # pcv数据字典
        self.log_keyword = {}               #

        self.shared = Manager().dict()
        self.shared["ready"] = False  # 播放前的数据是否加载完成
        self.shared['init_time'] = 0  # 初始化时间
        self.shared['log_start'] = 0  # 第一条log数据的记录时间

        self.mq = MMAPQueue(1024 * 1024 * 500)

        self.parser = {}
        self.can_types = {}
        self.msg_types = []

        self.cfg = uniconf
        self.real_interval = real_interval

        self.loop = loop
        self.replay_speed = 1  # 2x speed replay
        self.now_frame_id = 0
        self.pause_state = False
        self.paused_t = 0
        self.nosort = nosort

        self.main_video = chmain if chmain else 'camera'

    def init_env(self):
        self.shared['init_time'] = time.time()
        logger.debug('init start in {}'.format(self.shared["init_time"]))

        # 获取log第一条记录的时间
        with open(self.log_path) as rf:
            done = False
            while not done:
                line = rf.readline()
                try:
                    cols = line.split(' ')
                    self.shared['log_start'] = float(cols[0]) + float(cols[1]) / 1000000
                except Exception as e:
                    continue
                done = True

        # 处理配置文件对应的log关键词
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
                for keyword in cfg['ports']:
                    if 'can' in keyword and cfg['ports'][keyword].get("enable"):
                        # log.txt里面映射的字段，优先用topic，这样的话可以在回放的时候自由选择解析方式
                        topics = cfg['ports'][keyword].get('topic') or cfg['ports'][keyword].get('dbc')
                        # dbc解析字段是后面加的 如果没有的话说明是老版本字段topic
                        parser_name = cfg['ports'][keyword].get('dbc') or cfg['ports'][keyword].get('topic')
                        if not parser_name:
                            continue

                        if isinstance(topics, list):
                            topics = topics
                        else:
                            topics = [topics]

                        if isinstance(parser_name, list):
                            parsers = parser_name
                        else:
                            parsers = [parser_name]

                        if cfg["type"] != "can_collector":
                            # 旧版本字段需要进行字段映射来寻找解析方法
                            can_key = 'CAN' + '{:01d}'.format(idx * 2) if keyword == 'can0' else 'CAN' + '{:01d}'.format(idx * 2+1)
                            self.can_types[can_key] = {'parsers': parsers, 'index': idx}
                        else:
                            # 新版本字段仅用来判断是否需要解析
                            for i, t in enumerate(topics):
                                self.can_types['{}.{}.{}.{}'.format(cfg.get('origin_device', cfg['ports'][keyword].get('origin_device')), idx, keyword, t)] = {
                                    "parsers": parsers, "index": idx}
            elif cfg["ip"] == "192.168.30.42":
                device = cfg['origin_device']
                # 华为mdc数据采集
                for keyword in cfg['ports']:
                    if "video" in keyword and cfg['ports'][keyword].get("enable"):
                        dbc = cfg['ports'][keyword].get('dbc')
                        dir_name = "{}.{}".format(cfg['type'], idx)
                        dir_path = os.path.join(os.path.dirname(self.log_path), dir_name)
                        if cfg['origin_device'] == 'mdc':  # 新版本格式
                            log_key = "{}.{}.{}.{}".format(device, idx, keyword, self.dbc)
                            filename = "{}.bin".format(keyword)
                        else:
                            log_key = "mdc_video{}".format(cfg['ports'][keyword]['port'] - 24010)
                            filename = "{}.bin".format(log_key)
                        if log_key not in self.bin_rf:
                            if os.path.exists(os.path.join(dir_path, filename)):
                                self.bin_rf[log_key] = open(os.path.join(dir_path, filename), "rb")
                            else:
                                continue

            if cfg.get("ports", {}).get("video", {}).get("enable"):
                # 检查是否有视频数据
                dir_name = "video" if cfg.get("is_main") else "{}.{:d}".format(cfg["type"], idx)
                log_keyword = "camera" if dir_name == 'video' else dir_name
                video_path = os.path.dirname(self.log_path) + '/' + dir_name
                # 初始化视频图片生成器
                if os.path.exists(video_path):
                    self.jpeg_extractor[log_keyword] = jpeg_extractor(video_path)

                x1_log = os.path.dirname(self.log_path) + "/" + video_path + '/pcv_log.txt'
                if os.path.exists(x1_log):
                    self.x1_parser[log_keyword] = PcvParser(open(x1_log))

        # 打印can信号列表
        for i in self.can_types:
            logger.warning("{} | {}".format(i.ljust(20), self.can_types[i]['parsers']))

        self.shared['ready'] = True

    def get_veh_role(self, source):
        if not source:
            return
        for cfg in self.cfg.configs:
            msg_types = cfg.get('msg_types')
            if not msg_types:
                continue
            if source in msg_types:
                return cfg.get('veh_tag')
        return 'default'

    def put_sink(self, sink):
        """
        放入信号进程的钩子处理，可控制数据放出的速度
        :param sink:
        :return:
        """
        if self.real_interval and sink[2] == "camera":   # 是否以真实速度来回放
            sink_ts = sink[1]['ts'] if isinstance(sink[1], dict) else sink[1][0]['ts']
            dt = (sink_ts - self.shared['log_start']) / self.replay_speed - (time.time() - self.paused_t - self.shared['init_time'])
            if dt > 0:
                time.sleep(dt)

        self.mq.put(sink)

    def pause(self, pause):
        if pause:
            self.pause_state = True
        else:
            self.pause_state = False

    def add_pause(self, t):
        self.paused_t += t

    def close(self):
        self.exit.set()

    def run(self):
        try:
            logger.warning("log player starting, pid: {}".format(os.getpid()))
            self._do_replay()

            # 是否循环播放
            if self.loop:
                while True:
                    self._do_replay()
                    time.sleep(0.5)
            logger.warning('log player exit replaying.')
        except Exception as e:
            logger.exception(e)

    def _do_replay(self):
        self.init_env()
        rtk_dec = False
        rf = open(self.log_path)
        start_time = time.time()
        for line in rf:
            if self.exit.is_set():
                break

            if self.pause_state:
                logger.warning('replay paused.')
                while self.pause_state:
                    time.sleep(0.05)

            line = line.strip()
            if line == '':
                continue
            cols = line.split(' ')
            try:
                ts = float(cols[0]) + float(cols[1]) / 1000000
            except Exception as e:
                continue

            # 视频数据处理
            if self.jpeg_extractor.get(cols[2]):
                frame_id = int(cols[3])

                # 取出视频画面图片
                try:
                    fid, jpg = next(self.jpeg_extractor[cols[2]])
                except StopIteration as e:
                    logger.warning('images run out.')
                    return
                if fid and fid != frame_id:
                    print(bcl.FAIL + 'raw fid differs from log:' + bcl.ENDC, fid, frame_id)

                if cols[2] == self.main_video:
                    # 更新主视频的帧数
                    self.now_frame_id = frame_id
                    # 如果当前帧数跟开始帧数不对，进行跳过同步处理
                    if self.now_frame_id < self.start_frame:
                        logger.warning('fid from log drop backward {} {}'.format(self.now_frame_id, self.start_frame))
                        while self.now_frame_id < self.start_frame:
                            line = rf.readline().strip()
                            if line == "":
                                continue

                            cols = line.split(' ')
                            if cols[2] == self.main_video:
                                frame_id = int(cols[3])
                                _, jpg = next(self.jpeg_extractor)
                                if jpg is None:
                                    self.now_frame_id = frame_id

                source = "video" if cols[2] == self.main_video else cols[2]
                r = {'ts': ts, 'img': jpg, 'is_main': cols[2] == self.main_video, 'source': source, 'type': 'video', 'frame_id': frame_id}
                sink_source = 'camera' if cols[2] == self.main_video else cols[2]
                self.put_sink((frame_id, r, sink_source))

                if self.x1_parser.get(cols[2]):
                    res = self.x1_parser[cols[2]].get_frame(frame_id)
                    if res:
                        res['ts'] = ts
                        res['source'] = 'x1_data'
                        self.put_sink((frame_id, res, res['source']))

                # 超出视频范围，退出处理
                if self.now_frame_id >= self.end_frame:
                    logger.error('log player reached the end frame:'.format(self.end_frame))
                    break
            elif 'CAN' in cols[2]:      # 旧can source数据格式
                msg_type = cols[2]
                if int(cols[3], 16) == 0xc7 and rtk_dec:
                    continue
                if len(cols[4]) > 2:
                    data = bytes().fromhex(cols[4])
                else:
                    data = b''.join([int(x, 16).to_bytes(1, 'little') for x in cols[4:]])
                decode_msg = {
                    "type": "can",
                    "index": self.can_types[msg_type]['index'],
                    "data": data,
                    "parsers": self.can_types[msg_type]['parsers'],
                    "cid": int(cols[3], 16),
                    "ts": ts
                }
                data = can_decode(decode_msg)
                if data:
                    self.put_sink(data)
            elif 'can' in cols[2]:      # 新can source数据格式
                if not self.can_types.get(cols[2]):     # 判断是否需要解析
                    continue

                info_list = cols[2].split('.')
                index = info_list[1]
                dbc = info_list[3]
                data = bytes().fromhex(cols[4])

                decode_msg = {
                    "type": "can",
                    "index": index,
                    "parsers": self.can_types[cols[2]]['parsers'],
                    "source": '{}.{}-{}'.format(dbc, index, info_list[2].replace('can', '')),
                    "data": data,
                    "cid": int(cols[3], 16),
                    "ts": ts
                }
                data = can_decode(decode_msg)
                if data:
                    self.put_sink(data)
            elif 'rtk' in cols[2] and 'sol' in cols[2]:  # old d-rtk
                rtk_dec = True
                source = '.'.join(cols[2].split('.')[0:2])
                r = {'type': 'rtk', 'source': source, 'ts': ts, 'ts_origin': ts}
                r['rtkst'], r['orist'], r['lat'], r['lon'], r['hgt'], r['velN'], r['velE'], \
                r['velD'], r['yaw'], r['pitch'], r['length'] = (float(x) for x in cols[3:14])
                r['rtkst'] = int(r['rtkst'])
                r['orist'] = int(r['orist'])

                if r['orist'] > 34:
                    vehstate = {'type': 'vehicle_state', 'pitch': r['pitch'], 'yaw': r['yaw'], 'ts': ts}
                else:
                    vehstate = None
                self.put_sink((0xc7, [r, vehstate], source))

            # 定位打点
            elif 'pinpoint' in cols[2]:
                kw = cols[2].split('.')[-1]
                source = '.'.join(cols[2].split('.')[0:2])
                if kw in ub482_defs:
                    r = decode_with_def(ub482_defs, line)
                    if not r:
                        continue
                    r['ts'] = ts
                    r['type'] = kw
                    r['source'] = '.'.join(cols[2].split('.')[:2])
                    self.put_sink((0xc7, r, source))

            elif 'NMEA' in cols[2] or 'gps' in cols[2]:
                r = ublox.decode_nmea(cols[3])
                r['source'] = cols[2]
                self.put_sink((0x00, r, cols[2]))
            elif 'inspva' in cols[2]:
                try:
                    r = parse_novatel(None, cols[3], None)
                    r['source'] = '.'.join(cols[2].split('.')[0:2])
                    self.put_sink((0x00, r, r['source']))
                except Exception as e:
                    raise e
            elif 'pim222' in cols[2]:
                decode_msg = {
                    "type": "pim222",
                    "source": cols[2],
                    "data": cols[3],
                }
                data = pim222_decode(decode_msg)
                if data:
                    self.put_sink(data)

            elif 'q4_100' in cols[2]:
                if cols[2] not in self.bin_rf:
                    dir_path = os.path.join(os.path.dirname(self.log_path), cols[2])
                    if os.path.exists(os.path.join(dir_path, cols[2] + ".bin")):
                        self.bin_rf[cols[2]] = open(os.path.join(dir_path, cols[2] + ".bin"), "rb")
                    elif os.path.exists(os.path.join(dir_path, cols[2].split(".")[0] + ".bin")):
                        self.bin_rf[cols[2]] = open(os.path.join(dir_path, cols[2].split(".")[0] + ".bin"), "rb")
                    else:
                        continue

                sz = int(cols[3])
                buf_string = self.bin_rf[cols[2]].read(sz)

                decode_msg = {
                    "type": "q4_100",
                    "protocol": "q4_100",
                    "source": cols[2],
                    "data": buf_string,
                    "ts": ts
                }
                data = q4_decode(decode_msg)
                if data:
                    self.put_sink(data)

        logger.debug(bcl.OKBL + 'log.txt reached the end.' + bcl.ENDC)
        logger.info("take time: {}".format(time.time() - start_time))
        while not self.mq.empty():
            time.sleep(0.1)

        rf.close()
        return

    def pop_common(self):
        return self.mq.get(block=False)


def prep_replay(source, ns=False, chmain=None):
    """
    回放预处理，加载、修改配置文件
    :param source:
    :param ns:
    :param chmain:
    :return:
    """
    r_sort = os.path.join(os.path.dirname(source), 'log_sort.txt')

    if not os.path.exists(r_sort):
        # 是否进行排序整理
        if ns:
            r_sort = source
        else:
            r_sort = mytools.sort_big_file(source)

    # 加载配置文件
    config_path = os.path.join(os.path.dirname(source), 'config.json')
    install_path = os.path.join(os.path.dirname(source), 'installation.json')
    uniconf = CVECfg()
    if os.path.exists(config_path):
        logger.debug("using configs: {}".format(config_path))
        uniconf.configs = load_config(config_path)
    if os.path.exists(install_path):
        logger.debug("using installation: {}".format(install_path))
        uniconf.installs = load_installation(install_path)

    # 是否修改主设备
    if chmain:
        if chmain in uniconf.installs:
            uniconf.installs['video'] = uniconf.installs[chmain]
        else:
            logger.error("no {} installation".format(chmain))

    return r_sort, uniconf


def start_replay(source_path, args):
    logger.warning("main pid:{}, log path:{}".format(os.getpid(), source_path))

    # 初始化保存路径
    save_dir = None
    if args.render:
        if args.output and os.path.exists(args.output):
            save_dir = args.output
        else:
            save_dir = os.path.dirname(source_path)

    # 加载配置
    ns = args.nosort
    chmain = args.chmain
    r_sort, cfg = prep_replay(source_path, ns=ns, chmain=chmain)

    replay_hub = LogPlayer(r_sort, cfg, start_frame=args.start_frame, end_frame=args.end_frame,
                         start_time=args.start_time, end_time=args.end_time, loop=args.loop,
                         real_interval=args.real_interval, chmain=chmain)

    replay_hub.daemon = True

    if args.web:
        from video_server import PccServer
        server = PccServer()
        server.start()
        pcc = PCC(replay_hub, replay=True, rlog=r_sort, ipm=True, ipm_bg=args.show_ipm_bg, save_replay_video=save_dir, uniconf=cfg, to_web=server)
        replay_hub.start()
        pcc.start()
        while True:
            time.sleep(1)
    else:
        pcc = PCC(replay_hub, replay=True, rlog=r_sort, ipm=True, ipm_bg=args.show_ipm_bg, save_replay_video=save_dir, uniconf=cfg, eclient=args.eclient)
        replay_hub.start()

        # 控制子进程的退出
        global sub_processes
        sub_processes.append(replay_hub)
        signal.signal(signal.SIGTERM, term)

        pcc.start()
        replay_hub.join()
        print("replay_hub end join")
        pcc.control(ord('q'))
    sub_processes = []


if __name__ == "__main__":
    # 初始化命令行方法
    parser = argparse.ArgumentParser(description="Replay CVE log.")
    parser.add_argument('path', nargs='+', help="包含log.txt的路径，支持多个路径")
    parser.add_argument('-o', '--output', default=False)
    parser.add_argument('-r', '--render', action='store_true', help="是否保存回放渲染视频")
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
    parser.add_argument('-e', '--eclient', action="store_true")
    parser.add_argument('-d', '--debug', action="store_true", help="调试模式，可看调试信息")
    parser.add_argument('-chmain', default=None, help="change main video")
    args = parser.parse_args()

    # 提供冻结以产生 Windows 可执行文件的支持
    freeze_support()

    # 初始化信息输出等级
    if args.debug:
        logger.setLevel(level=logging.DEBUG)

    # 遍历寻找log.txt文件路径
    log_path_list = []
    for path in args.path:
        if not os.path.exists(path):
            continue
        log_path_list += log_list_from_path(path)

    if not log_path_list:
        logger.error("未识别到log路径")

    logger.debug("待回放的log路径：{}".format(log_path_list))
    try:
        for path in log_path_list:
            start_replay(path, args)
    except Exception as e:
        logger.exception(e)
