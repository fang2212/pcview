import asyncio
import json
import logging
import struct
import time
# from multiprocessing import Process
from threading import Thread

import aiohttp
import can
import msgpack

import nanomsg
from parsers import ublox, rtcm3
from parsers.drtk import V1_msg, v1_handlers
from parsers.parser import parsers_dict
from recorder.convert import *
from tools import mytools

# logging.basicConfig函数对日志的输出格式及方式做相关配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class Sink(Thread):
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
        if 'can' in msg_type:
            self.cls = 'can'
            # print(self.type, 'start.')

    def _init_port(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (self.dev, self.channel,))
        # self._socket = Socket(SUB)
        # self._socket.connect("tcp://%s:%s" % (self.dev, self.channel,))

    def read(self):
        bs = nanomsg.wrapper.nn_recv(self._socket, 0)[1]
        return bs
        # return self._socket.recv()

    def _init_local_socket(self):
        self.ss = None

    def run(self):
        self._init_port()
        # if 'can' in self.type:
        #     print(self.type, 'start.')
        while True:
            buf = self.read()
            if not buf:
                time.sleep(0.01)
                continue
            t0 = time.time()
            r = self.pkg_handler(buf)
            dt = time.time() - t0
            # print(self.dev, self.type, self.channel, 'dt: {:.5f}'.format(dt))
            if r is not None and not self.isheadless:
                self.queue.put((*r, self.cls))
            # time.sleep(0.01)

    def pkg_handler(self, msg_buf):
        pass


class SinkThread(Thread):
    def __init__(self, queue, ip, port, msg_type, index=0, isheadless=False):
        super(SinkThread, self).__init__()
        self.deamon = True
        self.dev = ip
        self.channel = port
        self.queue = queue
        self.type = msg_type
        self.index = index
        self.cls = msg_type
        self.isheadless = isheadless
        if 'can' in msg_type:
            self.cls = 'can'
            # print(self.type, 'start.')

    def _init_port(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (self.dev, self.channel,))
        # self._socket = Socket(SUB)
        # self._socket.connect("tcp://%s:%s" % (self.dev, self.channel,))

    def read(self):
        bs = nanomsg.wrapper.nn_recv(self._socket, 0)[1]
        return bs
        # return self._socket.recv()

    def _init_local_socket(self):
        self.ss = None

    def run(self):
        self._init_port()
        # if 'can' in self.type:
        #     print(self.type, 'start.')
        while True:
            buf = self.read()
            if not buf:
                time.sleep(0.001)
                continue
            t0 = time.time()
            r = self.pkg_handler(buf)
            dt = time.time() - t0
            # print(self.dev, self.type, self.channel, 'dt: {:.5f}'.format(dt))
            if r is not None and not self.isheadless:
                self.queue.put((*r, self.cls))
            # time.sleep(0.01)

    def pkg_handler(self, msg_buf):
        pass


class PinodeSink(Sink):
    def __init__(self, queue, ip, port, channel, index, resname, fileHandler, isheadless=False):
        super(PinodeSink, self).__init__(queue, ip, port, channel, index, isheadless)
        # print('pi_node connected.', ip, port, channel, index)
        self.source = 'rtk.{:d}'.format(index)
        self.index = index
        self.context = {'source': self.source}
        self.resname = resname
        self.fileHandler = fileHandler
        if resname == 'rtcm':
            self.rtcm3 = rtcm3.RTCM3()
        # print(queue, ip, port, channel, index, resname, fileHandler, isheadless)

    def pkg_handler(self, msg):
        # print('hahahahha')
        msg = memoryview(msg).tobytes()

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
                self.fileHandler.insert_raw((r['ts'], r['source'] + '.' + r['type'], compose_from_def(ub482_defs, r)))

            elif r['type'] == 'rtk':
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

        return self.channel, data

    def decode_pinode_res(self, resname, msg):
        if resname == 'rtk':
            return json.loads(msg.decode())
        elif resname == 'rtcm':
            self.rtcm3.add_data(msg)
            result = self.rtcm3.process_data(dump_decoded=False)
            r = None
            while result != 0:
                #        print str(datetime.now())
                if result == rtcm3.Got_Undecoded:
                    # if rtcm3.Dump_Undecoded:
                    print("Undecoded Data in RTCM.")
                elif result == rtcm3.Got_Packet:
                    r = self.rtcm3.dump(False, False, False, False)
                    # sys.stdout.flush()
                else:
                    print("INTERNAL ERROR: Unknown result (" + str(result) + ")")
                result = self.rtcm3.process_data()
            if r:
                r['type'] = 'rtcm'
                r['len'] = len(msg)
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

    def read(self):
        msg = nanomsg.wrapper.nn_recv(self._socket, 0)[1]
        msg = memoryview(msg).tobytes()
        dlc = msg[3]
        # print(dlc)
        can_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        timestamp, = struct.unpack('<d', msg[8:16])
        data = msg[16:]
        return can_id, timestamp, data

    def pkg_handler(self, msg):

        lst = time.time()

        can_id, timestamp, data = msg
        id = '0x%x' % can_id
        # print(data)

        # print('can', id)
        if self.type == 'can0':
            log_type = 'CAN' + '{:01d}'.format(self.index * 2)
        else:
            log_type = 'CAN' + '{:01d}'.format(self.index * 2 + 1)
        log_bytes = ' '.join(['{:02X}'.format(d) for d in data])
        # print('CAN sink save raw.', self.source)
        self.fileHandler.insert_raw((timestamp, log_type, id + ' ' + log_bytes))
        # if can_id == 0x7fe:  # timestamp sync test
        #     self.temp_ts[log_type] = timestamp
        #     if self.temp_ts['CAN2'] != 0 and self.temp_ts['CAN1'] != 0:
        #         dt = self.temp_ts['CAN1'] - self.temp_ts['CAN2']
        #         self.temp_ts['CAN2'] = 0
        #         self.temp_ts['CAN1'] = 0
        #         print('dt: {:2.05f}s'.format(dt))

        r = None
        for parser in self.parser:
            # print(parser)
            r = parser(can_id, data, self.context)
            if r is not None:
                break

        # print(r)
        if r is None:
            return None
        if isinstance(r, list):
            # print('r is list')
            for obs in r:
                obs['ts'] = timestamp
                obs['source'] = self.source
                # print(obs)
        else:
            # print('r is not list')
            r['ts'] = timestamp
            r['source'] = self.source
            # print(r['source'])
        # print(r)
        return can_id, r


class GsensorSink(Sink):
    def __init__(self, queue, ip, port, channel, index, fileHandler, isheadless=False):
        super(GsensorSink, self).__init__(queue, ip, port, channel, index, isheadless)
        self.fileHandler = fileHandler

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        gyro = [0, 0, 0]
        accl = [0, 0, 0]
        # print(len(msg[16:]))
        # timestamp, = struct.unpack('<d', msg[8:16])
        timestamp, gyro[0], gyro[1], gyro[2], accl[0], accl[1], accl[2], temp, sec, usec = struct.unpack(
            '<dhhhhhhhII', msg[8:])
        temp = temp / 340 + 36.53
        # print('gsensor', timestamp, 'gyro:', gyro,'accl:', accl, temp, sec, usec)
        self.fileHandler.insert_raw((timestamp, 'Gsensor.{}'.format(self.index),
                                     '{} {} {} {} {} {} {:.6f} {}'.format(accl[0], accl[1], accl[2], gyro[0], gyro[1],
                                                                          gyro[2], temp, sec, usec)))


class CameraSink(Sink):
    def __init__(self, queue, ip, port, channel, index, fileHandler, headless=False, is_main=False):
        super(CameraSink, self).__init__(queue, ip, port, channel, index, headless)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.headless = headless
        # self.index = index
        self.source = 'video.{:d}'.format(index)
        self.is_main = is_main

    def pkg_handler(self, msg):
        # print('cprocess-id:', os.getpid())
        msg = memoryview(msg).tobytes()
        jpg = msg[16:]
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        df = frame_id - self.last_fid
        if df != 1:
            print("\r{} frame jump at {}".format(df-1, frame_id), end='')
        self.last_fid = frame_id
        app1 = jpg.find(b'\xff\xe1')
        frame_id_jfif = int.from_bytes(jpg[24:28], byteorder="little")
        # print(app1, frame_id_jfif)
        timestamp, = struct.unpack('<d', msg[8:16])

        logging.debug('cam id {}'.format(frame_id))
        # print('frame id', frame_id)

        r = {'ts': timestamp, 'img': jpg, 'frame_id': frame_id, 'source': self.source, 'is_main': self.is_main}
        # print('frame id', frame_id)
        # self.fileHandler.insert_raw((timestamp, 'camera', '{}'.format(frame_id)))

        return frame_id, r


class FlowSink(Sink):

    def __init__(self, cam_queue, msg_queue, ip, port, channel, index, fileHandler, isheadless=False, is_main=False):
        super(FlowSink, self).__init__(cam_queue, ip, port, channel, index, isheadless)
        self.last_fid = 0
        self.fileHandler = fileHandler
        self.ip = ip
        self.port = port
        self.cam_queue = cam_queue
        self.msg_queue = msg_queue
        self.is_main = is_main
        self.source = 'video.{:d}'.format(index)

    async def _run(self):
        session = aiohttp.ClientSession()
        URL = 'ws://' + str(self.ip) + ':' + str(self.port)
        async with session.ws_connect(URL) as ws:
            msg = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': 'pcview',
            }

            msg_finish = {
                'source': 'pcview',
                'topic': 'subscribe',
                'data': 'finish'
            }
            data = msgpack.packb(msg)
            await ws.send_bytes(data)
            data = msgpack.packb(msg_finish)
            await ws.send_bytes(data)
            async for msg in ws:

                r = self.pkg_handler(msg)
                if r is not None:
                    if isinstance(r[0], type("")):
                        if 'x1_data' in r[0]:
                            self.msg_queue.put((r[1]['frame_id'], r[1], r[0]))
                    else:
                        self.cam_queue.put((*r, self.cls))

    def run(self):
        import asyncio
        from tornado.platform.asyncio import AnyThreadEventLoopPolicy
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run())

    def pkg_handler(self, msg):
        data = msgpack.unpackb(msg.data)
        # print('-----', data[b'topic'])
        if data[b'topic'] == b'finish':
            buf = data[b'data']
            if b'rc_fusion' in buf:
                buf = msgpack.unpackb(buf)
                data = buf[b'rc_fusion']
                buf = msgpack.packb(data, use_bin_type=True)
                self.fileHandler.insert_fusion_raw(buf)
            elif b'calib_params' in buf:
                buf = msgpack.unpackb(buf)
                data = buf[b'calib_params']
                buf = msgpack.packb(data, use_bin_type=True)
                self.fileHandler.insert_fusion_raw(buf)

            return 'fusion_data', data
        data = data[b'data']
        if b'frame_id' in data:
            data = msgpack.unpackb(data)
            pcv = mytools.convert(data)
            data = json.dumps(pcv)
            self.fileHandler.insert_pcv_raw(data)
            return 'x1_data', pcv

        frame_id = int.from_bytes(data[4:8], byteorder='little', signed=False)
        if frame_id - self.last_fid != 1:
            print("frame jump.", self.last_fid, frame_id)
        self.last_fid = frame_id
        ts = int.from_bytes(data[16:24], byteorder='little', signed=False)
        ts = ts / 1000000
        jpg = data[24:]
        if msg.type in (aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.ERROR):
            return None

        r = {'ts': ts, 'img': jpg, 'frame_id': frame_id, 'source': self.source, 'is_main': self.is_main}
        # self.fileHandler.insert_raw((ts, 'camera', '{}'.format(frame_id)))
        return frame_id, r


class RTKSink(Sink):

    def __init__(self, queue, ip, port, msg_type, index, fileHandler, isheadless=False):
        Sink.__init__(self, queue, ip, port, msg_type, index, isheadless)
        self.fileHandler = fileHandler

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
                    return msgid, r
            else:
                # print('0x{:04x}'.format(msgid), msg)
                pass
