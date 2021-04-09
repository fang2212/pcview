import os
import time
from multiprocessing import Process as kProcess
from multiprocessing import Queue as kQueue
from multiprocessing import Event
from threading import Thread

from config.config import bcl
from net.discover import CollectorFinder
from recorder.FileHandler import FileHandler
# from sink.pcc_sink_async import *
from sink.pcc_sink import *
from config.config import get_cached_macs, save_macs

from concurrent.futures import ThreadPoolExecutor
import asyncio


class CollectorNode(kProcess):
    def __init__(self, sinks):
        super(CollectorNode, self).__init__()
        self.sinks = sinks
        self.exit = Event()
        self.q = kQueue()


    def run(self):
        # if async_for_sink:
        #     self.am = AsyncManager()
        #     self.am.start()
        #     while self.am.loop is None: time.sleep(0.01)
        #     self.tep = ThreadPoolExecutor(2)

        print('Inited collector node', os.getpid())
        for sink in self.sinks:
            # if async_for_sink:
            #     if isinstance(sink, TCPSink) or isinstance(sink, RTKSink):
            #         t = self.am.loop.run_in_executor(self.tep, sink.run)
            #         self.am.add_task(asyncio.wait(t))
            #     else:
            #         self.am.add_task(sink.run())
            # else:
            sink.start()

        while not self.exit.is_set():
            if not self.q.empty():
                sink = self.q.get()
                if async_for_sink:
                    self.am.add_task(sink.run())
                else:
                    sink.start()

            else:
                time.sleep(0.1)
            # for sink in self.sinks:
            #     print(sink)
        for sink in self.sinks:
            sink.close()
        print('sink node exit.')

    def add(self, sink):
        self.sinks.append(sink)
        # self.q.put(sink)

    def close(self):
        self.exit.set()


class Hub(Thread):

    def __init__(self, headless=False, direct_cfg=None, uniconf=None):
        # msg_types = config.msg_types

        Thread.__init__(self)
        self.setName('hub_thread')
        self.headless = headless
        # print(self.headless)
        self.msg_queue = kQueue(maxsize=3000)
        # self.cam_queue = kQueue()
        # self.sink = {}
        self.cache = {}
        self.time_aligned = True
        self.msg_cnt = {}
        self.last_res = {}
        self.configs = uniconf.configs
        self.dev_find = False
        # self.collectors = {}

        x1_camera_flag = False
        self.max_cache = 40
        # self.msg_cnt['frame'] = 0
        self.msg_types = []
        self.type_roles = dict()
        self.sinks = []

        self.nodes = [CollectorNode([]), CollectorNode([])]

        self.mac_ip = None
        self.online = {}

        for msg_type in ['frame', 'can', 'gsensor', 'rtk', 'x1_data', 'video_aux']:
            self.cache[msg_type] = []
            self.msg_cnt[msg_type] = {
                'recv': 0,
                'ts': 0,
                'fix': 0,
            }
        local_cfg = uniconf.local_cfg
        self.direct_cfg = direct_cfg
        self.fileHandler = None
        if local_cfg.save.log or local_cfg.save.alert or local_cfg.save.video:
            self.fileHandler = FileHandler(uniconf=uniconf)
            # self.fileHandler.start()
            # self.fileHandler.start_rec()

        if direct_cfg is not None:  # direct mode
            self.online = self.direct_init(direct_cfg)
            return
        # targets = [{'ip':}]
        dev_finder = uniconf.runtime['modules'].get('device_finder')

        if dev_finder and dev_finder['enable'] or uniconf.version < 1.1:
            self.dev_find = True
            self.network = dev_finder.get('network') if dev_finder else '192.168.98.0/24'
            self.finder = CollectorFinder(self.network)
            self.finder.start()
            for dev in self.finder.request():
                pass
            time.sleep(0.6)

            cached_macs = get_cached_macs(uniconf.name, timeout=60 * 60 * 24)
            if not cached_macs:
                print('scanning for LAN devices...')
                mac_ip = self.finder.get_macs()
                # self.mac_ip = get_mac_ip(self.network)
                save_macs(uniconf.name, mac_ip)
                print('--------------------------------')
            else:
                print('---- using cached mac table ----')
                self.finder.load_cached_macs(cached_macs)
                # self.mac_ip = cached_macs
                for mac in cached_macs:
                    print(mac, cached_macs[mac])
                print('--------------------------------')

            if len(self.finder.found) > 0:
                # ts0 = self.finder.found[list(self.finder.found.keys())[0]]['ts']
                for ip in self.finder.found:
                    print("found:", ip, self.finder.found[ip]['mac'])
            else:
                print('no devices...')
        # self.online = self.init_collectors()
        self.init_collectors()

        print(bcl.OKGR + '---------------- collectors online ---------------' + bcl.ENDC)
        for ip in self.online:
            ol = self.online[ip]
            print('index {}'.format(ol['idx']), bcl.OKBL + ip + bcl.ENDC, ol.get('mac'), 'type:', ol['type'])
            print('definition:', ol['defs_path'])
            for iface in ol['ports']:
                print('--', iface, ol['ports'][iface]['topic'] + '.{}'.format(ol['idx']), ol['ports'][iface]['port'],
                      'enabled' if ol['ports'][iface]['enable'] else bcl.FAIL + 'disabled' + bcl.ENDC)
        print(bcl.OKGR + '---------------- ----------------- ---------------' + bcl.ENDC)

        print('hub init done')

    def run(self):
        while True:
            if self.dev_find:
                self.finder.request()
                for ip in self.finder.found:
                    mac = self.finder.found[ip]['mac']
                    for cfg in self.configs:
                        if cfg['mac'] == mac:
                            if ip not in self.online:
                                self.init_collector(cfg)
            time.sleep(5)

    def close(self):
        print('closing finder..')
        if self.dev_find:
            self.finder.close()
        print('closing file handler..')
        self.fileHandler.close()
        print('closing sink node..')
        # self.node.close()

        self.nodes[0].close()
        self.nodes[1].close()

    def get_veh_role(self, source):
        if source in self.type_roles:
            return self.type_roles[source]
        for ip in self.online:
            for data_type in self.online[ip]['msg_types']:
                if data_type == source:
                    role = self.online[ip].get('veh_tag') or 'default'
                    self.type_roles[source] = role
                    return role

    def direct_init(self, direct_cfg):
        import json
        cfg = json.load(open(direct_cfg))
        ip = cfg['ip']
        mac = cfg['mac']
        sinks = []
        cfgs_online = {ip: cfg}
        cfgs_online[ip]['msg_types'] = []
        # self.collectors[ip] = {'mac': mac}
        # self.collectors[ip]['sinks'] = {}
        print('initializing direct connect to {} {}'.format(ip, mac))

        if 'can_type' in cfg:
            sink = CameraSink(queue=self.msg_queue, ip=ip, port=1200, channel='camera', index=0,
                              fileHandler=self.fileHandler, is_main=True)
            sink.start()
            self.fpga_handle(cfg, self.msg_queue, ip)
        elif 'ports' in cfg:
            for iface in cfg['ports']:
                protocol = cfg['ports'][iface].get('protocol')
                transport = cfg['ports'][iface].get('transport')
                port = cfg['ports'][iface]['port']
                topic = cfg['ports'][iface]['topic']
                if not transport:
                    transport = protocol

                if transport == 'nanomsg':
                    if 'video' in iface:
                        sink = CameraSink(queue=self.msg_queue, ip=ip, port=1200, channel='camera', index=0,
                                          fileHandler=self.fileHandler, is_main=True)
                        sink.start()
                        cfgs_online[ip]['msg_types'].append('video.0')
                    if 'can' in iface:
                        chn = cfg['ports'][iface]
                        cansink = CANSink(self.msg_queue, ip=ip, port=chn['port'], channel=iface, type=[chn['topic']],
                                          index=0, fileHandler=self.fileHandler, isheadless=self.headless)

                        cansink.start()
                        cfgs_online[ip]['msg_types'].append('video.0')
                        cfgs_online[ip]['msg_types'].append(chn['topic'] + '.0')
                        # sinks.append(cansink)
                    elif 'gsensor' in iface:
                        chn = cfg['ports'][iface]
                        gsink = GsensorSink(queue=self.msg_queue, ip=ip, port=chn['port'], channel=iface, index=0,
                                            fileHandler=self.fileHandler, isheadless=self.headless)
                        gsink.start()
                        # print('gsensor found')
                        # sinks.append(gsink)
                        cfgs_online[ip]['msg_types'].append('gsensor.0')

                elif transport == 'libflow':
                    sink = FlowSink(msg_queue=self.msg_queue, cam_queue=self.msg_queue, ip=ip, port=port,
                                    channel=iface, topic=topic, index=0, fileHandler=self.fileHandler, is_main=True)
                    # print('inited flow video', sink)
                    sink.start()

        # node = CollectorNode(sinks)
        # node.start()
        # print(cfgs_online)
        return cfgs_online

    def init_collector(self, cfg):
        ip = cfg['ip']
        idx = cfg['idx']
        is_main = cfg.get('is_main')
        self.online[ip]['msg_types'] = []

        if 'type' not in cfg:
            return

        if "algo" in cfg.get('type'):
            for item in cfg['ports']:
                if not cfg['ports'][item].get('enable') and not is_main:
                    continue
                port = cfg['ports'][item]['port']
                proto = cfg['ports'][item].get('protocol')
                topic = cfg['ports'][item].get('topic')

                sink = FlowSink(msg_queue=self.msg_queue, cam_queue=self.msg_queue, ip=ip, port=port, channel=item,
                                index=idx, protocol=proto, topic=topic, log_name=item, fileHandler=self.fileHandler,
                                is_main=is_main, name=cfg.get("type"))
                # sink.start()
                # sink = {'stype': 'flow', 'msg_queue': self.msg_queue, 'cam_queue': self.cam_queue, 'ip': ip,
                #         'port': port, 'channel': item, 'index': idx, 'fileHandler': self.fileHandler,
                #         'is_main': cfg.get('is_main')}
                self.sinks.append(sink)
                self.online[ip]['msg_types'].append(item + '.{}'.format(idx))

        elif cfg.get('type') == 'pi_node':
            for name in cfg['ports']:
                if not cfg['ports'][name].get('enable'):
                    continue
                port = cfg['ports'][name]['port']
                pisink = PinodeSink(self.msg_queue, ip, port, channel='can', index=idx, resname=name,
                                    fileHandler=self.fileHandler, isheadless=self.headless)
                # print('added sink pinode', ip, port, name)
                # pisink.start()
                # pisink = {'stype': 'pi', 'queue': self.msg_queue, 'ip': ip, 'port': port, 'channel': 'can',
                #           'index': idx, 'resname': 'name', 'fileHandler': self.fileHandler,
                #           'isheadless': self.headless}
                self.sinks.append(pisink)
                self.online[ip]['msg_types'].append(name + '.{}'.format(idx))
        elif "collector" in cfg.get('type'):
            for iface in cfg['ports']:
                if not cfg['ports'][iface].get('enable') and not is_main:
                    continue
                if 'can' in iface:
                    chn = cfg['ports'][iface]
                    cansink = CANSink(self.msg_queue, ip=ip, port=chn['port'], channel=iface, type=[chn['topic']],
                                      index=idx, fileHandler=self.fileHandler, isheadless=self.headless)

                    # cansink.start()
                    # cansink = {'stype': 'can', 'queue': self.msg_queue, 'ip': ip, 'port': chn['port'],
                    #            'channel': iface, 'type': [chn['topic']], 'index': idx,
                    #            'fileHandler': self.fileHandler, 'isheadless': self.headless}
                    self.sinks.append(cansink)
                    self.online[ip]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'gsensor' in iface:
                    chn = cfg['ports'][iface]
                    gsink = GsensorSink(queue=self.msg_queue, ip=ip, port=chn['port'], channel=iface, index=idx,
                                        fileHandler=self.fileHandler, isheadless=self.headless)
                    # gsink.start()
                    # gsink = {'stype': 'imu', 'queue': self.msg_queue, 'ip': ip, 'port': chn['port'],
                    #          'channel': iface, 'index': idx, 'fileHandler': self.fileHandler,
                    #          'isheadless': self.headless}
                    self.sinks.append(gsink)
                    self.online[ip]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'video' in iface:
                    port = cfg['ports']['video']['port']
                    vsink = CameraSink(queue=self.msg_queue, ip=ip, port=port, channel='camera', index=idx,
                                       fileHandler=self.fileHandler, is_main=cfg.get('is_main'),
                                       devname=cfg.get('type'))
                    # vsink.start()
                    # vsink = {'stype': 'camera', 'queue': self.cam_queue, 'ip': ip, 'port': port,
                    #          'channel': 'camera', 'index': idx, 'fileHandler': self.fileHandler,
                    #          'is_main': cfg.get('is_main')}
                    self.sinks.append(vsink)

        elif cfg.get('type') == 'general':
            for iface in cfg['ports']:
                if not cfg['ports'][iface].get('enable') and not is_main:
                    continue
                port = cfg['ports'][iface]['port']
                if 'can' in iface:
                    chn = cfg['ports'][iface]
                    cansink = CANSink(self.msg_queue, ip=ip, port=port, channel=iface, type=[chn['topic']],
                                      index=idx, fileHandler=self.fileHandler, isheadless=self.headless)

                    # cansink.start()
                    # cansink = {'stype': 'can', 'queue': self.msg_queue, 'ip': ip, 'port': chn['port'],
                    #            'channel': iface, 'type': [chn['topic']], 'index': idx,
                    #            'fileHandler': self.fileHandler, 'isheadless': self.headless}
                    self.sinks.append(cansink)
                    self.online[ip]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'gsensor' in iface:
                    chn = cfg['ports'][iface]
                    gsink = GsensorSink(queue=self.msg_queue, ip=ip, port=port, channel=iface, index=idx,
                                        fileHandler=self.fileHandler, isheadless=self.headless)
                    # gsink.start()
                    # gsink = {'stype': 'imu', 'queue': self.msg_queue, 'ip': ip, 'port': chn['port'],
                    #          'channel': iface, 'index': idx, 'fileHandler': self.fileHandler,
                    #          'isheadless': self.headless}
                    self.sinks.append(gsink)
                    self.online[ip]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'video' in iface:
                    # port = cfg['ports']['video']['port']
                    vsink = CameraSink(queue=self.msg_queue, ip=ip, port=port, channel='camera', index=idx,
                                       fileHandler=self.fileHandler, is_main=cfg.get('is_main'),
                                       devname=cfg.get('name'))
                    # vsink.start()
                    # vsink = {'stype': 'camera', 'queue': self.cam_queue, 'ip': ip, 'port': port,
                    #          'channel': 'camera', 'index': idx, 'fileHandler': self.fileHandler,
                    #          'is_main': cfg.get('is_main')}
                    self.sinks.append(vsink)
                elif 'rtk' in iface or 'gps' in iface:
                    # port = cfg['ports'][iface]['port']
                    pisink = PinodeSink(self.msg_queue, ip, port, channel='can', index=idx, resname=iface,
                                        fileHandler=self.fileHandler, isheadless=self.headless)
                    # print('added sink pinode', ip, port, iface)
                    # pisink.start()
                    # pisink = {'stype': 'pi', 'queue': self.msg_queue, 'ip': ip, 'port': port, 'channel': 'can',
                    #           'index': idx, 'resname': 'name', 'fileHandler': self.fileHandler,
                    #           'isheadless': self.headless}
                    self.sinks.append(pisink)
                    self.online[ip]['msg_types'].append(iface + '.{}'.format(idx))

                elif cfg['ports'][iface].get('transport') == 'tcp':
                    proto = cfg['ports'][iface]['protocol']
                    tcpsink = TCPSink(self.msg_queue, ip, port, 'can', proto, idx, self.fileHandler)
                    self.sinks.append(tcpsink)
                    self.online[ip]['msg_types'].append(iface + '.{}'.format(idx))
                elif cfg['ports'][iface].get("transport") == 'udp':
                    proto = cfg['ports'][iface]['protocol']
                    udpsink = UDPSink(self.msg_queue, ip, port, cfg['ports'][iface]['topic'], proto, idx, self.fileHandler)
                    self.sinks.append(udpsink)
                    self.online[ip]['msg_types'].append(iface + '.{}'.format(idx))

        else:  # no type, default is x1 collector
            pass
            # self.fpga_handle(cfg, self.msg_queue, ip, index=idx)
            # cfgs_online[ip]['msg_types'].append(cfg['can_types']['can0'][0] + '.{}'.format(idx))
            # cfgs_online[ip]['msg_types'].append(cfg['can_types']['can1'][0] + '.{}'.format(idx))
            # cfgs_online[ip]['msg_types'].append('gsensor.{}'.format(idx))
            # if cfg.get('is_main'):
            #     sink = CameraSink(queue=self.cam_queue, ip=ip, port=1200, channel='camera', index=idx,
            #                       fileHandler=self.fileHandler, is_main=True)
            #     sink.start()
            # sinks.append(sink)
            # self.collectors[ip]['sinks']['video'] = sink

    def init_collectors(self):
        self.online = {}
        for idx, cfg in enumerate(self.configs):  # match cfg and finder results
            mac = cfg.get('mac')
            # print('-------------', cfg)
            if cfg.get('force_ip'):  # force to connect via pre-defined ip
                print('config force ip device.')
                if 'ip' not in cfg:
                    print('undefined ip addr for ip-force device', cfg['mac'])
                    continue
                ip = cfg['ip']
                cfg['idx'] = idx
                self.online[ip] = cfg

            for ip in self.finder.found:
                if cfg.get('mac') == self.finder.found[ip]['mac']:
                    cfg['ip'] = ip
                    cfg['idx'] = idx
                    self.online[ip] = cfg
                    break
        for ip in self.online:
            self.init_collector(self.online[ip])

        for i, s in enumerate(self.sinks):
            self.nodes[i & 1].add(s)

        self.nodes[0].start()
        self.nodes[1].start()

        if self.fileHandler:
            self.fileHandler.start()

        return self.online

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

    def get_statistics(self):
        cnt = 0
        for channel in self.msg_cnt:
            cnt += self.msg_cnt['channel']

    def pop_simple(self, pause=False):
        res = {}
        if not self.cam_queue.empty():
            frame_id, data, source = self.cam_queue.get()
            # print(frame_id, len(data), source)
            # fileHandler.insert_raw((data['ts'], 'camera', '{}'.format(frame_id)))
            is_main = data.get('is_main')
            if not is_main:
                self.cache['video_aux'].append(data)
                # self.msg_cnt['video']['rev'] += 1
                # self.msg_cnt['video']['show'] += 1
                # print('not main video stream')
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
            self.msg_cnt['frame']['recv'] += 1
            self.msg_cnt['frame']['ts'] = time.time()
            return res
        if not self.msg_queue.empty():
            id, msg_data, channel = self.msg_queue.get()
            if isinstance(msg_data, list):
                # print('msg data list')
                self.cache[channel].extend(msg_data)
            elif isinstance(msg_data, dict):
                self.cache[channel].append(msg_data)
            self.msg_cnt[channel]['recv'] += 1
            self.msg_cnt[channel]['ts'] = time.time()

    def pop_common(self):
        # res = {}
        if not self.msg_queue.empty():
            try:
                r = self.msg_queue.get()
                fid, data, source = r

            except ValueError as e:
                print('error when pop data:')
                print(r)
                raise e
            return fid, data, source

    def parse_can_msgs(self, status):
        for sink in self.sinks:
            if sink.type == 'can_sink':
                if status:
                    sink.parse_event.set()
                else:
                    sink.parse_event.clear()
