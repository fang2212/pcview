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

from collections import deque
from multiprocessing import Value, Event
from threading import Thread

from parsers import ublox, rtcm3
from parsers.drtk import V1_msg, v1_handlers
from parsers.parser import parsers_dict
from recorder.convert import *
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
    def __init__(self, ip, port, msg_type, index=0, sink_process=None):
        super().__init__()
        self.daemon = True  # 设置为守护线程
        self.ip = ip
        self.port = port
        self.msg_type = msg_type
        self.index = index
        self.sink_process=sink_process
        self.source = 'sink.{}'.format(index)
        self.exit = Event()

        self.pid = None  # 进程id

    def run(self):
        self.pid = os.getpid()
        logger.debug(f'sink {self.source} pid: {self.pid}')
        self.task()

    def task(self):
        pass

    def _init_port(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self.ip, self.port))

    def read(self):
        bs = self._socket.recv(66666)
        return bs

    def close(self):
        self.exit.set()
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
    def __init__(self, ip, port, msg_type, index=0, sink_process=None):
        super().__init__(ip=ip, port=port, msg_type=msg_type, sink_process=sink_process)
        self.ip = ip
        self.port = port
        self.type = msg_type
        self.index = index
        self.sink_process=sink_process
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
        while not self.exit.is_set():

            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue
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
                self.sink_process.put_decode((r))


class ZmqSink(Sink):
    def __init__(self, ip, port, msg_type, index, fileHandler, sink_process=None):
        super().__init__(ip=ip, port=port, msg_type=msg_type, sink_process=sink_process)
        self.ip = ip
        self.port = port
        self.msg_type = msg_type
        self.source = '{}.{:d}'.format(msg_type, index)
        self.index = index
        self.fileHandler = fileHandler
        self.sink_process = sink_process
        self.ctx = dict()
        self._buf = b''
        self.context = None

    def _init_port(self):
        self.context = zmq.Context()
        self._socket = self.context.socket(zmq.SUB)
        url = "tcp://%s:%d" % (self.ip, self.port)

        self._socket.connect(url)

    def read(self):
        bs = self._socket.recv()
        return bs

    def pkg_handler(self, msg):
        if self.msg_type == 'j2_zmq':
            data = {'type': self.msg_type, 'source': self.source, 'log_name': self.source, 'buf': msg}
            self.fileHandler.insert_general_bin_raw(data)
            return data

    def task(self):
        self._init_port()
        msg_cnt = 0
        while not self.exit.is_set():
            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue
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

                self.sink_process.put_decode((r))


class UDPSink(Sink):
    def __init__(self, ip, port, topic, protocol, index, file_andler, sink_process=None):
        super(UDPSink, self).__init__(ip=ip, port=port, msg_type=topic, sink_process=sink_process)
        self.ip = ip
        self.port = port
        self.msg_type = topic
        self.sink_process = sink_process
        self.source = '{}.{:d}'.format(topic, index)
        self.index = index
        self.fileHandler = file_andler
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
        if self.msg_type == "d1_udp":
            timestamp = time.time()
            r = {'type': self.msg_type, 'source': self.source, 'log_name': self.source, 'buf': msg}
            self.fileHandler.insert_general_bin_raw(r)
            self.fileHandler.insert_raw((timestamp, self.source, str(len(msg))))
        elif self.msg_type == 'q4_100':

            # no timestamp , use local timestamp
            timestamp = time.time()
            msg = struct.pack("<d", timestamp) + msg

            r = {'type': self.msg_type, 'source': self.source, 'log_name': self.source, 'buf': msg}
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
                self.sink_process.put_decode((r))


class TCPSink(Sink):
    def __init__(self, ip, port, msg_type, protocol, index, fileHandler, sink_process=None):
        super(TCPSink, self).__init__(ip=ip, port=port, msg_type=msg_type, sink_process=sink_process)
        self.ip = ip
        self.port = port
        self.msg_type = msg_type
        self.sink_process = sink_process
        self.source = 'tcp.{:d}'.format(index)
        self.index = index
        self.filehandler = fileHandler
        self.protocol = protocol
        self.ctx = dict()
        self._buf = b''
        self.exit = Event()

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
                self.sink_process.put_decode((r))


class PinodeSink(NNSink):
    def __init__(self, ip, port, msg_type, index, resname, fileHandler, sink_process=None):
        super().__init__(ip=ip, port=port, index=index, msg_type=msg_type, sink_process=sink_process)
        self.source = 'rtk.{:d}'.format(index)
        self.msg_type = msg_type
        self.index = index
        self.context = {'source': self.source}
        self.resname = resname
        self.fileHandler = fileHandler
        self.sink_process = sink_process
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
            self.sink_process.put_decode({"data": decode_msg})
            return

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


class CANSink(NNSink):
    def __init__(self, ip, port, msg_type, type, index, fileHandler, sink_process=None):
        super().__init__(ip=ip, port=port, msg_type=msg_type, index=index, sink_process=sink_process)
        self.fileHandler = fileHandler                          # 日志对象
        self.sink_process = sink_process
        self.source = '{}.{:d}'.format(type[0], index)
        self.type = 'can_sink'
        self.log_types = {'can0': 'CAN' + '{:01d}'.format(self.index * 2),
                          'can1': 'CAN' + '{:01d}'.format(self.index * 2 + 1)}
        self.log_type = self.log_types.get(self.msg_type)
        self.parse_event = Event()
        self.parse_event.set()

        # 解析方法初始化
        self.parser = []
        for parser in parsers_dict:
            if parser in type:
                self.parser.append(parsers_dict[parser])
        if len(self.parser) == 0:
            self.parser = [parsers_dict["default"]]

        print('CANSink initialized.', self.type, ip, port, self.parser[0].__name__)

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
            "source": self.source,
            "data": data,
            "parsers": self.parser,
            "cid": can_id,
            "ts": timestamp
        }
        self.sink_process.put_decode(decode_msg)


class GsensorSink(NNSink):
    def __init__(self, ip, port, msg_type, index, fileHandler, sink_process=None):
        super(GsensorSink, self).__init__(ip=ip, port=port, msg_type=msg_type, index=index, sink_process=sink_process)
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
    def __init__(self, ip, port, msg_type, index, fileHandler, is_main=False, devname=None, sink_process=None):
        super(CameraSink, self).__init__(ip=ip, port=port, msg_type=msg_type, index=index, sink_process=sink_process)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.source = '{:s}.{:d}'.format(devname, index)
        self.is_main = is_main
        self.devname = devname
        self.type = 'cam_sink'

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        jpg = msg[16:]
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        self.last_fid = frame_id
        timestamp, = struct.unpack('<d', msg[8:16])

        r = {'ts': timestamp, 'type': 'video', 'img': jpg, 'frame_id': frame_id, 'source': self.source,
             'is_main': self.is_main, 'device': self.devname}
        self.fileHandler.insert_jpg(r)

        return frame_id, r, self.source


class FlowSink(NNSink):
    def __init__(self, ip, port, msg_type, index, fileHandler, name='x1_algo',
                 log_name='pcv_log', topic='pcview', is_main=False, sink_process=None):
        super().__init__(ip=ip, port=port, msg_type=msg_type, index=index, sink_process=sink_process)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.ip = ip
        self.port = port
        self.sink_process = sink_process
        self.log_name = log_name
        self.is_main = is_main
        self.type = 'flow_sink'
        self.topic = topic
        self.source = name + '.{:d}'.format(index)

    async def _run(self):
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
                r = self.pkg_handler(msg)
                if r is not None:
                    if isinstance(r[0], type("")):
                        if 'x1_data' in r[0]:
                            self.sink_process.put_decode((r[1]['frame_id'], r[1], r[0]))
                        elif 'calib_param' in r[0]:
                            self.sink_process.put_decode((r[1]['frame_id'], r[1], self.source))
                    else:
                        self.sink_process.put_decode((*r, self.msg_type))
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
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._run())
        except Exception as e:
            logger.error(f'error when initiating flow sink on {self.ip}:{self.port}, {e}')

    def pkg_handler(self, msg):
        data = msgpack.unpackb(msg.data)
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
                        r = {'type': 'calib_param', 'source': self.source, 'ts': 0, 'frame_id': calib_params['frame_id']}
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
                         'is_main': self.is_main, 'transport': 'libflow'}
                    self.fileHandler.insert_jpg(r)
                    return frame_id, r
                else:
                    pass
            else:
                # print(data)
                pass
        elif msg_src == 'lane_profiling':
            if topic == 'lane_profiling_data':
                r = {'type': 'algo_debug', 'source': self.source, 'log_name': self.log_name, 'buf': payload}
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
