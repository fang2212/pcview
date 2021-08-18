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
import msgpack
import nnpy
import socket
import zmq
import paho.mqtt.client as mqtt

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


try:
    import pynng

    nn_impl = 'pynng'
except Exception as e:
    nn_impl = 'nanomsg'
    # import nanomsg

nn_impl = 'nanomsg'
# import nanomsg

# import pynng
from parsers import ublox, rtcm3
from parsers.drtk import V1_msg, v1_handlers
from parsers.parser import parsers_dict
from recorder.convert import *
from tools import mytools
from collections import deque


class NNSink(Thread):
    def __init__(self, queue, ip, port, msg_type, index=0, isheadless=False):
        super(NNSink, self).__init__()
        self.daemon = True
        self.dev = ip
        self.channel = port
        self.queue = queue
        self.type = msg_type
        self.index = index
        self.cls = msg_type
        self.isheadless = isheadless
        self.profile_intv = 1
        self.exit = Event()
        # if 'can' in msg_type:
        #     self.cls = 'can'
        # print(self.type, 'start.')
        self.source = 'general_dev.{}'.format(index)

    def _init_port(self):
        address = "tcp://%s:%s" % (self.dev, self.channel,)
        if nn_impl == 'pynng':
            self._socket = pynng.Sub0(dial=address, topics=b'', recv_timeout=500)
            self._socket.recv_buffer_size = 1
        else:
            # self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
            # nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
            # nanomsg.wrapper.nn_connect(self._socket, address)
            self._socket = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
            self._socket.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')
            self._socket.connect(address)

    def read(self):
        # if nn_impl == 'pynng':
        #     try:
        #         bs = self._socket.recv()
        #     except Exception as e:
        #         return
        # else:
        #     # bs = nanomsg.wrapper.nn_recv(self._socket, 1)[1]
        bs = self._socket.recv()  # flags=nnpy.DONTWAIT
        # print(self._socket.recv_buffer_size)
        return bs
        # return self._socket.recv()

    def _init_local_socket(self):
        self.ss = None

    def run(self):
        pid = os.getpid()
        print('sink {} pid:'.format(self.source), pid)
        time0 = time.time()
        self._init_port()
        pt_sum = 0
        next_check = 0
        self.pid = os.getpid()
        last_ts = 0
        msg_cnt = 0
        throuput = 0
        # if 'can' in self.type:
        #     print(self.type, 'start.')
        while not self.exit.is_set():

            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue
            t0 = time.time()
            msg_cnt += 1
            # throuput += len(buf)
            r = self.pkg_handler(buf)
            # dt = time.time() - t0
            # t1 = time.time()
            # pt_sum += t1 - t0
            # if t1 - last_ts >= 1.0:
            #     print('{} sink total cost in last sec: {:.2f}ms, cnt{}, throuput{}'.format(self.source, pt_sum*1000, msg_cnt, throuput))
            #     pt_sum = 0
            #     last_ts = t1
            #     msg_cnt = 0
            #     # throuput = 0
            # print(self.dev, self.type, self.channel, 'dt: {:.5f}'.format(dt))
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)
                if not self.queue.full():
                    self.queue.put((r))
                else:
                    print("full")
                    time.sleep(0.001)
                    continue

            # time.sleep(0.01)
            # if t0 > next_check:
            #     profile_info = {'type': 'profiling', 'source': self.source, 'pt_sum': pt_sum, 'uptime': t0-time0, 'ts': t0, 'pid': os.getpid()}
            #     self.queue.put((0, profile_info, self.source))
            #     next_check = t0 + self.profile_intv

        print('sink', self.source, 'exit.')

    def close(self):
        self.exit.set()

    def pkg_handler(self, msg_buf):
        pass


class ZmqSink(Thread):
    def __init__(self, queue, ip, port, topic, protocol, index, fileHandler):
        super(ZmqSink, self).__init__()
        self.ip = ip
        self.port = port
        self.channel = topic
        self.queue = queue
        self.source = '{}.{:d}'.format(topic, index)
        self.index = index
        self.fileHandler = fileHandler
        self.protocol = protocol
        self.ctx = dict()
        self._buf = b''
        self.exit = Event()
        self.type = "zmq_sink"
        self.context = None

    def _init_port(self):
        print('connecting', self.ip, self.port)
        self.context = zmq.Context()
        self._socket = self.context.socket(zmq.SUB)
        url = "tcp://%s:%d" % (self.ip, self.port)

        self._socket.connect(url)
        self._socket.setsockopt(zmq.SUBSCRIBE, b'')  # 接收所有消息

    def read(self):
        bs = self._socket.recv()
        return bs

    def pkg_handler(self, msg):
        if self.channel == 'j2_zmq':

            r = {'type': self.channel, 'source': self.source, 'log_name': self.source}
            r['buf'] = msg
            self.fileHandler.insert_general_bin_raw(r)


    def run(self):
        pid = os.getpid()
        print('sink {} pid:'.format(self.source), pid)
        time0 = time.time()
        self._init_port()
        pt_sum = 0
        next_check = 0
        self.pid = os.getpid()
        last_ts = 0
        msg_cnt = 0
        throuput = 0
        # if 'can' in self.type:
        #     print(self.type, 'start.')
        while not self.exit.is_set():

            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue
            t0 = time.time()
            msg_cnt += 1
            # throuput += len(buf)
            r = self.pkg_handler(buf)
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)
                if not self.queue.full():
                    self.queue.put((r))
                else:
                    time.sleep(0.001)
                    continue

        print('sink', self.source, 'exit.')



class UDPSink(Thread):
    def __init__(self, queue, ip, port, topic, protocol, index, fileHandler):
        super(UDPSink, self).__init__()
        self.ip = ip
        self.port = port
        self.channel = topic
        self.queue = queue
        self.source = '{}.{:d}'.format(topic, index)
        self.index = index
        self.fileHandler = fileHandler
        self.protocol = protocol
        self.ctx = dict()
        self._buf = b''
        self.exit = Event()
        self.type = "ucp_sink"

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
        if self.channel == "d1_udp":
            timestamp = time.time()
            r = {'type': self.channel, 'source': self.source, 'log_name': self.source, 'buf': msg}
            self.fileHandler.insert_general_bin_raw(r)
            self.fileHandler.insert_raw((timestamp, self.source, str(len(msg))))
        elif self.channel == 'q4_100':

            # no timestamp , use local timestamp

            timestamp = time.time()
            msg = struct.pack("<d", timestamp) + msg

            r = {'type': self.channel, 'source': self.source, 'log_name': self.source}
            r['buf'] = msg
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
            # log_bytes = data.hex()
            # print('CAN sink save raw.', self.source)

            return self.channel, ret, self.source

    def run(self):
        pid = os.getpid()
        print('sink {} pid:'.format(self.source), pid)
        time0 = time.time()
        self._init_port()
        pt_sum = 0
        next_check = 0
        self.pid = os.getpid()
        last_ts = 0
        msg_cnt = 0
        throuput = 0
        # if 'can' in self.type:
        #     print(self.type, 'start.')
        while not self.exit.is_set():

            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue
            t0 = time.time()
            msg_cnt += 1
            # throuput += len(buf)
            r = self.pkg_handler(buf)
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)
                if not self.queue.full():
                    self.queue.put((r))
                else:
                    time.sleep(0.001)
                    continue

        print('sink', self.source, 'exit.')


class MQTTSink(Thread):

    def __init__(self, queue, ip, can_list, index, fileHandler, isheadless=False, device="", cid=""):
        super(MQTTSink, self).__init__()
        self.type = 'mqtt_sink'
        self.ip = ip
        self.device = device
        self.index = index
        self.fileHandler = fileHandler
        self.can_list = can_list  # 四个端口的信号类型列表
        self.parser = {}
        self.queue = queue
        for ch in can_list:
            t = can_list[ch]
            self.parser[t["dbc"]] = parsers_dict.get(t["dbc"], parsers_dict["default"])

        self.source = []
        self.context = {}
        self.log_types = {}
        self.parse_event = Event()
        self.parse_event.set()

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
            source = '{}.{}.{}.{}'.format(self.device, self.index, ch, t['dbc'])
            self.source.append(source)
            # self.log_types["can{}".format(i)] = source  # 写入日志的信号名
            self.context[source] = {"source": "{}.{}".format(t["dbc"], self.index)}  # 解析用的变量空间
            # self.source.append(source)  # 来源列表
            self.topic_list[t['topic']] = self.can_list[ch]
            self.topic_list[t['topic']]['name'] = ch
            self.topic_list[t['topic']]['source'] = source

    def _init_port(self):
        print('mqtt connecting', self.ip)

        self.client.connect(self.ip)
        for topic in self.topic_list:
            self.client.subscribe(topic, self.topic_list[topic]['qos'])
        self.client.on_message = self.pkg_handler
        self.mq_last_time = time.time()
        # client.loop_start()

    def run(self):
        pid = os.getpid()
        print('mqtt sink {} pid:'.format(self.source), pid)
        self._init_port()
        self.client.loop_forever()

    def pkg_handler(self, mosq, obj, msg):
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

        parser = self.parser[t["dbc"]]
        ret = parser(can_id, can_data, self.context[source])
        now = time.time()
        self.mq_time += now - self.mq_last_time
        self.mq_last_time = now
        self.mq_count += 1
        print("avg time:", self.mq_time/self.mq_count)

        print(timestamp, '0x%x' % can_id,  can_data.hex(), ret)
        if ret is None:
            return None

        if isinstance(ret, list):
            for obs in ret:
                obs['ts'] = timestamp
        else:
            ret['ts'] = timestamp
        # print(ret)
        if isinstance(ret, list):
            # print('r is list')
            for obs in ret:
                obs['ts'] = timestamp
                obs['source'] = source
                # print(obs)
        else:
            # print('r is not list')
            ret['ts'] = timestamp
            ret['source'] = source

        self.queue.put((can_id, ret, source))
        # return can_id, ret, source


class TCPSink(Thread):
    def __init__(self, queue, ip, port, channel, protocol, index, fileHandler):
        super(TCPSink, self).__init__()
        self.ip = ip
        self.port = port
        self.channel = channel
        self.queue = queue
        self.source = 'tcp.{:d}'.format(index)
        self.index = index
        self.filehandler = fileHandler
        self.protocol = protocol
        self.ctx = dict()
        self._buf = b''
        self.exit = Event()
        self.type = "tcp_sink"

    def _init_port(self):
        print('connecting', self.ip, self.port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.ip, self.port))

    def read(self):
        bs = self._socket.recv(2048)  # flags=nnpy.DONTWAIT
        return bs

    def pkg_handler(self, msg):
        if self.protocol == 'novatel':
            # print(msg)
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
                    print('error parsing novatel,', phr)
                    # raise e
                    return
                if not r:
                    return
                r['source'] = self.source
                ret.append(r)
                self.filehandler.insert_raw((r['ts'], r['source'] + '.{}'.format(r['type']), phr))
            return self.channel, ret, self.source

    def run(self):
        pid = os.getpid()
        print('sink {} pid:'.format(self.source), pid)
        time0 = time.time()
        self._init_port()
        pt_sum = 0
        next_check = 0
        self.pid = os.getpid()
        last_ts = 0
        msg_cnt = 0
        throuput = 0
        # if 'can' in self.type:
        #     print(self.type, 'start.')
        while not self.exit.is_set():

            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue
            t0 = time.time()
            msg_cnt += 1
            # throuput += len(buf)
            r = self.pkg_handler(buf)
            if r is not None:
                if isinstance(r[1], dict):
                    r[1]['ts_arrival'] = t0
                elif isinstance(r[1], list):
                    for item in r[1]:
                        item['ts_arrival'] = t0
                else:
                    print(r)
                if not self.queue.full():
                    self.queue.put((r))
                else:
                    time.sleep(0.001)
                    continue

        print('sink', self.source, 'exit.')


class PinodeSink(NNSink):
    def __init__(self, queue, ip, port, channel, index, resname, fileHandler, isheadless=False):
        super(PinodeSink, self).__init__(queue, ip, port, channel, index, isheadless)
        # print('pi_node connected.', ip, port, channel, index)
        self.source = 'rtk.{:d}'.format(index)
        self.index = index
        self.context = {'source': self.source}
        self.resname = resname
        self.fileHandler = fileHandler
        self.type = 'pi_sink'
        print('inited pi_node sink res:', resname)
        if resname == 'rtcm':
            self.rtcm3 = rtcm3.RTCM3()
        self._buf = b''
        # elif resname == 'pim222':
        #     print('pim222 sodes')
        # print(queue, ip, port, channel, index, resname, fileHandler, isheadless)
        self.ctx = {}

    def pkg_handler(self, msg):
        # if self.resname == 'pim222':
        # print(self.resname, '-----------------------------------------hahahahha')

        msg = memoryview(msg).tobytes()
        if self.resname == 'pim222':
            from parsers.pim222 import parse_pim222
            source = 'pim222.{}'.format(self.index)
            if not msg.startswith(b'$'):
                return
            # print('pim222 pkg handler')
            self.fileHandler.insert_raw((time.time(), source, msg.decode().strip()))
            r = parse_pim222(None, msg, self.ctx)
            if r:
                r['source'] = source
                # print(r)
                return self.channel, r, source
        # print(self.resname, msg)
        data = self.decode_pinode_res(self.resname, msg)
        if not data:
            return

        if not isinstance(data, list):
            data = [data]

        for r in data:
            # print(r)
            r['source'] = self.source
            if r.get('sensor') == 'm8n':
                r['source'] = 'gps.{:d}'.format(self.index)
            if r['type'] in ub482_defs:
                # print(r)
                if self.fileHandler.is_recording:
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
                # print(r)
                self.fileHandler.insert_raw((time.time(), r['source'], msg.decode().strip()))
                # print(time.time(), r['ts_origin'])

        return self.channel, data, self.source

    # def read(self):
        # if self.resname == 'pim222':
        #     print('--------------------------------------------------------------pim222')
        # bs = self._socket.recv(2048)  # flags=nnpy.DONTWAIT
        # return bs

    def decode_pinode_res(self, resname, msg):
        if resname == 'rtk':
            results = json.loads(msg.decode())
            for res in results:
                if res['type'] == 'novatel-like':
                    # print(msg)
                    ret = []
                    phr = res['buf']
                    if len(phr) > 0:
                        # print('phrase', phr)
                        try:
                            r = parsers_dict['novatel'](None, phr, None)
                            if r:
                                # print(r)
                                r['source'] = 'rtk.{}'.format(self.index)
                                self.fileHandler.insert_raw((r['ts'], r['source'] + '.{}'.format(r['type']), phr))
                                ret.append(r)
                                # print(r)
                        except Exception as e:
                            print('error decoding novatel-like:', phr)
                            # raise e

                    # print(ret)

                    return ret
                    # except Exception as e:
                    #     print('parsing novatel-like msg error:', res['buf'])

            return results

        elif resname == 'rtcm':
            self.rtcm3.add_data(msg)
            result = self.rtcm3.process_data(dump_decoded=False)
            r = None
            while result != 0:
                #        print str(datetime.now())
                if result == rtcm3.Got_Undecoded:
                    # if rtcm3.Dump_Undecoded:
                    # print("Undecoded Data in RTCM.")
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


class PinodeSinkGeneral(NNSink):
    def __init__(self, queue, ip, port, channel, index, resname, fileHandler, isheadless=False):
        super(PinodeSinkGeneral, self).__init__(queue, ip, port, channel, index, isheadless)
        # print('pi_node connected.', ip, port, channel, index)
        self.source = 'rtk.{:d}'.format(index)
        self.index = index
        self.context = {'source': self.source}
        self.resname = resname
        self.fileHandler = fileHandler
        self.type = 'pi_sink'
        if resname == 'rtcm':
            self.rtcm3 = rtcm3.RTCM3()
        # print(queue, ip, port, channel, index, resname, fileHandler, isheadless)

    def pkg_handler(self, msg):
        # print('-----------------------------------------hahahahha')

        msg = memoryview(msg).tobytes()
        # print(self.resname, msg)
        data = self.decode_pinode_res(self.resname, msg)
        if not data:
            return

        if not isinstance(data, list):
            data = [data]

        for r in data:
            # print(r)
            r['source'] = self.source
            if r.get('sensor') == 'm8n':
                r['source'] = 'gps.{:d}'.format(self.index)
            if r['type'] in ub482_defs:
                # print(r)
                if self.fileHandler.is_recording:
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
                # print(r)
                self.fileHandler.insert_raw((time.time(), r['source'], msg.decode().strip()))
                # print(time.time(), r['ts_origin'])

        return self.channel, data, self.source

    def decode_pinode_res(self, resname, msg):
        if resname == 'rtk':
            results = json.loads(msg.decode())
            for res in results:
                if res['type'] == 'novatel-like':
                    ret = []
                    for phr in res['buf'].split('#'):
                        if len(phr) > 0:
                            # print('phrase', phr)
                            r = parsers_dict['novatel'](None, '#'+phr, None)
                            if r:
                                ret.append(r)
                    # print(ret)

                    return ret

            return results

        elif resname == 'rtcm':
            self.rtcm3.add_data(msg)
            result = self.rtcm3.process_data(dump_decoded=False)
            r = None
            while result != 0:
                #        print str(datetime.now())
                if result == rtcm3.Got_Undecoded:
                    # if rtcm3.Dump_Undecoded:
                    # print("Undecoded Data in RTCM.")
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
    can-fd设备有四个can端口，需做区分处理
    """
    def __init__(self, queue, ip, port, can_list, index, fileHandler, isheadless=False, device=""):
        super(CANCollectSink, self).__init__(queue, ip, port, "can", index, isheadless)
        self.type = 'can_collect_sink'
        self.device = device
        self.fileHandler = fileHandler
        self.can_list = can_list                  # 四个端口的信号类型列表
        self.parser = {}
        for ch in can_list:
            t = can_list[ch]
            self.parser[t["dbc"]] = parsers_dict.get(t["dbc"], parsers_dict["default"])
        print('CANCollectSink initialized.', self.type, ip, port)

        self.source = []
        self.context = {}
        self.log_types = {}
        self.parse_event = Event()
        self.parse_event.set()

        self.init_env()

    def init_env(self):
        # 根据传入四个端口信号进行初始化相关环境
        for i, ch in self.can_list:
            t = self.can_list[ch]
            source = '{}.{}.{}.{}'.format(t.get("origin_device", self.device), self.index, ch, t["dbc"])
            self.log_types["can{}".format(i)] = source                                          # 写入日志的信号名
            self.context[source] = {"source": "{}.{}".format(t["dbc"], self.index)}           # 解析用的变量空间
            self.source.append(source)              # 来源列表

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        if not msg:
            return
        channel = msg[0]
        can_id = struct.unpack('<i', msg[1:5])[0]
        timestamp = struct.unpack('<d', msg[5:13])[0]
        data = msg[13:]

        log_type = self.log_types.get("can{}".format(channel))
        self.fileHandler.insert_raw((timestamp, log_type, '0x%x' % can_id + ' ' + data.hex()))

        if not self.parse_event.is_set():
            return

        msg_type = self.can_list[channel]["topic"]
        parser = self.parser[msg_type]
        source = self.source[channel]
        ret = parser(can_id, data, self.context[source])
        if ret is None:
            return None

        if isinstance(ret, list):
            for obs in ret:
                obs['ts'] = timestamp
        else:
            ret['ts'] = timestamp
        return can_id, ret, self.context[source]["source"]


class CANSink(NNSink):
    def __init__(self, queue, ip, port, channel, type, index, fileHandler, isheadless=False):
        super(CANSink, self).__init__(queue, ip, port, channel, index, isheadless)
        self.fileHandler = fileHandler
        self.parser = []
        for ptype in parsers_dict:
            if ptype in type:
                self.parser.append(parsers_dict[ptype])

        if self.isheadless:
            self.parser = []

        if len(self.parser) == 0:
            self.parser = [parsers_dict["default"]]
        self.stat = {}
        print('CANSink initialized.', self.type, ip, port, self.parser[0].__name__)

        self.temp_ts = {'CAN1': 0, 'CAN2': 0}
        self.source = '{}.{:d}'.format(type[0], index)
        self.context = {'source': self.source}
        # self.parse_switch = Value('i', 1)
        self.buf = deque(maxlen=2000)
        self.parse_event = Event()
        self.type = 'can_sink'
        self.parse_event.set()
        self.log_types = {'can0': 'CAN' + '{:01d}'.format(self.index * 2),
                          'can1': 'CAN' + '{:01d}'.format(self.index * 2 + 1)}
        self.log_type = self.log_types.get(self.cls)
        # self.log_type = '{}.{}'.format(self.cls, self.index)

    # def read(self):
    #     msg = nanomsg.wrapper.nn_recv(self._socket, 0)[1]
    #     # msg = self._socket.recv()
    #     msg = memoryview(msg).tobytes()
    #     dlc = msg[3]
    #     # print(dlc)
    #     can_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
    #     timestamp, = struct.unpack('<d', msg[8:16])
    #     data = msg[16:]
    #     return can_id, timestamp, data

    # def disable_parsing(self):
    #     self.parse_switch.value = 0
    #
    # def enable_parsing(self):
    #     self.parse_switch.value = 1

    def pkg_handler(self, msg):

        # lst = time.time()
        # can_id, timestamp, data = msg
        msg = memoryview(msg).tobytes()
        # dlc = msg[3]
        # print(dlc)
        # msg = msg.decode()
        can_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)

        # can_id = struct.unpack('<I', msg[4:8])
        timestamp = struct.unpack('<d', msg[8:16])[0]
        data = msg[16:]
        id = '0x%x' % can_id
        # print(data)

        # print('can', id)
        # if self.cls == 'can0':
        #     log_type = 'CAN' + '{:01d}'.format(self.index * 2)
        # else:
        #     log_type = 'CAN' + '{:01d}'.format(self.index * 2 + 1)
        log_type = self.log_type
        # log_bytes = ' '.join(['{:02X}'.format(d) for d in data])
        log_bytes = data.hex()
        # print('CAN sink save raw.', self.source)
        self.fileHandler.insert_raw((timestamp, log_type, id + ' ' + log_bytes))
        # if can_id == 0x7fe:  # timestamp sync test
        #     self.temp_ts[log_type] = timestamp
        #     if self.temp_ts['CAN2'] != 0 and self.temp_ts['CAN1'] != 0:
        #         dt = self.temp_ts['CAN1'] - self.temp_ts['CAN2']
        #         self.temp_ts['CAN2'] = 0
        #         self.temp_ts['CAN1'] = 0
        #         print('dt: {:2.05f}s'.format(dt))

        # if self.parse_switch.value == 0:
        #     return
        # self.buf.append((can_id, data))
        if not self.parse_event.is_set():
            return
        # else:
        #     self.parse_event.clear()
        #     # r = None
        # ret = []
        #     # print(parser)
        # for i in range(len(self.buf)):
        #     can_id, data = self.buf.popleft()
        #     for parser in self.parser:
        #         r = parser(can_id, data, self.context)
        #         if r is not None:
        #             if isinstance(r, list):
        #                 for obs in r:
        #                     obs['ts'] = timestamp
        #                     obs['source'] = self.source
        #                 ret.extend(r)
        #             elif isinstance(r, dict):
        #                 r['ts'] = timestamp
        #                 r['source'] = self.source
        #                 ret.append(r)
        #             break
        for parser in self.parser:
            ret = parser(can_id, data, self.context)
            # print(r)
            if ret is None:
                return None
            # print("data:", data)
            if isinstance(ret, list):
                # print('r is list')
                for obs in ret:
                    obs['ts'] = timestamp
                    obs['source'] = self.source
                    # print(obs)
            else:
                # print('r is not list')
                ret['ts'] = timestamp
                ret['source'] = self.source
                # print(r['source'])
            # print(r)
            return can_id, ret, self.source


class GsensorSink(NNSink):
    def __init__(self, queue, ip, port, channel, index, fileHandler, isheadless=False):
        super(GsensorSink, self).__init__(queue, ip, port, channel, index, isheadless)
        self.fileHandler = fileHandler
        self.type = 'gsensor_sink'

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        gyro = [0, 0, 0]
        accl = [0, 0, 0]
        # print(len(msg[16:]))
        # timestamp, = struct.unpack('<d', msg[8:16])
        timestamp, gyro[0], gyro[1], gyro[2], accl[0], accl[1], accl[2], temp, sec, usec = struct.unpack(
            '<dhhhhhhhII', msg[8:])
        temp = temp / 340 + 36.53
        # print('gsensor', timestamp, 'gyro:', gyro, 'accl:', accl, temp, sec, usec)
        self.fileHandler.insert_raw((timestamp, 'Gsensor.{}'.format(self.index),
                                     '{} {} {} {} {} {} {:.6f} {}'.format(accl[0], accl[1], accl[2], gyro[0], gyro[1],
                                                                          gyro[2], temp, sec, usec)))


class CameraSink(NNSink):
    def __init__(self, queue, ip, port, channel, index, fileHandler, headless=False, is_main=False, devname=None):
        super(CameraSink, self).__init__(queue, ip, port, channel, index, headless)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.headless = headless
        # self.index = index
        self.source = '{:s}.{:d}'.format(devname, index)
        self.is_main = is_main
        self.devname = devname
        self.type = 'cam_sink'


    def pkg_handler(self, msg):
        # print('cprocess-id:', os.getpid())
        t0 = time.time()
        msg = memoryview(msg).tobytes()
        jpg = msg[16:]
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        df = frame_id - self.last_fid
        if df != 1:
            # print("\r{} frame jump at {}".format(df - 1, frame_id), 'in', self.source, end='')
            pass
        self.last_fid = frame_id
        app1 = jpg.find(b'\xff\xe1')
        frame_id_jfif = int.from_bytes(jpg[24:28], byteorder="little")
        # print(app1, frame_id_jfif)
        timestamp, = struct.unpack('<d', msg[8:16])

        # logging.debug('cam id {}'.format(frame_id))
        # print('frame id', frame_id)

        r = {'ts': timestamp, 'type': 'video', 'img': jpg, 'frame_id': frame_id, 'source': self.source,
             'is_main': self.is_main, 'device': self.devname}
        self.fileHandler.insert_jpg(r)
        # print('frame id', frame_id)
        # self.fileHandler.insert_raw((timestamp, 'camera', '{}'.format(frame_id)))
        # dt = time.time() - t0
        # print('camera sink pkg handling cost: {:.2f}ms'.format(dt*1000))

        return frame_id, r, self.source


class FlowSink(NNSink):
    def __init__(self, cam_queue, msg_queue, ip, port, channel, index, fileHandler, protocol='msgpack', name='x1_algo',
                 log_name='pcv_log', topic='pcview', isheadless=False, is_main=False):
        super(FlowSink, self).__init__(cam_queue, ip, port, channel, index, isheadless)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.ip = ip
        self.port = port
        self.cam_queue = cam_queue
        self.msg_queue = msg_queue
        self.protocol = protocol
        self.log_name = log_name
        self.is_main = is_main
        self.type = 'flow_sink'
        self.topic = topic
        self.source = name + '.{:d}'.format(index)
        self.new_a1j = False        # 做个兼容处理，新的a1j不需要进行msgpack.unpack

    async def _run(self):
        print("FlowSink Initialized", self.ip, self.port, self.topic)
        session = aiohttp.ClientSession()
        URL = 'ws://' + str(self.ip) + ':' + str(self.port)
        async with session.ws_connect(URL) as ws:
            msg = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': self.topic,
            }

            msg_finish = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': 'finish'
            }

            msg_imu = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': 'imuinfo'
            }

            msg_lane = {
                'source': 'lane_profiling',
                'topic': 'subscribe',
                'data': 'lane_profiling_data'
            }
            data = msgpack.packb(msg)
            await ws.send_bytes(data)
            # data = msgpack.packb(msg_finish)
            # await ws.send_bytes(data)
            # data = msgpack.packb(msg_imu)
            # await ws.send_bytes(data)
            # data = msgpack.packb(msg_lane)
            # await ws.send_bytes(data)
            async for msg in ws:
                r = self.pkg_handler(msg)
                if r is not None:
                    if isinstance(r[0], type("")):
                        if 'x1_data' in r[0]:
                            self.msg_queue.put((r[1]['frame_id'], r[1], r[0]))
                        elif 'calib_param' in r[0]:
                            self.msg_queue.put((r[1]['frame_id'], r[1], self.source))
                            # print(self.source)
                    else:
                        self.cam_queue.put((*r, self.cls))
                else:
                    time.sleep(0.001)

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
            print(bcl.FAIL+'error:'+ str(e) + ' when initiating flow sink on'+bcl.ENDC, self.ip, self.port)
            # raise (e)

    def pkg_handler(self, msg):
        # 判断是否新的a1j设备，如果是新a1j设备的话不需要进行解码处理
        if not self.new_a1j:
            try:
                data = msgpack.unpackb(msg.data)
            except Exception as e:
                self.new_a1j = True
                data = msg.data
        else:
            data = msg.data

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
                 'is_main': self.is_main, 'transport': 'libflow'}
            self.fileHandler.insert_jpg(r)
            # self.fileHandler.insert_raw((ts, 'camera', '{}'.format(frame_id)))
            return frame_id, r

        if self.topic == "*":
            # Q3华为mdc特殊处理数据
            data["origin-source"] = data["source"]
            data["source"] = self.source
            data["data"] = base64.b64encode(data["data"]).decode('utf-8')
            self.fileHandler.insert_pcv_raw(data)
            return

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
                # topic = 'finish'
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
                        # print(calib_params)
                        r = {'type': 'calib_param', 'source': self.source, 'ts': 0, 'frame_id': calib_params['frame_id']}
                        r.update(calib_params['calib_param'])
                        # print(r)
                        return 'calib_param', r
                elif payload.startswith(b'\xff\x03'):  # jpeg pack header
                    # print(payload)
                    frame_id = int.from_bytes(payload[4:8], byteorder='little', signed=False)
                    # if frame_id - self.last_fid != 1:
                    #     print("frame jump at", self.last_fid, frame_id, 'in', self.source)
                    self.last_fid = frame_id
                    ts = int.from_bytes(payload[16:24], byteorder='little', signed=False)
                    ts = ts / 1000000
                    jpg = payload[24:]
                    if msg.type in (aiohttp.WSMsgType.CLOSED,
                                    aiohttp.WSMsgType.ERROR):
                        return None

                    r = {'ts': ts, 'img': jpg, 'frame_id': frame_id, 'type': 'video', 'source': self.source,
                         'is_main': self.is_main, 'transport': 'libflow'}
                    self.fileHandler.insert_jpg(r)
                    # self.fileHandler.insert_raw((ts, 'camera', '{}'.format(frame_id)))
                    return frame_id, r
            elif topic == "video":
                frame_id = int.from_bytes(payload[4:8], byteorder='little', signed=False)
                # if frame_id - self.last_fid != 1:
                #     print("frame jump at", self.last_fid, frame_id, 'in', self.source)
                self.last_fid = frame_id
                ts = int.from_bytes(payload[16:24], byteorder='little', signed=False)
                ts = ts / 1000000
                jpg = payload[24:]
                if msg.type in (aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR):
                    return None

                r = {'ts': ts, 'img': jpg, 'frame_id': frame_id, 'type': 'video', 'source': self.source,
                     'is_main': self.is_main, 'transport': 'libflow'}
                self.fileHandler.insert_jpg(r)
                # self.fileHandler.insert_raw((ts, 'camera', '{}'.format(frame_id)))
                return frame_id, r
            elif topic in ["radar_data", "fusion_data", "vehicle_data", "lane_data", "drive_data", "fusion_inject"]:
                r = {"source": self.source, "log_name": self.log_name, "buf": payload}
                self.fileHandler.insert_general_bin_raw(r)
        elif msg_src == 'lane_profiling':
            if topic == 'lane_profiling_data':
                r = {'type': 'algo_debug', 'source': self.source, 'log_name': self.log_name}
                r['buf'] = payload
                self.fileHandler.insert_general_bin_raw(r)
                return 'algo_debug', r
        elif msg_src == 'imu':
            if topic == 'imuinfo':
                imu_info = msgpack.unpackb(payload)
                # print(imu_info)
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
                # print(imu_info)
                for idx in range(imu_info['data_count']):
                    d = imu_info['imu_info'][idx]
                    ts = d['timestamp'] / 1000000
                    # rtos_tick = d['rtostick']
                    self.fileHandler.insert_raw((ts, self.source + '.gsensor', '{} {} {} {} {} {} {} {}'.format(
                        d['accel'][0], d['accel'][1], d['accel'][2],
                        d['gyro'][0], d['gyro'][1], d['gyro'][2],
                        d['temp'], int(ts), 1000000 * (ts - int(ts)))))
                return

        else:  # msg_src == 'pcview'
            # buf = msgpack.unpackb(payload)
            pass

        # elif b'calib_params' in buf:
        #     buf = msgpack.unpackb(buf)
        #     data = buf['calib_params']
        #     buf = msgpack.packb(data, use_bin_type=True)
        #     print(buf)
        #     self.fileHandler.insert_fusion_raw(buf)
        # return 'fusion_data', data

        if b'frame_id' in payload:
            # print(data['source'], data['topic'])
            payload = msgpack.unpackb(payload)
            if b'ultrasonic' in payload:
                payload[b'ultrasonic'][b'can_data'] = [x for x in payload[b'ultrasonic'][b'can_data']]

            pcv = mytools.convert(payload)

            # cv22_algo_data
            if 'data' in pcv and 'key' in pcv:
                pcv[pcv['key']] = pcv['data']
                pcv.pop('data')
                pcv.pop('key')

            pcv['source'] = self.source
            pcv['type'] = 'pcv_data'
            pcv['ts'] = ts
            # print(pcv)
            # data = json.dumps(pcv)
            self.fileHandler.insert_pcv_raw(pcv)

            if not self.is_main:
                return None

            return 'x1_data', pcv, self.source


class ProtoSink(NNSink):
    def __init__(self, cam_queue, msg_queue, ip, port, channel, index, fileHandler, protocol='msgpack', name='proto',
                 log_name='proto_log', topic='pcview', isheadless=False, is_main=False):
        super(ProtoSink, self).__init__(cam_queue, ip, port, channel, index, isheadless)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.ip = ip
        self.port = port
        self.cam_queue = cam_queue
        self.msg_queue = msg_queue
        self.protocol = protocol
        self.log_name = log_name
        self.is_main = is_main
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


class RTKSink(NNSink):

    def __init__(self, queue, ip, port, msg_type, index, fileHandler, isheadless=False):
        NNSink.__init__(self, queue, ip, port, msg_type, index, isheadless)
        self.fileHandler = fileHandler
        self.source = 'drtk'

    def _init_port(self):
        # self._socket = can.interface.Bus()
        try:
            self._socket = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=1000000)
            self.v1msg = V1_msg()
        except Exception as e:
            self._socket = None

    def can_send(self, bus, buf):
        idx = int(len(buf) / 8)
        last_dlc = len(buf) % 8

        for i in range(idx):
            msg = can.Message(arbitration_id=0xc6, data=[x for x in buf[i * 8:i * 8 + 8]], extended_id=False)
            bus.send(msg)
        msg = can.Message(arbitration_id=0xc6, data=[x for x in buf[-last_dlc:]], extended_id=False)
        bus.send(msg)

    def read(self):
        if self._socket:
            r = self._socket.recv(128)
            if r:
                return r.data

    def write(self, data):
        if self._socket:
            self.can_send(self._socket, data)

    def pkg_handler(self, msg):
        timestamp = time.time()
        # timestamp =
        self.v1msg.push(bytes(msg))
        # print(msg)
        while not self.v1msg.unpacked.empty():
            msg = self.v1msg.unpacked.get()
            msgid = msg['cmdSet'] << 8 | msg['cmdID']
            if msgid in v1_handlers:
                r = v1_handlers[msgid](msg, self.write)
                if r is not None:
                    r['ts'] = timestamp
                    self.fileHandler.insert_raw((timestamp, 'rtksol0',
                                                 '{} {} {:.8f} {:.8f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}'.format(
                                                     r['rtkst'], r['orist'], r['lat'], r['lon'], r['hgt'], r['velN'],
                                                     r['velE'], r['velD'], r['yaw'], r['pitch'], r['length'])))
                    self.fileHandler.insert_raw(
                        (timestamp, 'rtkdop0', '{} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(
                            r['sat'][0], r['sat'][1], r['sat'][2], r['sat'][3], r['sat'][4], r['sat'][5], r['gdop'],
                            r['pdop'], r['hdop'], r['htdop'], r['tdop'], r['cutoff'], r['trkSatn'], r['prn']
                        )))
                    return msgid, r, self.source
            else:
                # print('0x{:04x}'.format(msgid), msg)
                pass
