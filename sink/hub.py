import logging
import time
from multiprocessing import Queue
from multiprocessing.dummy import Process as Thread

from config.config import configs, bcl, local_cfg
from net.discover import CollectorFinder
from recorder.FileHandler import FileHandler
from sink.pcc_sink import PinodeSink, CANSink, CameraSink, GsensorSink, FlowSink

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')  # logging.basicConfig函数对日志的输出格式及方式做相关配置


class Hub(Thread):

    def __init__(self, headless=False, direct_cfg=None):

        # msg_types = config.msg_types

        Thread.__init__(self)
        self.headless = headless
        # print(self.headless)
        self.msg_queue = Queue()
        self.cam_queue = Queue()
        # self.sink = {}
        self.cache = {}
        self.time_aligned = True
        self.msg_cnt = {}
        self.last_res = {}
        # self.collectors = {}

        self.finder = CollectorFinder()
        self.finder.start()

        x1_camera_flag = False
        self.max_cache = 40
        self.msg_cnt['frame'] = 0
        self.msg_types = []

        for msg_type in ['can', 'gsensor', 'rtk', 'x1_data', 'video_aux']:
            self.cache[msg_type] = []
            self.msg_cnt[msg_type] = {
                'rev': 0,
                'show': 0,
                'fix': 0,
            }
        # for i in range(3):
        #     # try:
        #     self.finder.request()
        #     # except Exception as e:
        #     #     pass
        #     time.sleep(0.2)

        self.direct_cfg = direct_cfg
        if local_cfg.save.log or local_cfg.save.alert or local_cfg.save.video:
            self.fileHandler = FileHandler()
            self.fileHandler.start()
            # self.fileHandler.start_rec()

        if direct_cfg is not None:
            import json
            cfg = json.load(open(direct_cfg))
            ip = cfg['ip']
            mac = cfg['mac']
            # self.collectors[ip] = {'mac': mac}
            # self.collectors[ip]['sinks'] = {}
            print('initializing direct connect to {} {}'.format(ip, mac))
            sink = CameraSink(queue=self.cam_queue, ip=ip, port=1200, channel='camera', index=0,
                              fileHandler=self.fileHandler)
            sink.start()
            # self.collectors[ip]['sinks']['video'] = sink
            # self.collectors[ip]['idx'] = 0
            # self.collectors[ip]['sinks'].update(self.fpga_handle(cfg, self.msg_queue, ip, index=0))
            self.msg_types = []
            self.msg_types.append(cfg['can_types']['can0'][0] + '.0')
            self.msg_types.append(cfg['can_types']['can1'][0] + '.0')

            print(self.msg_types)
            return

        self.finder.request()
        time.sleep(0.6)
        self.finder.request()
        time.sleep(0.6)
        self.finder.request()
        time.sleep(0.6)
        if len(self.finder.found) > 0:
            ts0 = self.finder.found[list(self.finder.found.keys())[0]]['ts']
            for ip in self.finder.found:
                print("found:", ip, self.finder.found[ip]['mac'])
        else:
            print('no devices...')
        self.online = self.init_collectors()

        print(bcl.OKGR + '---------------- collectors online ---------------' + bcl.ENDC)
        for ip in self.online:
            ol = self.online[ip]
            print('index {}'.format(ol['idx']), bcl.OKBL + ip + bcl.ENDC, ol.get('mac'))
            print('definition:', ol['defs_path'])
            for iface in ol['ports']:
                print('--', iface, ol['ports'][iface]['topic'] + '.{}'.format(ol['idx']),
                      'enabled' if ol['ports'][iface]['enable'] else bcl.FAIL+'disabled'+bcl.ENDC)
        print(bcl.OKGR + '---------------- ----------------- ---------------' + bcl.ENDC)

        print('hub init done')

    def get_veh_role(self, source):
        for ip in self.online:
            for data_type in self.online[ip]['msg_types']:
                if data_type == source:
                    role = self.online[ip].get('veh_tag') or 'default'
                    return role

    def init_collectors(self):
        cfgs_online = {}
        for idx, cfg in enumerate(configs):  # match cfg and finder results
            if cfg.get('type') == 'x1_algo':
                cfg['idx'] = idx
                ip = cfg['ip']
                cfgs_online[ip] = cfg
                # self.collectors[ip] = self.finder.found[ip]
                continue
            for ip in self.finder.found:
                if cfg.get('mac') == self.finder.found[ip]['mac']:
                    cfg['ip'] = ip
                    cfg['idx'] = idx
                    cfgs_online[ip] = cfg
                    # self.collectors[ip] = self.finder.found[ip]
                    break

        for ip in cfgs_online:  # initialize online collectors
            cfg = cfgs_online[ip]
            ip = cfg['ip']
            idx = cfg['idx']
            # self.collectors[ip]['idx'] = idx
            # self.collectors[ip]['sinks'] = {}
            cfgs_online[ip]['msg_types'] = []
            if cfg.get('type') == 'x1_algo':
                for item in cfg['ports']:
                    if not cfg['ports'][item].get('enable'):
                        continue
                    port = cfg['ports'][item]['port']
                    sink = FlowSink(msg_queue=self.msg_queue, cam_queue=self.cam_queue, ip=ip, port=port, channel=item,
                                    index=idx, fileHandler=self.fileHandler, is_main=cfg.get('is_main'))
                    sink.start()
                    # self.collectors[ip]['sinks'][item] = sink
                    cfgs_online[ip]['msg_types'].append(item + '.{}'.format(idx))

            elif cfg.get('type') == 'pi_node':
                for name in self.finder.found[ip]['ports']:
                    if not cfg['ports'][name].get('enable'):
                        continue
                    port = self.finder.found[ip]['ports'][name]
                    pisink = PinodeSink(self.msg_queue, ip, port, channel='can', index=idx, resname=name,
                                        fileHandler=self.fileHandler, isheadless=self.headless)
                    pisink.start()
                    cfgs_online[ip]['msg_types'].append(name + '.{}'.format(idx))
                    # self.collectors[ip]['sinks'][name] = pisink
            elif cfg.get('type') == 'x1_collector':
                sink = {}
                for iface in cfg['ports']:
                    if not cfg['ports'][iface].get('enable'):
                        continue
                    if 'can' in iface:
                        chn = cfg['ports'][iface]
                        cansink = CANSink(self.msg_queue, ip=ip, port=chn['port'], channel=iface, type=[chn['topic']],
                                              index=idx, fileHandler=self.fileHandler, isheadless=self.headless)

                        cansink.start()
                        cfgs_online[ip]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                        # self.collectors[ip]['sinks'].update(sink)
                        # self.msg_types.append(chn['topic'] + '.' + str(idx))
                        # print(chn['topic'])
                    elif 'gsensor' in iface:
                        chn = cfg['ports'][iface]
                        gsink = GsensorSink(queue=self.msg_queue, ip=ip, port=chn['port'], channel=iface, index=idx,
                                                      fileHandler=self.fileHandler, isheadless=self.headless)
                        gsink.start()
                        cfgs_online[ip]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                    elif 'video' in iface:
                        port = cfg['ports']['video']['port']
                        vsink = CameraSink(queue=self.cam_queue, ip=ip, port=port, channel='camera', index=idx,
                                          fileHandler=self.fileHandler, is_main=cfg.get('is_main'))
                        vsink.start()
                # if cfg.get('is_main'):
                #     port = cfg['ports']['video']['port']
                #     sink = CameraSink(queue=self.cam_queue, ip=ip, port=port, channel='camera', index=idx,
                #                       fileHandler=self.fileHandler)
                #     sink.start()
                    # self.collectors[ip]['sinks']['video'] = sink
            else:  # no type, default is x1 collector
                # self.collectors[ip]['idx'] = idx
                self.fpga_handle(cfg, self.msg_queue, ip, index=idx)
                cfgs_online[ip]['msg_types'].append(cfg['can_types']['can0'][0] + '.{}'.format(idx))
                cfgs_online[ip]['msg_types'].append(cfg['can_types']['can1'][0] + '.{}'.format(idx))
                cfgs_online[ip]['msg_types'].append('gsensor.{}'.format(idx))
                if cfg.get('is_main'):
                    sink = CameraSink(queue=self.cam_queue, ip=ip, port=1200, channel='camera', index=idx,
                                      fileHandler=self.fileHandler, is_main=True)
                    sink.start()
                    # self.collectors[ip]['sinks']['video'] = sink
        return cfgs_online

    def fpga_handle(self, cfg, msg_queue, ip, index=0):
        print('fpga handle:', index, cfg)
        sink = {}

        if 'can0' in cfg['msg_types'] and len(cfg['can_types']['can0']) != 0:
            # typestr = 'can' + '{:01d}'.format(index * 2)

            types = cfg['can_types']['can0']
            sink['can0'] = CANSink(queue=msg_queue, ip=ip, port=1207, channel='can0', type=types,
                                   index=index, fileHandler=self.fileHandler, isheadless=self.headless)
            sink['can0'].start()

        if 'can1' in cfg['msg_types'] and len(cfg['can_types']['can1']) != 0:
            # typestr = 'can' + '{:01d}'.format(index * 2 + 1)

            types = cfg['can_types']['can1']
            sink['can1'] = CANSink(queue=msg_queue, ip=ip, port=1208, channel='can1', type=types,
                                   index=index, fileHandler=self.fileHandler, isheadless=self.headless)
            sink['can1'].start()

        if 'gsensor' in cfg['msg_types']:
            sink['gsensor'] = GsensorSink(queue=msg_queue, ip=ip, port=1209, channel='gsensor', index=index,
                                          fileHandler=self.fileHandler, isheadless=self.headless)
            sink['gsensor'].start()

        return sink

    def pop_simple(self, pause=False):
        res = {}
        if not self.cam_queue.empty():
            frame_id, data, msg_type = self.cam_queue.get()
            # fileHandler.insert_raw((data['ts'], 'camera', '{}'.format(frame_id)))
            is_main = data.get('is_main')
            if not is_main:
                self.cache['video_aux'].append(data)
                # self.msg_cnt['video']['rev'] += 1
                # self.msg_cnt['video']['show'] += 1
                return
            res['ts'] = data['ts']
            res['img'] = data['img']
            res['frame_id'] = frame_id
            # for key in self.last_res:
            #   res[key] = self.last_res[key]
            for key in self.cache:
                # print(key, len(self.cache[key]))
                if len(self.cache[key]) > 0:
                    # self.last_res[key] = self.cache[key]
                    res[key] = self.cache[key]
                self.cache[key] = []
            self.msg_cnt['frame'] += 1
            return res
        if not self.msg_queue.empty():
            id, msg_data, channel = self.msg_queue.get()
            if isinstance(msg_data, list):
                # print('msg data list')
                self.cache[channel].extend(msg_data)
            elif isinstance(msg_data, dict):
                self.cache[channel].append(msg_data)
            self.msg_cnt[channel]['rev'] += 1
            self.msg_cnt[channel]['show'] += 1
