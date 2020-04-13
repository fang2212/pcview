import os
import sys
import time
import nanomsg
import cv2
import numpy as np
import struct
from datetime import datetime
from multiprocessing import Process, Queue, freeze_support


class NanoClient(object):
    """nanomsg client bind
    nanomsg sub client类
    默认sub '' 即此端口所有topic
    """
    def __init__(self, ip, port, add_recv_ts=False):
        self.ip = ip
        self.port = port
        self.add_recv_ts = add_recv_ts
        self._socket = None

    def init(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB,
                                      nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket,
                                   "tcp://%s:%s" % (self.ip, self.port, ))

    def run(self, queue):
        while True:
            queue.put(self.recv(0))

    def recv(self, flags=1):
        """
        flags 0 blocking
        flags 1 unblocking
        """
        buf = nanomsg.wrapper.nn_recv(self._socket, flags)
        if self.add_recv_ts:
            ts = int(time.time()*1000000)
            return ts, buf[1]
        return buf[1]


class Pkg(object):
    """
    """
    @classmethod
    def can(cls, msg, msg_type=''):
        msg = memoryview(msg).tobytes()
        can_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        timestamp, = struct.unpack('<d', msg[8:16])
        data = msg[16:]
        return {
            'ts': timestamp,
            'can_id': can_id,
            'data': data,
            'msg_type': msg_type,
        }

    @classmethod
    def gsensor(cls, msg, msg_type=''):
        msg = memoryview(msg).tobytes()
        gyro = [0, 0, 0]
        accl = [0, 0, 0]
        timestamp, gyro[0], gyro[1], gyro[2], \
        accl[0], accl[1], accl[2], \
        temp, sec, usec = struct.unpack('<dhhhhhhhII', msg[8:])
        temp = temp / 340 + 36.53
        return {
            'ts': timestamp,
            'accl': accl,
            'gyro': gyro,
            'temp': temp,
            'sec': sec,
            'usec': usec,
            'msg_type': msg_type
        }

    @classmethod
    def camera(self, msg, msg_type=''):
        msg = memoryview(msg).tobytes()
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        timestamp, = struct.unpack('<d', msg[8:16])
        data = msg[16:]
        image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
        return {
            'ts': timestamp,
            'fid': frame_id,
            'image': image,
            'msg_type': msg_type
        }


class NanoGroup(Process):

    def __init__(self, continue_size=100):
        Process.__init__(self)
        self.group = []
        self.continue_size = continue_size

    def add_sink(self, sink):
        client = NanoClient(sink['ip'], sink['port'], sink['add_recv_ts'])
        sink['client'] = client
        self.group.append(sink)

    def init_all(self):
        for sink in self.group:
            sink['client'].init()

    def run(self):
        self.init_all()
        while True:
            for sink in self.group:
                client, pkg, queue = sink['client'], sink['pkg'], sink['queue']
                size = self.continue_size
                while size:
                    size -= 1
                    data = client.recv()
                    if data:
                        data = pkg(data, sink['msg_type'])
                        queue.put(data)
                    else:
                        break
            time.sleep(0.01)


def pcc_record():
    sink_group = NanoGroup()
    sinks = [
        {
            'ip': '127.0.0.1',
            'port': 1209,
            'msg_type': 'gsensor',
            'add_recv_ts': False,
            'pkg': Pkg.gsensor,
            'queue': Queue()
        },
        {
            'ip': '127.0.0.1',
            'port': 1208,
            'msg_type': 'can1',
            'add_recv_ts': False,
            'pkg': Pkg.can,
            'queue': Queue()
        },
        {
            'ip': '127.0.0.1',
            'port': 1207,
            'msg_type': 'can0',
            'add_recv_ts': False,
            'pkg': Pkg.can,
            'queue': Queue()
        },
        {
            'ip': '127.0.0.1',
            'port': 1200,
            'msg_type': 'camera',
            'add_recv_ts': False,
            'pkg': Pkg.camera,
            'queue': Queue()
        }
    ]
    for sink in sinks:
        sink_group.add_sink(sink)
    sink_group.start()
    while True:
        for sink in sinks:
            queue = sink['queue']
            msg_type = sink['msg_type']
            while not queue.empty():
                data = queue.get()
                if msg_type == 'camera':
                    print(data['ts'])
                    image = cv2.imdecode(np.fromstring(data['data'], np.uint8), cv2.IMREAD_COLOR)
                    cv2.imshow('hello', image)
                    cv2.waitKey(1)
                else:
                    print(data)
        time.sleep(0.01)


def nano_client_test():
    gsensor_client = NanoClient('127.0.0.1', 1209)
    gsensor_client.init()
    camera_client = NanoClient('127.0.0.1', 1200)
    camera_client.init()
    while True:
        temp = gsensor_client.recv()
        if temp:
            print(Pkg.gsensor(temp))
        temp = camera_client.recv()
        if temp:
            ts, fid, data = Pkg.camera(temp)
            print(ts, fid)
            image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow('hello', image)
            cv2.waitKey(1)
        time.sleep(0.02)


if __name__ == '__main__':
    # nano_client_test()
    freeze_support()
    pcc_record()
