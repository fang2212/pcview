from parsers.drtk import V1_msg, v1_handlers
from multiprocessing.dummy import Process as Thread
from multiprocessing import Process
import struct
import nanomsg
import logging
import can
from parsers.parser import parsers_dict
import json
import time

# logging.basicConfig函数对日志的输出格式及方式做相关配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class Sink(Process):
    def __init__(self, queue, ip, port, msg_type, index=0):
        Process.__init__(self)
        self.deamon = True
        self.dev = ip
        self.channel = port
        self.queue = queue
        self.type = msg_type
        self.index = index
        self.cls = msg_type
        if 'can' in msg_type:
            self.cls = 'can'
            print(self.type, 'start.')


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
            r = self.pkg_handler(buf)
            if r is not None:
                self.queue.put((*r, self.cls))

    def pkg_handler(self, msg_buf):
        pass


class PinodeSink(Sink):
    def __init__(self, queue, ip, port, channel, index, resname):
        super(PinodeSink, self).__init__(queue, ip, port, channel, index)
        print('pi_node connected.', ip, port, channel, index)
        self.source = 'rtk.{:d}'.format(index)
        self.context = {'source': self.source}
        self.resname = resname

    def pkg_handler(self, msg):
        # print('hahahahha')
        msg = memoryview(msg).tobytes()

        data = self.decode_pinode_res(self.resname, msg)
        if not data:
            return

        if isinstance(data, list):
            for r in data:
                r['source'] = self.source
        else:
            data['source'] = self.source
        # print(data)
        return self.channel, data

    def decode_pinode_res(self, resname, msg):
        if resname == 'rtk':
            return json.loads(msg.decode())
        elif resname == 'rtcm':
            return {'type': 'rtcm', 'len': len(msg)}


class CANSink(Sink):
    def __init__(self, queue, ip, port, channel, type, index, fileHandler):
        Sink.__init__(self, queue, ip, port, channel, index)
        self.fileHandler = fileHandler
        self.parser = []
        for ptype in parsers_dict:
            if ptype in type:
                self.parser.append(parsers_dict[ptype])
        if len(self.parser) == 0:
            self.parser = [parsers_dict["default"]]
        self.stat = {}
        print('CANSink initialized.', self.type, ip, port, self.parser)

        self.temp_ts = {'CAN1': 0, 'CAN2': 0}
        self.source = '{}.{:d}'.format(type[0], index)
        self.context = {'source': self.source}

    def read(self):
        msg = nanomsg.wrapper.nn_recv(self._socket, 0)[1]
        msg = memoryview(msg).tobytes()
        can_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        timestamp, = struct.unpack('<d', msg[8:16])
        data = msg[16:]
        return can_id, timestamp, data

    def pkg_handler(self, msg):
        can_id, timestamp, data = msg
        id = '0x%x' % can_id

        # print('can', id)
        if self.type == 'can0':
            log_type = 'CAN' + '{:01d}'.format(self.index * 2)
        else:
            log_type = 'CAN' + '{:01d}'.format(self.index * 2 + 1)
        log_bytes = ' '.join(['{:02X}'.format(d) for d in data])
        # print('CAN sink save raw.', self.source)
        self.fileHandler.insert_raw((timestamp, log_type, id + ' ' + log_bytes))
        # if not self.raw_queue.full():
        #     self.raw_queue.put((timestamp, log_type, id, log_bytes))

        if can_id == 0x7fe:
            # print(log_type, id, timestamp)
            self.temp_ts[log_type] = timestamp
            if self.temp_ts['CAN2'] != 0 and self.temp_ts['CAN1'] != 0:
                dt = self.temp_ts['CAN1'] - self.temp_ts['CAN2']
                self.temp_ts['CAN2'] = 0
                self.temp_ts['CAN1'] = 0
                print('dt: {:2.05f}s'.format(dt))
        # elif can_id == 0xc6:
        #     print(log_bytes)
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
    def __init__(self, queue, ip, port, channel, index, fileHandler):
        Sink.__init__(self, queue, ip, port, channel, index)
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
        self.fileHandler.insert_raw((timestamp, 'Gsensor',
                                '{} {} {} {} {} {} {:.6f} {}'.format(accl[0], accl[1], accl[2], gyro[0], gyro[1],
                                                                     gyro[2], temp, sec, usec)))



class CameraSink(Sink):

    def __init__(self, queue, ip, port, channel, fileHandler):
        Sink.__init__(self, queue, ip, port, channel)
        self.last_fid = 0
        self.fileHandler = fileHandler

    def pkg_handler(self, msg):
        # print('cprocess-id:', os.getpid())
        msg = memoryview(msg).tobytes()
        jpg = msg[16:]
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        if frame_id - self.last_fid != 1:
            print("frame jump.", self.last_fid, frame_id)
        self.last_fid = frame_id
        app1 = jpg.find(b'\xff\xe1')
        frame_id_jfif = int.from_bytes(jpg[24:28], byteorder="little")
        # print(app1, frame_id_jfif)
        timestamp, = struct.unpack('<d', msg[8:16])

        logging.debug('cam id {}'.format(frame_id))

        r = {'ts': timestamp, 'img': jpg, 'frame_id': frame_id}

        self.fileHandler.insert_raw((timestamp, 'camera', '{}'.format(frame_id)))

        return frame_id, r


class RTKSink(Sink):

    def __init__(self, queue, ip, port, msg_type, index, fileHandler):
        Sink.__init__(self, queue, ip, port, msg_type, index)
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
                    self.fileHandler.insert_raw((timestamp, 'rtksol0', '{} {} {:.8f} {:.8f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}'.format(
                        r['rtkst'], r['orist'], r['lat'], r['lon'], r['hgt'], r['velN'], r['velE'], r['velD'], r['yaw'], r['pitch'], r['length'])))
                    self.fileHandler.insert_raw((timestamp, 'rtkdop0', '{} {} {} {} {} {} {} {} {} {} {} {} {} {}'.format(
                        r['sat'][0], r['sat'][1], r['sat'][2], r['sat'][3], r['sat'][4], r['sat'][5], r['gdop'],
                        r['pdop'], r['hdop'], r['htdop'], r['tdop'], r['cutoff'], r['trkSatn'], r['prn']
                    )))
                    return msgid, r
            else:
                # print('0x{:04x}'.format(msgid), msg)
                pass