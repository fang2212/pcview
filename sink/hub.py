import os
import sys
import time
from multiprocessing import Process, Lock
from multiprocessing import Queue
from multiprocessing import Event
from threading import Thread

from config.config import bcl
from net.discover import CollectorFinder
from recorder.FileHandler import FileHandler
# from sink.pcc_sink_async import *
from sink.mmap_queue import MMAPQueue
from sink.pcc_sink import *
from config.config import get_cached_macs, save_macs

import mmap

from concurrent.futures import ThreadPoolExecutor
import asyncio


class CollectorNode(Process):
    """
    采集器进程，里面包含多个采集线程
    """
    def __init__(self, sinks):
        super(CollectorNode, self).__init__()
        self.sinks = sinks
        self.exit = Event()

    def run(self):
        logger.debug('Inited collector node, pid:{}'.format(os.getpid()))
        # 开始采集线程
        for sink in self.sinks:
            sink.start()

        # 线程守护
        while not self.exit.is_set():
            time.sleep(0.2)

        # 关闭采集线程
        for sink in self.sinks:
            sink.close()
        logger.warning('sink node exit, pid: {}'.format(os.getpid()))

    def add(self, sink):
        self.sinks.append(sink)

    def close(self):
        self.exit.set()


class Hub(Thread):
    """
    信号接受进程
    """
    def __init__(self, uniconf=None, decode_queue=None, result_queue=None):
        Thread.__init__(self)
        self.exit = False
        self.setName('hub_thread')
        self.msg_queue = Queue(maxsize=3000)
        self.mq = MMAPQueue(1024 * 1024 * 500)
        self.msg_list = []
        self.cache = {}
        self.time_aligned = True
        self.last_res = {}
        self.uniconf = uniconf
        self.configs = uniconf.configs
        self.dev_find = False

        self.cache = {}
        self.msg_cnt = {}

        self.msg_types = []
        self.type_roles = dict()
        self.sinks = []

        self.nodes = []
        self.nodes_num = 4

        self.network = self.uniconf.runtime['modules'].get('network') or '192.168.98.0/24'
        self.finder = CollectorFinder(self.network)
        self.mac_ip = None
        self.online = {}

        self.fileHandler = None

        self.init_env()

    def init_env(self):
        """
        初始化运行环境
        :return:
        """
        # 初始化缓存数据字段
        for msg_type in ['frame', 'can', 'gsensor', 'rtk', 'x1_data', 'video_aux']:
            self.cache[msg_type] = []
            self.msg_cnt[msg_type] = {
                'recv': 0,
                'ts': 0,
                'fix': 0,
            }

        # 初始化采集进程
        for i in range(self.nodes_num):
            self.nodes.append(CollectorNode([]))

        # 初始化日志文件对象
        local_cfg = self.uniconf.local_cfg
        if local_cfg.save.log or local_cfg.save.alert or local_cfg.save.video:
            self.fileHandler = FileHandler(uniconf=self.uniconf)

        # 初始化在线设备
        self.finder.start()
        self.finder.take_request()
        time.sleep(0.6)

        cached_macs = get_cached_macs(self.uniconf.name, timeout=60 * 60 * 24)
        if cached_macs:
            print('---- using cached mac table ----')
            self.finder.load_cached_macs(cached_macs)
            for mac in cached_macs:
                print(mac, cached_macs[mac])
            print('--------------------------------')
        else:
            print('scanning for LAN devices...')
            mac_ip = self.finder.get_macs()
            for mac in mac_ip:
                print(mac, mac_ip[mac])
            save_macs(self.uniconf.name, mac_ip)
            print('--------------------------------')

        if len(self.finder.found) > 0:
            for ip in self.finder.found:
                print("found:", ip, self.finder.found[ip]['mac'])
        else:
            print('no devices...')
        self.init_collectors()

        print(bcl.OKGR + '---------------- collectors online ---------------' + bcl.ENDC)
        for ip_type in self.online:
            ol = self.online[ip_type]
            print('index {}'.format(ol['idx']), bcl.OKBL + ip_type + bcl.ENDC, ol.get('mac'))
            print('definition:', ol['defs_path'])
            for iface in ol['ports']:
                topic = ol['ports'][iface].get('dbc', ol['ports'][iface].get('topic'))
                print('--', iface, topic + '.{}'.format(ol['idx']), ol['ports'][iface].get('port') or ol.get("port"),
                      'enabled' if ol['ports'][iface]['enable'] else bcl.FAIL + 'disabled' + bcl.ENDC)
        print(bcl.OKGR + '---------------- ----------------- ---------------' + bcl.ENDC)

        print('hub init done')

    def run(self):
        logger.warning('{} pid:{}'.format("HUB".ljust(20), os.getpid()))
        while not self.exit:
            self.finder.take_request()
            for ip in self.finder.found:
                mac = self.finder.found[ip]['mac']
                for cfg in self.configs:
                    if cfg.get('mac', '').lower() == mac.lower():
                        ip_type = "{}@{}".format(ip, cfg['type'])
                        if ip_type not in self.online:
                            self.init_collector(cfg)
            time.sleep(3)
        logger.warning('{} pid:{}'.format("HUB exit".ljust(20), os.getpid()))

    def close(self):
        self.finder.close()
        self.fileHandler.close()

        for node in self.nodes:
            node.close()
        self.exit = True

    def get_veh_role(self, source):
        if source in self.type_roles:
            return self.type_roles[source]
        for ip_type in self.online:
            for data_type in self.online[ip_type]['msg_types']:
                if data_type == source:
                    role = self.online[ip_type].get('veh_tag') or 'default'
                    self.type_roles[source] = role
                    return role

    def init_collector(self, cfg):
        """
        初始化采集进程
        :param cfg:
        :return:
        """
        ip = cfg['ip']
        idx = cfg['idx']
        is_main = cfg.get('is_main')
        ip_type = "{}@{}".format(ip, cfg['type'])
        if self.online.get(ip_type) is None:
            self.online[ip_type] = {}
        self.online[ip_type]['msg_types'] = []

        if 'type' not in cfg:
            return

        if "algo" in cfg.get('type'):
            for item in cfg['ports']:
                if not cfg['ports'][item].get('enable') and not is_main:
                    continue
                port = cfg['ports'][item]['port']
                topic = cfg['ports'][item].get('topic')
                transport = cfg['ports'][item].get('transport')

                if transport == "libflow":
                    sink = FlowSink(ip=ip, port=port, msg_type=item, index=idx, fileHandler=self.fileHandler,
                                    name=cfg.get("type"), log_name=item, topic=topic, is_main=is_main, mq=self.mq)
                elif transport == "protoflow":
                    sink = ProtoSink(ip=ip, port=port, msg_type=item, index=idx, fileHandler=self.fileHandler,
                                     name=cfg.get("type"), topic=topic, log_name=item, mq=self.mq)
                else:
                    return
                self.sinks.append(sink)
                self.online[ip_type]['msg_types'].append(item + '.{}'.format(idx))

        elif cfg.get('type') == 'pi_node':
            for name in cfg['ports']:
                if not cfg['ports'][name].get('enable'):
                    continue
                port = cfg['ports'][name]['port']
                pisink = PinodeSink(ip, port, msg_type=name, index=idx, resname=name,
                                    fileHandler=self.fileHandler, mq=self.mq)
                self.sinks.append(pisink)
                self.online[ip_type]['msg_types'].append(name + '.{}'.format(idx))
        elif "can_collector" in cfg.get("type"):
            can_list = {}
            transport = cfg.get('transport')
            for iface in cfg['ports']:
                if cfg["ports"][iface].get("transport"):
                    transport = cfg["ports"][iface].get("transport")
                if "can" in iface:
                    can_list[iface] = cfg["ports"][iface]

            if transport == "nanomsg":
                can_collector = CANCollectSink(ip=ip, port=cfg.get("port"), index=idx, can_list=can_list,
                                               device=cfg.get("origin_device"),
                                               fileHandler=self.fileHandler, mq=self.mq)
                self.sinks.append(can_collector)
                self.online[ip_type]['msg_types'].extend([can_list[ch]["dbc"] + '.{}'.format(idx) for ch in can_list])
            elif transport == "mqtt":
                device = cfg.get('origin_device', cfg['name'])
                can_collector = MQTTSink(ip=ip, can_list=can_list, index=idx, fileHandler=self.fileHandler, device=device, cid=cfg.get("cid"), mq=self.mq)
                self.sinks.append(can_collector)
                self.online[ip_type]['msg_types'].extend([can_list[ch]["dbc"] + '.{}'.format(idx) for ch in can_list])
        elif "collector" in cfg.get('type'):
            for iface in cfg['ports']:
                if not cfg['ports'][iface].get('enable') and not is_main:
                    continue
                if 'can' in iface:
                    chn = cfg['ports'][iface]
                    cansink = CANSink(ip=ip, port=chn['port'], msg_type=iface, type=[chn['topic']],
                                      fileHandler=self.fileHandler,
                                      index=idx, mq=self.mq)

                    self.sinks.append(cansink)
                    self.online[ip_type]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'gsensor' in iface:
                    chn = cfg['ports'][iface]
                    gsink = GsensorSink(ip=ip, port=chn['port'], msg_type=iface, index=idx,
                                        fileHandler=self.fileHandler, mq=self.mq)
                    self.sinks.append(gsink)
                    self.online[ip_type]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'video' in iface:
                    port = cfg['ports']['video']['port']
                    vsink = CameraSink(ip=ip, port=port, msg_type='camera', index=idx,
                                       fileHandler=self.fileHandler, is_main=cfg.get('is_main'),
                                       devname=cfg.get('type'), mq=self.mq)
                    self.sinks.append(vsink)

        elif cfg.get('type') == 'general':
            for iface in cfg['ports']:
                if not cfg['ports'][iface].get('enable') and not is_main:
                    continue
                port = cfg['ports'][iface]['port']
                if 'can' in iface:
                    chn = cfg['ports'][iface]
                    cansink = CANSink(ip=ip, port=port, msg_type=iface, type=[chn['topic']],
                                      index=idx, fileHandler=self.fileHandler, mq=self.mq)
                    self.sinks.append(cansink)
                    self.online[ip_type]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'gsensor' in iface:
                    chn = cfg['ports'][iface]
                    gsink = GsensorSink(ip=ip, port=port, msg_type=iface, index=idx,
                                        fileHandler=self.fileHandler, mq=self.mq)
                    self.sinks.append(gsink)
                    self.online[ip_type]['msg_types'].append(chn['topic'] + '.{}'.format(idx))
                elif 'video' in iface:
                    vsink = CameraSink(ip=ip, port=port, msg_type='camera', index=idx,
                                       fileHandler=self.fileHandler, is_main=cfg.get('is_main'),
                                       devname=cfg.get('name'), mq=self.mq)
                    self.sinks.append(vsink)
                elif 'rtk' in iface or 'gps' in iface:
                    pisink = PinodeSink(ip, port, msg_type=iface, index=idx, resname=iface,
                                        fileHandler=self.fileHandler, mq=self.mq)
                    self.sinks.append(pisink)
                    self.online[ip_type]['msg_types'].append(iface + '.{}'.format(idx))
                elif cfg['ports'][iface].get('transport') == 'tcp':
                    proto = cfg['ports'][iface]['protocol']
                    tcpsink = TCPSink(ip, port, cfg['ports'][iface]['topic'], proto, idx, self.fileHandler, mq=self.mq)
                    self.sinks.append(tcpsink)
                    self.online[ip_type]['msg_types'].append(iface + '.{}'.format(idx))
                elif cfg['ports'][iface].get("transport") == 'udp':
                    proto = cfg['ports'][iface]['protocol']
                    udpsink = UDPSink(ip, port, cfg['ports'][iface]['topic'], proto, idx, self.fileHandler, mq=self.mq)
                    self.sinks.append(udpsink)
                    self.online[ip_type]['msg_types'].append(iface + '.{}'.format(idx))
                elif cfg['ports'][iface].get("transport") == 'zmq':
                    zmqSink = ZmqSink(ip, port, cfg['ports'][iface]['topic'], idx, self.fileHandler, mq=self.mq)
                    self.sinks.append(zmqSink)
                    self.online[ip_type]['msg_types'].append(iface + '.{}'.format(idx))

        else:  # no type, default is x1 collector
            pass

    def init_collectors(self):
        self.online = {}
        for idx, cfg in enumerate(self.configs):  # match cfg and finder results
            cfg['idx'] = idx
            if cfg.get('force_ip'):  # force to connect via pre-defined ip
                if 'ip' not in cfg:
                    logger.error('undefined ip addr for ip-force device: {}'.format(cfg))
                    continue
                ip = cfg['ip']
                self.online["{}@{}".format(ip, cfg['type'])] = cfg
                logger.debug('config force ip device: {}'.format(ip))

            for ip in self.finder.found:
                if cfg.get('mac', '').lower() == self.finder.found[ip]['mac'].lower():
                    cfg['ip'] = ip
                    self.online["{}@{}".format(ip, cfg['type'])] = cfg
                    break

        for ip_type in self.online:
            self.init_collector(self.online[ip_type])

        logger.info("sink num:{}".format(len(self.sinks)))
        for i, s in enumerate(self.sinks):
            self.nodes[i % self.nodes_num].add(s)

        for node in self.nodes:
            node.start()

        if self.fileHandler:
            self.fileHandler.start()

        return self.online

    def pop_common(self):
        # res = {}
        return self.mq.get(block=False)

    def parse_can_msgs(self, status):
        for sink in self.sinks:
            if sink.type == 'can_sink':
                if status:
                    sink.parse_event.set()
                else:
                    sink.parse_event.clear()
