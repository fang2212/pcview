#!/usr/bin/python
# -*- coding:utf8 -*-

from multiprocessing import Process
import nanomsg
import msgpack
from etc.config import config

class Sink(Process):
    def __init__(self, queue, port=1200):
        Process.__init__(self)
        self.deamon = True
        self.port = port
        self.queue = queue
        self.q_max = 20
        self.cur_frame_id = -1

    def _init_socket(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB,
                nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (config.ip, self.port, ))

    def run(self):
        self._init_socket()
        while True:
            buf = nanomsg.wrapper.nn_recv(self._socket, 0)
            frame_id, data = self.pkg_handler(buf[1])

    def pkg_handler(self, msg_buf):
        pass

    def set_frame_id(self, frame_id):
        # This method must be called
        self.cur_frame_id = frame_id

def convert(data):
    if isinstance(data, bytes):      return data.decode('ascii')
    if isinstance(data, dict):       return dict(map(convert, data.items()))
    if isinstance(data, tuple):      return tuple(map(convert, data))
    if isinstance(data, list):       return list(map(convert, data))
    if isinstance(data, set):        return set(map(convert, data))
    return data

class CameraSink(Sink):

    def __init__(self, queue, port=1200):
        Sink.__init__(self, queue, port)

    def pkg_handler(self, msg):
        # print('c--process-id:', os.getpid())
        msg = memoryview(msg).tobytes()
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        data = msg[16:]
        res = {'frame_id': frame_id, 'img': data}
        self.queue.put(('img', msg))
        return frame_id, data

class LaneSink(Sink):

    def __init__(self, queue, port=1203):
        Sink.__init__(self, queue, port)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        self.queue.put(('lane', res))
        # print(`', res)
        return frame_id, res

class VehicleSink(Sink):

    def __init__(self, queue, port=1204):
        Sink.__init__(self, queue, port)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        # print('v data:', res)
        self.queue.put(('vehicle', res))
        return frame_id, res

class PedSink(Sink):

    def __init__(self, queue, port=1205):
        Sink.__init__(self, queue, port)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        # print('p data:', res)
        self.queue.put(('ped', res))
        return frame_id, res
