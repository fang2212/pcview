#!/usr/bin/python
# -*- coding -*-

from multiprocessing import Process
import asyncio
import websockets
import msgpack
def convert(data):
    if isinstance(data, bytes):      return data.decode('ascii')
    if isinstance(data, dict):       return dict(map(convert, data.items()))
    if isinstance(data, tuple):      return tuple(map(convert, data))
    if isinstance(data, list):       return list(map(convert, data))
    if isinstance(data, set):        return set(map(convert, data))
    return data

class MtkSink(Process):
    def __init__(self, queue):
        Process.__init__(self)
        self.daemon = True
        self.msg_queue = queue

    def run(self):
        asyncio.get_event_loop().run_until_complete(
                self.msg_recv('ws://192.168.1.201:24012', self.msg_queue))

    async def msg_recv(self, uri, msg_queue):
        async with websockets.connect(uri) as websocket:
            msg = {
                'source': 'pcview-client',
                'topic': 'subscribe',
                'data': 'debug.hub.*',
            }
            data = msgpack.packb(msg)
            await websocket.send(data)

            while True:
                try:
                    data = await websocket.recv()
                    msg = msgpack.unpackb(data, use_list=False)
                    if msg[b'topic'] == b'debug.hub.ped':
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        # print('ped', convert(data))
                        msg_queue.put(('ped', convert(data)))
                    if msg[b'topic'] == b'debug.hub.lane':
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        # print('lane', convert(data))
                        msg_queue.put(('lane', convert(data)))
                    if msg[b'topic'] == b'debug.hub.vehicle':
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        # print('vehicle', convert(data))
                        msg_queue.put(('vehicle',convert(data)))
                    if msg[b'topic'] == b'debug.hub.tsr':
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        # print('tsr', convert(data))
                        msg_queue.put(('tsr',convert(data)))

                except websockets.exceptions.ConnectionClosed as err:
                    print('Connection was closed')
                    break
