import asyncio
import json
import struct
import time
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
import aionn

async_for_sink = True

try:
    import pynng

except Exception as e:
    nn_impl = 'nanomsg'
    # import nanomsg

nn_impl = 'aionn'
# import nanomsg

# import pynng
from parsers import ublox, rtcm3
from parsers.drtk import V1_msg, v1_handlers
from parsers.parser import parsers_dict
from recorder.convert import *
from tools import mytools
from collections import deque
from multiprocessing import Queue
import asyncio
import platform
import aionn


# async task manager
class AsyncManager(Thread):
    def __init__(self):
        super(AsyncManager, self).__init__()
        self.q = asyncio.Queue()
        self.loop = None

    def run(self) -> None:

        if platform.python_version() > "3.6":
            from tornado.platform.asyncio import AnyThreadEventLoopPolicy
            asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        try:
            self.loop.run_forever()
            # self.loop.run_until_complete(self._tasks())
        except Exception as e:
            print(e)
            print("init loop error")

    def add_task(self, task):
        # print("add task")
        # self.q.put(task)
        while self.loop is None: time.sleep(0.01)
        asyncio.run_coroutine_threadsafe(task, self.loop)


class Sink(object):
    def __init__(self, queue, ip, port, msg_type, index=0, isheadless=False):
        super(Sink, self).__init__()
        self.deamon = True
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

        elif nn_impl == 'aionn':
            self._socket = aionn.Socket(aionn.AF_SP, aionn.SUB)
            self._socket.connect(address)
            self._socket.setsockopt(aionn.SUB, aionn.SUB_SUBSCRIBE, '')

        else:
            # self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
            # nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
            # nanomsg.wrapper.nn_connect(self._socket, address)
            self._socket = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
            self._socket.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')
            self._socket.connect(address)

    async def read(self):
        # if nn_impl == 'pynng':
        #     try:
        #         bs = self._socket.recv()
        #     except Exception as e:
        #         return
        # else:
        #     # bs = nanomsg.wrapper.nn_recv(self._socket, 1)[1]
        # bs = self._socket.recv(2048)
        bs = await self._socket.recv()
        # print(self._socket.recv_buffer_size)
        return bs
        # return self._socket.recv()

    def _init_local_socket(self):
        self.ss = None

    async def run(self):
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

            buf = await self.read()
            if not buf:
                time.sleep(0.001)
                continue
            t0 = time.time()
            msg_cnt += 1
            # throuput += len(buf)

            try:
                r = self.pkg_handler(buf)
            except Exception as e:
                # print(e, buf[:10])
                print(self.source, "pkg error")
                continue
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


class TCPSink(Sink):
    def __init__(self, queue, ip, port, channel, protocol, index, fileHandler):
        super(TCPSink, self).__init__(queue, ip, port, channel, index, False)
        self.source = 'tcp.{:d}'.format(index)
        self.index = index
        self.filehandler = fileHandler
        self.protocol = protocol
        self.ctx = dict()

    def _init_port(self):
        print('connecting', self.dev, self.channel)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.dev, self.channel))

    async def read(self):
        return self._socket.recv(2048)

    def pkg_handler(self, msg):
        if self.protocol == 'novatel':
            # print(msg)
            parser = parsers_dict.get(self.protocol)
            if isinstance(msg, bytes):
                msg = msg.decode().strip()
            if parser:
                # if msg.count('\n') > 1:
                ret = []
                for phr in msg.split('\n'):
                    if len(phr) > 0:
                        # print('msg phrase', msg)
                        # print(phr)
                        try:
                            r = parser(None, phr, self.ctx)
                        except Exception as e:
                            print('error parsing novatel,', phr)
                            raise e
                        if not r:
                            return
                        r['source'] = self.source
                        ret.append(r)
                        # if len(msg) > 500:
                        #     print('novatel too long:', msg)
                        self.filehandler.insert_raw((r['ts'], r['source'] + '.{}'.format(r['type']), phr))
                # else:
                #     ret = parser(None, msg, self.ctx)
                #     if not ret:
                #         return
                #     ret['source'] = self.source
                #     self.filehandler.insert_raw((ret['ts'], ret['source'] + '.{}'.format(ret['type']), msg))
                # if isinstance(r, list):
                #     for res in r:
                #         res['source'] = self.source
                #         self.filehandler.insert_raw((res['ts'], res['source'] + '.{}'.format(res['type']), msg.decode().strip()))
                # else:
                #     r['source'] = self.source
                #     self.filehandler.insert_raw((r['ts'], r['source'] + '.{}'.format(r['type']), msg.decode().strip()))
                return self.channel, ret, self.source


class PinodeSink(Sink):
    def __init__(self, queue, ip, port, channel, index, resname, fileHandler, isheadless=False):
        super(PinodeSink, self).__init__(queue, ip, port, channel, index, isheadless)
        # print('pi_node connected.', ip, port, channel, index)
        self.source = 'rtk.{:d}'.format(index)
        self.index = index
        self.context = {'source': self.source}
        self.resname = resname
        self.fileHandler = fileHandler
        self.type = 'pi_sink'
        if resname == 'rtcm':
            self.rtcm3 = rtcm3.RTCM3()
        # print(queue, ip, port, channel, index, resname, fileHandler, isheadless, '------------------------------------------------------------')

    def pkg_handler(self, msg):
        # print('-----------------------------------------hahahahha')

        msg = memoryview(msg).tobytes()
        # print(self.resname, msg)
        if self.resname == 'pim222':
            # print('pim222 pkg handler')
            data = msg.decode()

            print(msg)
            return

        data = self.decode_pinode_res(self.resname, msg)
        # print(data)
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
                    for phr in res['buf'].split('\n'):
                        if len(phr) > 0:
                            # print('phrase', phr)
                            r = parsers_dict['novatel'](None, phr, None)
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


class PinodeSinkGeneral(Sink):
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
        # print('inited resname:', resname)
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
                            r = parsers_dict['novatel'](None, '#' + phr, None)
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


class CANSink(Sink):
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


class GsensorSink(Sink):
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


class CameraSink(Sink):
    def __init__(self, queue, ip, port, channel, index, fileHandler, headless=False, is_main=False, devname=None):
        super(CameraSink, self).__init__(queue, ip, port, channel, index, headless)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.headless = headless
        # self.index = index
        self.source = 'video.{:d}'.format(index)
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
            print("\r{} frame jump at {}".format(df - 1, frame_id), 'in', self.source, end='')
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


class FlowSink(Sink):
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

    async def run(self):
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
            # print(self.topic, data)
            async for msg in ws:
                # print(msg[:100])
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

    def pkg_handler(self, msg):
        # print(msg)
        # if self.protocol != 'msgpack':
        #     r = {'type': 'algo_debug', 'source': self.source, 'log_name': self.log_name}
        #     r['buf'] = msg.data
        #     data = msgpack.unpackb(msg.data)
        #     print(data)
        #     # print(msg)
        #     self.fileHandler.insert_general_bin_raw(r)
        #     return 'algo_debug', r

        data = msgpack.unpackb(msg.data)
        # print('-----', data[b'topic'])
        ts = time.time()
        topic = None
        # if 'topic' not in data:
        #     return
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
                pass
                #  print(payload[:10])

                if b'calib_param' in payload:
                    calib_params = msgpack.unpackb(payload)
                    calib_params = mytools.convert(calib_params)
                    if calib_params:
                        # print(calib_params)
                        r = {'type': 'calib_param', 'source': self.source, 'ts': 0,
                             'frame_id': calib_params['frame_id']}
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
                else:
                    # print('unknown payload begins with:', payload[:20])
                    pass
            else:
                # print(data)
                pass
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
            print(data)
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
            pcv['source'] = self.source
            pcv['type'] = 'algo_debug'
            pcv['ts'] = ts
            # data = json.dumps(pcv)
            self.fileHandler.insert_pcv_raw(pcv)
            return 'x1_data', pcv, self.source


class RTKSink(Sink):

    def __init__(self, queue, ip, port, msg_type, index, fileHandler, isheadless=False):
        Sink.__init__(self, queue, ip, port, msg_type, index, isheadless)
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

    async def read(self):
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

