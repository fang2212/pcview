import asyncio
import base64
import json
import struct
import time

from google.protobuf import json_format

from pyproto import vehicle_pb2, pedestrian_pb2, roadmarking_pb2, object_attribute_pb2, object_pb2
from pyproto import calib_param_pb2, dev_object_pb2, vehicle_signal_pb2
# from multiprocessing import Process
from threading import Thread
# from threading import Event as tEvent
from multiprocessing import Value, Event
import os
import aiohttp
import can
import json
import msgpack
import nnpy
import os
import socket
import struct
import time
import zmq
import paho.mqtt.client as mqtt

from collections import deque
from multiprocessing import Value, Event
from threading import Thread

from parsers import ublox, rtcm3
from parsers.drtk import V1_msg, v1_handlers
from parsers.parser import parsers_dict
from recorder.convert import *
from sink.sink import can_decode, pim222_decode
from tools import mytools
from utils import logger

async_for_sink = False


class bcl:
    HDR = '\033[95m'
    OKBL = '\033[94m'
    OKGR = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Sink(Thread):
    """
    信号解析基本类
    """
    def __init__(self, ip, port, msg_type, index=0, mq=None, sq=None):
        super().__init__()
        self.daemon = True  # 设置为守护线程
        self.ip = ip
        self.port = port
        self.msg_type = msg_type
        self.index = index
        self.source = '{}.{}'.format(self.msg_type, index)
        self.exit = False

        self.mq = mq  # mmap内存对象
        self.sq = sq

        self.pid = None  # 进程id

    def run(self):
        self.pid = os.getpid()
        if isinstance(self.source, list):
            logger.warning('{} pid: {}'.format(','.join(self.source).ljust(20), self.pid))
        else:
            logger.warning('{} pid: {}'.format(self.source.ljust(20), self.pid))
        self.before_task()
        self.task()

    def before_task(self):
        pass

    def task(self):
        pass

    def _init_port(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self.ip, self.port))

    def read(self):
        bs = self._socket.recv(66666)
        return bs

    def close(self):
        self.exit = True
        logger.debug(f'sink {self.source} exit')

    def pkg_handler(self, msg_buf):
        """
        原数据处理
        :param msg_buf:原信号数据
        :return:
        """
        pass


class NNSink(Sink):
    """
    nnpy类型信号处理基类
    """
    def __init__(self, ip, port, msg_type, index=0, decode_queue=None, result_queue=None, mq=None, sq=None):
        super().__init__(ip=ip, port=port, msg_type=msg_type, mq=mq, sq=sq)
        self.ip = ip
        self.port = port
        self.type = msg_type
        self.index = index
        self.decode_queue = decode_queue
        self.result_queue = result_queue
        self.source = 'nnpy_sink.{}'.format(index)

    def _init_port(self):
        address = "tcp://%s:%s" % (self.ip, self.port,)
        self._socket = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
        self._socket.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')
        self._socket.connect(address)

    def read(self):
        bs = self._socket.recv()
        return bs

    def task(self):
        self._init_port()
        self.pid = os.getpid()
        while not self.exit:
            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue

            # self.sq.put([self.ip, self.port, self.index, self.source])

            t0 = time.time()
            r = self.pkg_handler(buf)
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)
                self.mq.put(r)


class ZmqSink(Sink):
    def __init__(self, ip, port, msg_type, index, fileHandler, mq=None, sq=None):
        super().__init__(ip=ip, port=port, msg_type=msg_type, mq=mq, sq=sq)
        self.ip = ip
        self.port = port
        self.msg_type = msg_type
        self.source = '{}.{:d}'.format(msg_type, index)
        self.index = index
        self.fileHandler = fileHandler
        self.ctx = dict()
        self._buf = b''
        self.context = None

    def _init_port(self):
        self.context = zmq.Context()
        self._socket = self.context.socket(zmq.SUB)
        url = "tcp://%s:%d" % (self.ip, self.port)

        self._socket.connect(url)
        self._socket.setsockopt(zmq.SUBSCRIBE, b'')  # 接收所有消息

    def read(self):
        bs = self._socket.recv()
        return bs

    def pkg_handler(self, msg):
        if self.msg_type == 'j2_zmq':
            data = {
                'type': self.msg_type,
                'source': self.source,
                'log_name': self.msg_type,
                'buf': msg,
                "meta": {
                    "source": self.source,
                    "type": "bin",
                    "parsers": ["j2_zmq"]
                }
            }
            self.fileHandler.insert_general_bin_raw(data)
            return data

    def task(self):
        self._init_port()
        msg_cnt = 0
        while not self.exit:
            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue

            # self.sq.put([self.ip, self.port, self.index, self.source])

            t0 = time.time()
            msg_cnt += 1
            r = self.pkg_handler(buf)
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)

                self.mq.put(r)

        print('sink', self.source, 'exit.')


class UDPSink(Sink):
    def __init__(self, ip, port, topic, protocol, index, file_andler, mq=None, sq=None):
        super(UDPSink, self).__init__(ip=ip, port=port, msg_type=topic, mq=mq, sq=sq)
        self.ip = ip
        self.port = port
        self.msg_type = topic
        self.source = '{}.{:d}'.format(topic, index)
        self.index = index
        self.fileHandler = file_andler
        self.protocol = protocol
        self.ctx = dict()
        self._buf = b''
        self.exit = Event()
        self.type = "udp_sink"

    def _init_port(self):
        print('udp connecting', self.ip, self.port)

        # 0.0.0.*的ip代表是广播类的，需要改为空字符串
        if self.ip.startswith("0.0.0"):
            self.ip = ""

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self.ip, self.port))

    def read(self):
        bs = self._socket.recv(66666)
        return bs

    def pkg_handler(self, msg):
        if self.msg_type == "d1_udp":
            timestamp = time.time()
            r = {
                'type': self.msg_type,
                'source': self.source,
                'log_name': self.msg_type,
                'buf': msg,
                'meta': {
                    "source": self.source,
                    "type": self.msg_type,
                    "parsers": [self.msg_type]
                }
            }
            self.fileHandler.insert_general_bin_raw(r)
            self.fileHandler.insert_raw((timestamp, self.source, str(len(msg))))
        elif self.msg_type == 'q4_100':

            # no timestamp , use local timestamp
            timestamp = time.time()
            msg = struct.pack("<d", timestamp) + msg

            r = {
                'type': self.msg_type,
                'source': self.source,
                'log_name': self.msg_type,
                'buf': msg,
                'meta': {
                    'type': self.msg_type,
                    'source': self.source,
                    'parsers': [self.msg_type]
                }
            }
            self.fileHandler.insert_general_bin_raw(r)
            self.fileHandler.insert_raw((timestamp, self.source, str(len(msg))))

            ret = parsers_dict.get(self.protocol, "default")(0, msg, self.ctx)
            if ret is None:
                return ret
            if type(ret) != list:
                ret = [ret]

            for obs in ret:
                obs['ts'] = timestamp
                obs['source'] = self.source

            return self.msg_type, ret, self.source

    def task(self):
        self._init_port()
        while not self.exit.is_set():
            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue

            # self.sq.put([self.ip, self.port, self.index, self.source])

            t0 = time.time()
            r = self.pkg_handler(buf)
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)
                self.mq.put(r)

        print('sink', self.source, 'exit.')


class TCPSink(Sink):
    def __init__(self, ip, port, msg_type, protocol, index, fileHandler, mq=None, sq=None):
        super(TCPSink, self).__init__(ip=ip, port=port, msg_type=msg_type, mq=mq, sq=sq)
        self.ip = ip
        self.port = port
        self.msg_type = msg_type
        self.source = '{}.{:d}'.format(msg_type, index)
        self.index = index
        self.filehandler = fileHandler
        self.protocol = protocol
        self.ctx = dict()
        self._buf = b''
        self.exit = Event()
        self.type = "tcp_sink"

    def _init_port(self):
        print('tcp connecting', self.ip, self.port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.ip, self.port))

    def read(self):
        bs = self._socket.recv(2048)  # flags=nnpy.DONTWAIT
        return bs

    def pkg_handler(self, msg):
        if self.protocol == 'novatel':
            ret = []
            self._buf += msg
            while True:
                a = self._buf.find(b'#')
                b = self._buf.find(b'\r\n')
                if a == -1 or b == -1 or len(self._buf) == 0 or a > b:
                    if a > -1:
                        self._buf = self._buf[a:]
                    break

                phr = self._buf[a:b].decode()
                # print(a, b, self._buf[a:b])
                self._buf = self._buf[b + 2:]
                try:
                    parser = parsers_dict.get(self.protocol)
                    if not parser:
                        return
                    r = parser(None, phr, self.ctx)
                except Exception as e:
                    logger.error(f'error parsing novatel, {phr}')
                    return
                if not r:
                    return
                r['source'] = self.source
                ret.append(r)
                self.filehandler.insert_raw((r['ts'], r['source'] + '.{}'.format(r['type']), phr))
            return self.msg_type, ret, self.source

    def task(self):
        self._init_port()
        self.pid = os.getpid()
        while not self.exit.is_set():
            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue

            # self.sq.put([self.ip, self.port, self.index, self.source])

            t0 = time.time()
            r = self.pkg_handler(buf)
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)
                self.mq.put(r)

        print('sink', self.source, 'exit.')


class PinodeSink(NNSink):
    def __init__(self, ip, port, msg_type, index, resname, fileHandler, mq=None, sq=None):
        super().__init__(ip=ip, port=port, index=index, msg_type=msg_type, mq=mq, sq=sq)
        self.source = '{}.{:d}'.format(msg_type, index)
        self.msg_type = msg_type
        self.index = index
        self.context = {'source': self.source}
        self.resname = resname
        self.fileHandler = fileHandler
        self.type = 'pi_sink'
        logger.debug(f'inited pi_node sink res:{resname}')
        if resname == 'rtcm':
            self.rtcm3 = rtcm3.RTCM3()
        self._buf = b''
        self.ctx = {}

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        if self.resname == 'pim222':
            source = 'pim222.{}'.format(self.index)
            if not msg.startswith(b'$'):
                return
            self.fileHandler.insert_raw((time.time(), source, msg.decode().strip()))

            decode_msg = {
                "type": "pim222",
                "source": source,
                "data": msg,
            }
            return pim222_decode(decode_msg)

        data = self.decode_pinode_res(self.resname, msg)
        if not data:
            return

        if not isinstance(data, list):
            data = [data]

        for r in data:
            r['source'] = self.source
            if r.get('sensor') == 'm8n':
                r['source'] = 'gps.{:d}'.format(self.index)
            if r['type'] in ub482_defs:
                # print(r)
                self.fileHandler.insert_raw(
                    (r['ts'], r['source'] + '.' + r['type'], compose_from_def(ub482_defs, r)))

            elif r['type'] == 'rtk':  # old d-rtk
                timestamp = r['ts_origin']
                self.fileHandler.insert_raw((timestamp, r['source'] + '.sol',
                                             '{} {} {:.8f} {:.8f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}'.format(
                                                 r['rtkst'], r['orist'], r['lat'], r['lon'], r['hgt'], r['velN'],
                                                 r['velE'], r['velD'], r['yaw'], r['pitch'], r['length'])))
                self.fileHandler.insert_raw((timestamp, r['source'] + '.dop',
                                             '{} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(
                                                 r['sat'][0], r['sat'][1], r['sat'][2], r['sat'][3], r['sat'][4],
                                                 r['sat'][5], r['gdop'],
                                                 r['pdop'], r['hdop'], r['htdop'], r['tdop'], r['cutoff'], r['trkSatn'],
                                                 r['prn'])))
            elif r['type'] == 'gps':
                self.fileHandler.insert_raw((time.time(), r['source'], msg.decode().strip()))

        return self.msg_type, data, self.source

    def decode_pinode_res(self, resname, msg):
        if resname == 'rtk':
            results = json.loads(msg.decode())
            for res in results:
                if res['type'] == 'novatel-like':
                    ret = []
                    phr = res['buf']
                    if len(phr) > 0:
                        try:
                            r = parsers_dict['novatel'](None, phr, None)
                            if r:
                                r['source'] = 'rtk.{}'.format(self.index)
                                self.fileHandler.insert_raw((r['ts'], r['source'] + '.{}'.format(r['type']), phr))
                                ret.append(r)
                        except Exception as e:
                            logger.error(f'error decoding novatel-like:{phr}')

                    return ret

            return results

        elif resname == 'rtcm':
            self.rtcm3.add_data(msg)
            result = self.rtcm3.process_data(dump_decoded=False)
            r = None
            while result != 0:
                if result == rtcm3.Got_Undecoded:
                    pass
                elif result == rtcm3.Got_Packet:
                    r = self.rtcm3.dump(False, False, False, False)
                    # sys.stdout.flush()
                else:
                    print("INTERNAL ERROR: Unknown result (" + str(result) + ")")
                result = self.rtcm3.process_data()
            if r:
                r['type'] = 'rtcm'
                r['len'] = len(msg)
                r['ts'] = time.time()
                return r
        elif resname == 'gps':
            # print(msg)
            data = ublox.decode_nmea(msg.decode())
            return data


class CANCollectSink(NNSink):
    """
    can-fd设备有4/8个can端口，需做区分处理
    """
    def __init__(self, ip, port, can_list, index, fileHandler, device='', mq=None, sq=None):
        super(CANCollectSink, self).__init__(ip, port, "can", index, mq=mq, sq=sq)
        self.type = 'can_sink'
        self.fileHandler = fileHandler
        self.can_list = can_list                  # 四个端口的信号类型列表
        self.device = device
        self.parser = {}
        self.index = index
        # for ch in can_list:
        #     t = can_list[ch]
        #     self.parser[t["dbc"]] = parsers_dict.get(t["dbc"], parsers_dict["default"])
        print('CANCollectSink initialized.', self.type, ip, port)
        self.chlist = {}

        self.source = []
        self.context = {}
        self.log_types = {}
        self.parse_event = Event()
        self.parse_event.set()

        self.init_env()

    def init_env(self):
        # 根据传入四个端口信号进行初始化相关环境
        for port in self.can_list:
            t = self.can_list[port]
            source = '{}.{}.{}.{}'.format(t.get("origin_device", self.device), self.index, port, t["dbc"] if t.get('dbc') else 'none')
            self.context[source] = {"source": "{}.{}".format(t["dbc"], self.index)}         # 解析用的变量空间
            self.source.append(source)              # 来源列表
            self.chlist[port] = t.copy()
            self.chlist[port]['source'] = source
            if isinstance(t["dbc"], list):
                self.chlist[port]['parsers'] = t["dbc"]
            else:
                self.chlist[port]['parsers'] = [t["dbc"]]

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        if not msg:
            return
        # source = t['source']

        # print(msg)
        channel = msg[2]
        source = self.chlist["can{}".format(channel+1)]['source']
        dlc = msg[3]
        can_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        timestamp = struct.unpack('<d', msg[8:16])[0]
        data = msg[16:]

        # channel = msg[0]
        # can_id = struct.unpack('<i', msg[1:5])[0]
        # timestamp = struct.unpack('<d', msg[5:13])[0]
        # data = msg[13:]

        # log_type = self.log_types.get("can{}".format(channel))
        # print('can rcv ch={} id={} dlc={} ts={} data={}'.format(channel, can_id, dlc, timestamp, data))
        self.fileHandler.insert_raw((timestamp, source, '0x%x' % can_id + ' ' + data.hex()))

        if not self.parse_event.is_set():
            return

        # 添加到解析队列
        decode_msg = {
            "type": "can",
            "index": self.index,
            "data": data,
            "num": channel,
            "parsers": self.chlist["can{}".format(channel+1)]["parsers"],
            "cid": can_id,
            "ts": timestamp
        }
        return can_decode(decode_msg)


class MQTTSink(NNSink):

    def __init__(self, ip, can_list, index, fileHandler, device="", cid="", mq=None, sq=None):
        super(MQTTSink, self).__init__(ip, "*", can_list, mq=mq, sq=sq)
        self.type = 'mqtt_sink'
        self.ip = ip
        self.device = device
        self.index = index
        self.fileHandler = fileHandler
        self.can_list = can_list  # 四个端口的信号类型列表
        self.parser = {}

        self.parser_list = []
        self.context = {}
        self.log_types = {}
        self.parse_event = Event()
        # self.parse_event.set()

        self.client = mqtt.Client(cid)

        self.topic_list = {}
        self.init_env()

        print('MQTTSink initialized.', self.type, ip)
        self.mq_time = 0
        self.mq_count = 0
        self.mq_last_time = time.time()

    def init_env(self):
        # 根据传入四个端口信号进行初始化相关环境
        for ch in self.can_list:
            t = self.can_list[ch]
            if isinstance(t["dbc"], list):
                for d in t["dbc"]:
                    source = '{}.{}.{}.{}'.format(t.get('origin_device', self.device), self.index, ch, d)
                    self.parser[d] = source
                    self.parser_list.append(d)
            else:
                source = '{}.{}.{}.{}'.format(t.get('origin_device', self.device), self.index, ch, t["dbc"])
                self.parser[t["dbc"]] = source
                self.parser_list.append(t["dbc"])

    def _init_port(self):
        # print('mqtt connecting', self.ip)

        self.client.connect(self.ip)
        print('mqtt connected', self.ip)
        # print('topic list:', self.topic_list)
        for topic in self.topic_list:
            self.client.subscribe(topic, self.topic_list[topic]['qos'])
        self.client.on_message = self.on_msg
        self.mq_last_time = time.time()

    def run(self):
        pid = os.getpid()
        print('mqtt sink {} pid:'.format(self.parser_list), pid)
        self._init_port()
        self.client.loop_forever()

    def close(self):
        self.client.loop_stop()

    def on_msg(self, mosq, obj, msg):
        data = msg.payload

        if not data:
            return

        topic = msg.topic
        # print(topic, data)

        t = self.topic_list.get(topic)
        if not t:
            return

        source = t['source']
        channel = data[2]
        dlc = data[3]
        can_id = int.from_bytes(data[4:8], byteorder="little", signed=False)
        timestamp = struct.unpack('<d', data[8:16])[0]
        can_data = data[16:]

        # print('can rcv ch={} id=0x{:x} dlc={} ts={} data={}'.format(channel, can_id, dlc, timestamp, can_data))
        self.fileHandler.insert_raw((timestamp, source, '0x%x' % can_id + ' ' + can_data.hex()))

        if not self.parse_event.is_set():
            return

        # 添加到解析队列
        decode_msg = {
            "type": "can",
            "index": self.index,
            "data": data,
            "num": channel,
            "parsers": topic,
            "cid": can_id,
            "ts": timestamp
        }
        return can_decode(decode_msg)


class CANSink(NNSink):
    def __init__(self, ip, port, msg_type, topics, index, fileHandler, mq=None, sq=None):
        super().__init__(ip=ip, port=port, msg_type=msg_type, index=index, mq=mq, sq=sq)
        self.fileHandler = fileHandler                          # 日志对象
        self.type = 'can_sink'
        self.log_types = {'can0': 'CAN' + '{:01d}'.format(self.index * 2),
                          'can1': 'CAN' + '{:01d}'.format(self.index * 2 + 1)}
        self.log_type = self.log_types.get(self.msg_type)
        self.parse_event = Event()
        self.parse_event.set()

        # 解析方法初始化
        if isinstance(topics, list):
            self.parsers = topics
        else:
            self.parsers = [topics]

        print('CANSink initialized.', self.type, ip, port, self.parsers)

    def pkg_handler(self, msg):
        # can信号基本信息解析
        msg = memoryview(msg).tobytes()
        can_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        timestamp = struct.unpack('<d', msg[8:16])[0]
        data = msg[16:]
        id = '0x%x' % can_id
        log_type = self.log_type
        log_bytes = data.hex()
        # 记录原始报文
        self.fileHandler.insert_raw((timestamp, log_type, id + ' ' + log_bytes))

        if not self.parse_event.is_set():
            return

        # 添加到解析队列
        decode_msg = {
            "type": "can",
            "index": self.index,
            "data": data,
            "parsers": self.parsers,
            "cid": can_id,
            "ts": timestamp
        }
        return can_decode(decode_msg)


class GsensorSink(NNSink):
    def __init__(self, ip, port, msg_type, index, fileHandler, mq=None, sq=None):
        super(GsensorSink, self).__init__(ip=ip, port=port, msg_type=msg_type, index=index, mq=mq, sq=sq)
        self.fileHandler = fileHandler
        self.type = 'gsensor_sink'

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        gyro = [0, 0, 0]
        accl = [0, 0, 0]
        timestamp, gyro[0], gyro[1], gyro[2], accl[0], accl[1], accl[2], temp, sec, usec = struct.unpack(
            '<dhhhhhhhII', msg[8:])
        temp = temp / 340 + 36.53
        self.fileHandler.insert_raw((timestamp, 'Gsensor.{}'.format(self.index),
                                     '{} {} {} {} {} {} {:.6f} {}'.format(accl[0], accl[1], accl[2], gyro[0], gyro[1],
                                                                          gyro[2], temp, sec, usec)))


class CameraSink(NNSink):
    def __init__(self, ip, port, msg_type, index, fileHandler, is_main=False, devname=None, mq=None, sq=None):
        super(CameraSink, self).__init__(ip=ip, port=port, msg_type=msg_type, index=index, mq=mq, sq=sq)
        self.fileHandler = fileHandler
        self.source = '{:s}.{:d}'.format(devname, index)
        self.is_main = is_main
        self.devname = devname
        self.type = 'cam_sink'

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        jpg = msg[16:]
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        timestamp, = struct.unpack('<d', msg[8:16])

        r = {'ts': timestamp, 'type': 'video', 'img': jpg, 'frame_id': frame_id, 'source': self.source,
             'is_main': self.is_main, 'device': self.devname}
        self.fileHandler.insert_jpg(r)

        return frame_id, r, self.source


class FlowSink(Sink):
    def __init__(self, ip, port, msg_type, index, fileHandler, name='x1_algo', device="", dbc=None, port_name="", sq=None,
                 log_name='pcv_log', topic='pcview', is_main=False, is_back=False, mq=None, save_type=None, install_key="video"):
        super().__init__(ip=ip, port=port, msg_type=msg_type, index=index, mq=mq, sq=sq)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.ip = ip
        self.port = port
        self.log_name = log_name
        self.is_main = is_main
        self.is_back = is_back
        self.install_key = install_key
        self.type = 'flow_sink'
        self.topic = topic
        self.dbc = dbc
        self.device = device
        self.port_name = port_name
        self.source = name + '.{:d}'.format(index)
        self.index = index
        self.name = name
        self.new_a1j = False        # 做个兼容处理，新的a1j不需要进行msgpack.unpack
        self.save_type = save_type

        self.client = None

        # 初始化解析流程
        if self.topic == '*' or self.dbc == "video_h265":   # Q3华为mdc数据
            if 24011 <= self.port <= 24017 or self.dbc == "video_h265":     # h264视频数据
                self.pkg_handler = self.video_h265
            elif self.dbc == "video_h265_new":
                self.pkg_handler = self.video_h265_new
            elif self.port == 28011:
                self.pkg_handler = self.mdc_ts
            else:
                self.pkg_handler = self.mdc_data
        elif self.dbc == "video_jpeg":
            self.pkg_handler = self.video_jpeg
        elif self.topic == 'MdcTime':
            self.pkg_handler = self.mdc_ts
        elif self.save_type == 'bin':
            self.pkg_handler = self.bin_data

    async def _run(self):
        logger.warning(f"FlowSink Initialized {self.ip}:{self.port} topic:{self.topic}")
        session = aiohttp.ClientSession()
        URL = 'ws://' + str(self.ip) + ':' + str(self.port)
        async with session.ws_connect(URL) as ws:
            msg = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': self.topic,
            }
            data = msgpack.packb(msg)
            await ws.send_bytes(data)
            async for msg in ws:
                if self.exit:
                    break

                # self.sq.put([self.ip, self.port, self.index, self.source])

                r = self.pkg_handler(msg)
                if r is not None:
                    if isinstance(r[0], type("")):
                        if 'x1_data' in r[0]:
                            self.mq.put((r[1]['frame_id'], r[1], r[0]))
                        elif 'calib_param' in r[0]:
                            self.mq.put((0, r[1], self.source))
                    else:
                        self.mq.put((*r, self.source))
                else:
                    time.sleep(0.001)

    def task(self):
        import asyncio
        import platform

        if platform.python_version() > "3.6":
            from tornado.platform.asyncio import AnyThreadEventLoopPolicy
            asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
        self.client = asyncio.get_event_loop()
        try:
            self.client.run_until_complete(self._run())
        except Exception as e:
            logger.error(f'error when initiating flow sink on {self.ip}:{self.port}, {e}')

    def decode_data(self, msg):
        # 判断是否新的a1j设备，如果是新a1j设备的话不需要进行解码处理
        if not self.new_a1j:
            try:
                data = msgpack.unpackb(msg.data)
            except Exception as e:
                self.new_a1j = True
                data = msg.data
        else:
            data = msg.data
        return data

    def decode_video(self, data):
        """
        解析视频数据，对图像数据跟视频头格式进行解析处理
        Args:
            msg:

        Returns:
        """
        head_data = {
            "height": int.from_bytes(data[:4], byteorder='little', signed=False),
            "width": int.from_bytes(data[4:8], byteorder='little', signed=False),
            "send_time_high": int.from_bytes(data[8:12], byteorder='little', signed=False),
            "send_time_low": int.from_bytes(data[12:16], byteorder='little', signed=False),
            "frame_type": int.from_bytes(data[16:20], byteorder='little', signed=False),
            "data_size": int.from_bytes(data[20:24], byteorder='little', signed=False),
            "seq": int.from_bytes(data[24:28], byteorder='little', signed=False),
            "sec": int.from_bytes(data[28:32], byteorder='little', signed=False),
            "nsec": int.from_bytes(data[32:36], byteorder='little', signed=False)
        }
        img = data[36:]
        return img, head_data

    def img_ext_info(self, data):
        """
        额外的图像信息
        Args:
            msg:

        Returns:

        """
        head_data = [
            int.from_bytes(data[:4], byteorder='little', signed=False),                              # 图像序号
            int.from_bytes(data[4:8], byteorder='little', signed=False),                      # 帧类型 0：MJPEG, 1:H264, 2:H265
            int.from_bytes(data[8:12], byteorder='little', signed=False),                      # 数据大小
            int.from_bytes(data[12:16], byteorder='little', signed=False),                         # 宽
            int.from_bytes(data[16:20], byteorder='little', signed=False),                        # 高

            int.from_bytes(data[20:24], byteorder='little', signed=False),                 # Fsync曝光信号触发的时刻，数据面时间，秒
            int.from_bytes(data[24:28], byteorder='little', signed=False),                # Fsync曝光信号触发的时刻，数据面时间，纳秒
            int.from_bytes(data[28:32], byteorder='little', signed=False),                # Fsync曝光信号触发的时刻，管理面时间，秒
            int.from_bytes(data[32:36], byteorder='little', signed=False),               # Fsync曝光信号触发的时刻，管理面时间，纳秒

            int.from_bytes(data[36:40], byteorder='little', signed=False),             # 图像曝光开始的时刻，数据面时间，秒
            int.from_bytes(data[40:44], byteorder='little', signed=False),            # 图像曝光开始的时刻，数据面时间，纳秒
            int.from_bytes(data[44:48], byteorder='little', signed=False),            # 图像曝光开始的时刻，管理面时间，秒
            int.from_bytes(data[48:52], byteorder='little', signed=False),           # 图像曝光开始的时刻，管理面时间，纳秒

            int.from_bytes(data[52:56], byteorder='little', signed=False),               # 图像曝光结束的时刻，数据面时间，秒
            int.from_bytes(data[56:60], byteorder='little', signed=False),              # 图像曝光结束的时刻，数据面时间，纳秒
            int.from_bytes(data[60:64], byteorder='little', signed=False),              # 图像曝光结束的时刻，管理面时间，秒
            int.from_bytes(data[64:68], byteorder='little', signed=False),             # 图像曝光结束的时刻，管理面时间，纳秒

            int.from_bytes(data[68:72], byteorder='little', signed=False),                      # 图像大像素曝光持续时间，微秒
            int.from_bytes(data[72:76], byteorder='little', signed=False),                      # 图像小像素曝光持续时间，微秒
            # "image_supplement": int.from_bytes(data[76:128], byteorder='little', signed=False),             # 图像附加描述信息，跟平台相关
        ]

        log = ""
        for i in head_data:
            log += "{} ".format(i)

        timestamp = head_data[7] + head_data[8]/1000000000
        self.fileHandler.insert_raw(
            (timestamp, "{}.{}.{}.{}".format(self.device, self.index, self.port_name, self.dbc), log.strip()))

    def mdc_ts(self, msg):
        data = self.decode_data(msg)
        data = data['data']
        ads_sec = int.from_bytes(data[:8], byteorder='little', signed=False),
        ads_nsec = int.from_bytes(data[8:16], byteorder='little', signed=False),
        gnss_sec = int.from_bytes(data[16:24], byteorder='little', signed=False),
        gnss_nsec = int.from_bytes(data[24:32], byteorder='little', signed=False),
        timestamp = time.time()
        # print(ads_sec, ads_nsec, gnss_sec, gnss_nsec)
        # print("mdc_ts", "{} {} {} {}".format(ads_sec, ads_nsec, gnss_sec, gnss_nsec))
        self.fileHandler.insert_raw((timestamp, "mdc_ts", "{} {} {} {}".format(ads_sec[0], ads_nsec[0], gnss_sec[0], gnss_nsec[0])))

    def video_h265(self, msg):
        data = self.decode_data(msg)
        img, head_data = self.decode_video(data)
        sec = head_data["send_time_high"]
        nsec = head_data["send_time_low"]
        timestamp = sec + nsec/1000000000

        if self.topic != "*":
            log_name = self.topic
        else:
            log_name = self.port_name
        r = {
            "source": self.source,
            "log_name": log_name,
            "buf": img,
            "meta": {
                "source": '{}.{}.{}.'.format(self.device, self.index, self.port_name),
                "type": "video",
                "parsers": [self.dbc]
            }
        }
        self.fileHandler.insert_general_bin_raw(r)
        self.fileHandler.insert_raw(
            (timestamp, "{}.{}.{}.{}".format(self.device, self.index, self.port_name, self.dbc), "{:d} {:d} {} {} {} {} {} {} {}".format(head_data["height"], head_data["width"], head_data["send_time_high"],
                                                                                                         head_data["send_time_low"], head_data["frame_type"], head_data["data_size"], head_data["seq"], head_data["sec"], head_data["nsec"])))

    def video_jpeg(self, msg):
        data = self.decode_data(msg)
        img, head_data = self.decode_video(data)
        r = {'ts': head_data['sec']+head_data['nsec']/1000000000, 'img': img, 'frame_id': head_data['seq'],
             'type': 'video', 'source': self.source, 'is_main': self.is_main, "is_back": self.is_back,
             'transport': 'libflow', 'install': self.install_key,
             "meta": {
                 "source": '{}.{}.{}.{}'.format(self.device, self.index, self.port_name, self.topic),
                 "type": "video",
                 "parsers": [self.dbc]
             }
        }
        self.fileHandler.insert_jpg(r)
        return head_data['seq'], r

    def mdc_data(self, msg):
        # Q3华为mdc算法数据
        data = self.decode_data(msg)

        data["origin-source"] = data["source"]
        data["source"] = self.source
        data["data"] = base64.b64encode(data["data"]).decode('utf-8')
        self.fileHandler.insert_pcv_raw(data)
        return

    def bin_data(self, msg):
        """
        数据保存为bin文件
        :param msg:
        :return:
        """
        data = self.decode_data(msg)
        if b'data' in data:
            payload = data[b'data']
            topic = data[b'topic'].decode()
        elif 'data' in data:
            payload = data['data']
            topic = data['topic']
        else:
            return

        if topic == 'calib_params':
            calib_params = msgpack.unpackb(payload)
            calib_params = mytools.convert(calib_params)
            if calib_params:
                r = {'type': 'calib_params', 'source': self.source, 'ts': time.time()}
                r.update(calib_params)
                return 'calib_param', r
        else:
            r = {
                "source": self.source,
                "log_name": topic,
                "buf": payload,
                "meta": {
                    "source": '{}.{}.{}.{}'.format(self.device, self.index, self.port_name, topic),
                    "type": self.msg_type,
                    "parsers": [topic]
                }
            }
            self.fileHandler.insert_general_bin_raw(r)
            return

    def pkg_handler(self, msg):
        data = self.decode_data(msg)

        # 新a1j设备图片数据
        if isinstance(data, bytes) and data.startswith(b'\xff\x03'):  # jpeg pack header
            frame_id = int.from_bytes(data[4:8], byteorder='little', signed=False)
            self.last_fid = frame_id
            ts = int.from_bytes(data[16:24], byteorder='little', signed=False)
            ts = ts / 1000000
            jpg = data[24:]
            if msg.type in (aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR):
                return None

            r = {'ts': ts, 'img': jpg, 'frame_id': frame_id, 'type': 'video', 'source': self.source,
                 'is_main': self.is_main, 'is_back': self.is_back, 'transport': 'libflow', "install": self.install_key,
                 'meta': {
                     'source': 'camera' if self.is_main else self.source,
                     'type': self.msg_type,
                     'parsers': [self.topic]
                 }
                }
            self.fileHandler.insert_jpg(r)
            return frame_id, r

        ts = time.time()
        if b'data' in data:
            msg_src = data[b'source'].decode()
            payload = data[b'data']
            topic = data[b'topic'].decode()
        elif 'data' in data:
            msg_src = data['source']
            payload = data['data']
            topic = data['topic']
        else:
            return

        if msg_src == 'pcview':
            if topic == 'finish':
                buf = payload
                if b'rc_fusion' in buf:
                    buf = msgpack.unpackb(buf)
                    buf = mytools.convert(buf)
                    data = buf['rc_fusion']
                    buf = msgpack.packb(data, use_bin_type=True)
                    # print(buf)
                    r = {'source': self.source, 'buf': buf}
                    self.fileHandler.insert_fusion_raw(r)
            elif topic == 'imuinfo':
                imu_info = msgpack.unpackb(payload)
                imu_info = mytools.convert(imu_info)
                for idx in range(imu_info['data_count']):
                    d = imu_info['imu_info'][idx]
                    ts = d['timestamp'] / 1000000
                    self.fileHandler.insert_raw((ts, self.source + '.gsensor', '{} {} {} {} {} {} {} {}'.format(
                        d['accel'][0], d['accel'][1], d['accel'][2],
                        d['gyro'][0], d['gyro'][1], d['gyro'][2],
                        d['temp'], int(ts), 1000000 * (ts - int(ts)))))
                return
            elif topic == 'pcview':
                if b'calib_param' in payload:
                    calib_params = msgpack.unpackb(payload)
                    calib_params = mytools.convert(calib_params)
                    if calib_params:
                        r = {'type': 'calib_param', 'source': self.source, 'ts': time.time(), 'frame_id': calib_params['frame_id']}
                        r.update(calib_params['calib_param'])
                        return 'calib_param', r
                elif payload.startswith(b'\xff\x03'):  # jpeg pack header
                    frame_id = int.from_bytes(payload[4:8], byteorder='little', signed=False)
                    self.last_fid = frame_id
                    ts = int.from_bytes(payload[16:24], byteorder='little', signed=False)
                    ts = ts / 1000000
                    jpg = payload[24:]
                    if msg.type in (aiohttp.WSMsgType.CLOSED,
                                    aiohttp.WSMsgType.ERROR):
                        return None

                    r = {'ts': ts, 'img': jpg, 'frame_id': frame_id, 'type': 'video', 'source': self.source,
                         'is_main': self.is_main, "is_back": self.is_back, 'transport': 'libflow',
                         'install': self.install_key,
                         'meta': {
                             'source': 'camera' if self.is_main else self.source,
                             'type': self.msg_type,
                             'parsers': [topic]
                         }
                    }
                    self.fileHandler.insert_jpg(r)
                    return frame_id, r
                else:
                    pass
            elif topic == "video":
                frame_id = int.from_bytes(payload[4:8], byteorder='little', signed=False)
                self.last_fid = frame_id
                ts = int.from_bytes(payload[16:24], byteorder='little', signed=False)
                ts = ts / 1000000
                jpg = payload[24:]
                if msg.type in (aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR):
                    return None

                r = {'ts': ts, 'img': jpg, 'frame_id': frame_id, 'type': 'video', 'source': self.source,
                     'is_main': self.is_main, "is_back": self.is_back, 'transport': 'libflow',
                     'install': self.install_key,
                     'meta': {
                         'source': 'camera' if self.is_main else self.source,
                         'type': self.msg_type,
                         'parsers': [topic]
                     }
                }
                self.fileHandler.insert_jpg(r)
                return frame_id, r
            elif topic == 'calib_params':
                calib_params = msgpack.unpackb(payload)
                calib_params = mytools.convert(calib_params)
                if calib_params:
                    r = {'type': 'calib_params', 'source': self.source, 'ts': time.time()}
                    r.update(calib_params)
                    return 'calib_param', r
        elif msg_src == 'lane_profiling':
            if topic == 'lane_profiling_data':
                r = {
                    'type': 'algo_debug',
                    'source': self.source,
                    'log_name': self.name,
                    'buf': payload,
                    'meta': {
                        'source': self.source,
                        'type': self.msg_type,
                        'parsers': [topic]
                    }
                }
                self.fileHandler.insert_general_bin_raw(r)
                return 'algo_debug', r
        elif msg_src == 'imu':
            if topic == 'imuinfo':
                imu_info = msgpack.unpackb(payload)
                imu_info = mytools.convert(imu_info)

                for idx in range(imu_info['data_count']):
                    d = imu_info['imu_info'][idx]
                    ts = d['timestamp'] / 1000000
                    rtos_tick = d['rtostick']
                    self.fileHandler.insert_raw((ts, self.source + '.gsensor', '{} {} {} {} {} {} {} {}'.format(
                        d['accel'][0], d['accel'][1], d['accel'][2],
                        d['gyro'][0], d['gyro'][1], d['gyro'][2],
                        d['temp'], rtos_tick, 0)))
                return
        elif msg_src == 'imuinfo':
            if topic == 'imuinfo':
                imu_info = msgpack.unpackb(payload)
                imu_info = mytools.convert(imu_info)
                for idx in range(imu_info['data_count']):
                    d = imu_info['imu_info'][idx]
                    ts = d['timestamp'] / 1000000
                    self.fileHandler.insert_raw((ts, self.source + '.gsensor', '{} {} {} {} {} {} {} {}'.format(
                        d['accel'][0], d['accel'][1], d['accel'][2],
                        d['gyro'][0], d['gyro'][1], d['gyro'][2],
                        d['temp'], int(ts), 1000000 * (ts - int(ts)))))
                return

        else:
            pass

        if b'frame_id' in payload:
            payload = msgpack.unpackb(payload)
            if b'ultrasonic' in payload:
                payload[b'ultrasonic'][b'can_data'] = [x for x in payload[b'ultrasonic'][b'can_data']]

            pcv = mytools.convert(payload)

            if 'data' in pcv and 'key' in pcv:
                pcv[pcv['key']] = pcv['data']
                pcv.pop('data')
                pcv.pop('key')

            pcv['source'] = self.source
            pcv['type'] = 'pcv_data'
            pcv['ts'] = ts
            self.fileHandler.insert_pcv_raw(pcv)

            if not self.is_main:
                return None

            return 'x1_data', pcv, self.source


class ProtoSink(NNSink):
    def __init__(self, ip, port, msg_type, index, fileHandler, name='proto',
                 log_name='proto_log', topic='pcview', mq=None, sq=None):
        super().__init__(ip, port, msg_type, index, mq=mq, sq=sq)
        self.fileHandler = fileHandler
        self.ip = ip
        self.port = port
        self.log_name = log_name
        self.type = 'prote_sink'
        self.topic = topic
        self.source = name + '.{:d}'.format(index)

        self.key_pb = {
            # "vehicle": vehicle_pb2.Vehicle,
            "pedestrian": pedestrian_pb2.Pedestrian,
            "roadmarking": roadmarking_pb2.Roadmarking,
            "object_attribute": object_attribute_pb2.Box3DGroup,
            "vehicle": object_pb2.ObjectList,
            "ped": object_pb2.ObjectList,
            "calib_param": calib_param_pb2.CalibParam,
            "tsr": object_pb2.ObjectList,
            "dev_object": dev_object_pb2.DevObjectList,
            "vehicle_signal": vehicle_signal_pb2.VehicleSignal,
            "obs": object_pb2.ObjectList
        }

    async def _run(self):
        print("ProtoSink Initialized", self.ip, self.port, self.topic)
        session = aiohttp.ClientSession()
        URL = 'ws://' + str(self.ip) + ':' + str(self.port)
        async with session.ws_connect(URL) as ws:
            msg = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': self.topic,
            }

            data = msgpack.packb(msg)
            await ws.send_bytes(data)
            async for msg in ws:
                if self.exit:
                    break
                self.pkg_handler(msg)

    def run(self):
        import asyncio
        import platform

        if platform.python_version() > "3.6":
            from tornado.platform.asyncio import AnyThreadEventLoopPolicy
            asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._run())
        except Exception as e:
            print(bcl.FAIL+'error:'+ str(e) + ' when initiating proto flow sink on'+bcl.ENDC, self.ip, self.port)

    def pkg_handler(self, msg):
        data = msgpack.unpackb(msg.data)
        # print('-----', data[b'topic'])
        if b'data' in data:
            payload = data[b'data']
            topic = data[b'topic'].decode()
        elif 'data' in data:
            payload = data['data']
            topic = data['topic']
        else:
            return

        if topic in self.key_pb:
            pb = self.key_pb.get(topic)
            if pb is None:
                return
            v = pb()
            v.ParseFromString(payload)
            if topic == "calib_param" or topic == "vehicle_signal":
                frame_id = self.fileHandler.fid
            else:
                frame_id = v.frame_id
            try:
                data = json_format.MessageToDict(v, preserving_proto_field_name=True)
                self.fileHandler.insert_pcv_raw(
                    {"source": self.source, "frame_id": frame_id, "type": topic, topic: data,
                     "rec_ts": time.time()})
            except Exception as e:
                print("protobuf decode error:", e)
