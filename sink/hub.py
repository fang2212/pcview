from multiprocessing.dummy import Process as Thread
from multiprocessing import Queue
from sink.pcc_sink import PinodeSink, CANSink, CameraSink, GsensorSink, X1CameraSink
from recorder.FileHandler import FileHandler
from config.config import configs, bcl, local_cfg
import time
from net.discover import CollectorFinder
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')  # logging.basicConfig函数对日志的输出格式及方式做相关配置


class Hub(Thread):

    def __init__(self, headless=False):

        # msg_types = config.msg_types

        Thread.__init__(self)
        self.headless = headless

        self.msg_queue = Queue()
        self.cam_queue = Queue()
        # self.sink = {}
        self.cache = {}
        self.time_aligned = True
        self.msg_cnt = {}
        self.last_res = {}
        self.collectors = {}

        self.finder = CollectorFinder()
        self.finder.start()
        # for i in range(3):
        #     # try:
        #     self.finder.request()
        #     # except Exception as e:
        #     #     pass
        #     time.sleep(0.2)
        self.finder.request()
        time.sleep(0.6)

        if local_cfg.save.log or local_cfg.save.alert or local_cfg.save.video:
            self.fileHandler = FileHandler()
            self.fileHandler.start()
            # self.fileHandler.start_rec()

        if len(self.finder.found) > 0:
            ts0 = self.finder.found[list(self.finder.found.keys())[0]]['ts']
        else:
            print('no devices...')

        x1_camera_flag = False
        if 'use_x1_camera' in configs[0] and configs[0]['use_x1_camera']['use']:
            ip = configs[0]['use_x1_camera']['ip']
            port = configs[0]['use_x1_camera']['port']
            self.camera_sink = X1CameraSink(msg_queue=self.msg_queue, cam_queue=self.cam_queue, ip=ip, port=port,
                                            channel='camera',
                                            fileHandler=self.fileHandler)
            self.camera_sink.start()
            x1_camera_flag = True
            print('use x1 algorithm camera')

        # self.collectors[ip]['sinks']['video'] = self.camera_sink

        print('Devices found:')
        # for dev in self.finder.found:
        #     print(dev, self.finder.found[dev])

        for dev in self.finder.found:
            print(bcl.OKGR+dev+bcl.ENDC, self.finder.found[dev])
            self.collectors[dev] = self.finder.found[dev]
            if self.finder.found[dev]['ts'] - ts0 > 1.0 or self.finder.found[dev]['ts'] - ts0 < -1.0:
                self.time_aligned = False

        print('Connecting to device(s)...')
        # print('collector0 on {}, types:'.format(config.ip), config.msg_types)
        # print('collector1 on {}, types:'.format(config2.ip), config2.msg_types)

        for ip in self.finder.found:
            self.collectors[ip]['sinks'] = {}
            if self.finder.found[ip]['mac'] == configs[0]['mac']:
                if not x1_camera_flag:
                    self.camera_sink = CameraSink(queue=self.cam_queue, ip=ip, port=1200, channel='camera',
                                                  fileHandler=self.fileHandler)
                    self.camera_sink.start()
                    self.collectors[ip]['sinks']['video'] = self.camera_sink

                    print('use x1 collector camera')

            ndev = 0

            print('hub configs', len(configs))
            for idx, c in enumerate(configs):
                if c['mac'] == self.finder.found[ip]['mac']:
                    if self.finder.found[ip].get('type') == 'pi_node':
                        for name in self.finder.found[ip]['ports']:
                            port = self.finder.found[ip]['ports'][name]
                            self.collectors[ip]['idx'] = idx
                            pisink = PinodeSink(self.msg_queue, ip, port, channel='can', index=idx, resname=name,
                                                fileHandler=self.fileHandler, isheadless=self.headless)
                            pisink.start()
                            self.collectors[ip]['sinks'][name] = pisink
                    else:
                        self.collectors[ip]['idx'] = idx
                        self.collectors[ip]['sinks'].update(self.fpga_handle(c, self.msg_queue, ip, index=idx))
                    ndev += 1
                    print('Connected dev {} on {}, types:'.format(idx, ip), configs[0]['msg_types'])

        msg_types = []
        for ip in self.collectors:
            # print(ip, collectors[ip]['sinks'])
            for port in self.collectors[ip]['sinks']:
                if 'can' in port:
                    itype = configs[self.collectors[ip]['idx']]['can_types'][port]
                    msg_types.append(itype[0] + '.{}'.format(self.collectors[ip]['idx']))

        print(msg_types)

        self.msg_types = msg_types

        self.max_cache = 40

        for msg_type in ['can', 'gsensor', 'rtk', 'x1_data']:
            self.cache[msg_type] = []
            self.msg_cnt[msg_type] = {
                'rev': 0,
                'show': 0,
                'fix': 0,
            }
        self.msg_cnt['frame'] = 0
        print('hub init done')
    
    def find_collectors(self):
        self.finder.request()

        if len(self.finder.found) > 0:
            ts0 = self.finder.found[list(self.finder.found.keys())[0]]['ts']
        else:
            # print('no devices...')
            pass

        # x1_camera_flag = False
        # if 'use_x1_camera' in configs[0] and configs[0]['use_x1_camera']['use']:
        #     ip = configs[0]['use_x1_camera']['ip']
        #     port = configs[0]['use_x1_camera']['port']
        #     self.camera_sink = X1CameraSink(msg_queue=self.msg_queue, cam_queue=self.cam_queue, ip=ip, port=port,
        #                                     channel='camera',
        #                                     fileHandler=self.fileHandler)
        #     self.camera_sink.start()
        #     x1_camera_flag = True
        #     print('use x1 algorithm camera')

        # self.collectors[ip]['sinks']['video'] = self.camera_sink

        # print('Devices found:')
        # for dev in self.finder.found:
        #     print(dev, self.finder.found[dev])

        for ip in self.finder.found:
            if ip in self.collectors:
                continue
            # print(bcl.OKGR+ip+bcl.ENDC, self.finder.found[ip])
            self.collectors[ip] = self.finder.found[ip]
            self.collectors[ip]['sinks'] = {}
            if self.finder.found[ip]['mac'] == configs[0]['mac']:
                # if not x1_camera_flag:
                self.camera_sink = CameraSink(queue=self.cam_queue, ip=ip, port=1200, channel='camera',
                                              fileHandler=self.fileHandler)
                self.camera_sink.start()
                self.collectors[ip]['sinks']['video'] = self.camera_sink

                print('use x1 collector camera')

            ndev = 0

            print('hub configs', len(configs))
            for idx, c in enumerate(configs):
                if c['mac'] == self.finder.found[ip]['mac']:
                    if self.finder.found[ip].get('type') == 'pi_node':
                        for name in self.finder.found[ip]['ports']:
                            port = self.finder.found[ip]['ports'][name]
                            self.collectors[ip]['idx'] = idx
                            pisink = PinodeSink(self.msg_queue, ip, port, channel='can', index=idx, resname=name,
                                                fileHandler=self.fileHandler, isheadless=self.headless)
                            pisink.start()
                            self.collectors[ip]['sinks'][name] = pisink
                    else:
                        self.collectors[ip]['idx'] = idx
                        self.collectors[ip]['sinks'].update(self.fpga_handle(c, self.msg_queue, ip, index=idx))
                    ndev += 1
                    print('Connected dev {} on {}, types:'.format(idx, ip), configs[0]['msg_types'])

        return {'status': 'ok', 'info': 'oj8k'}
        # print('Connecting to device(s)...')
        # print('collector0 on {}, types:'.format(config.ip), config.msg_types)
        # print('collector1 on {}, types:'.format(config2.ip), config2.msg_types)

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


