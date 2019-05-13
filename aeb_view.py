#.!/usr/bin/python
#coding:utf-8

import asyncio
import msgpack
import aiohttp
import numpy as np
import time
from multiprocessing import Process, Queue
import cv2

def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):  return data.decode('ascii')
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return tuple(map(convert, data))
    if isinstance(data, list):   return list(map(convert, data))
    if isinstance(data, set):    return set(map(convert, data))
    return data

class Sync(object):
    def __init__(self, id_size, key='frame_id'):
        self.id_size = id_size
        self.id_cache = []
        self.key = key
        self.id_set = set()

        self.inc = 0
        self.ready = 100
        self.res_size = 0

    def append(self, one):
        key = self.key
        self.id_set.add(one.get(key))
        self.id_cache.append(one)
        self.id_cache.sort(key=lambda o: o.get(key))
        # print('len', len(self.id_cache))
        # print('gap', len(self.id_set))
        res = []
        ok = 0
        if len(self.id_set) > self.id_size:
            ok = 1
    
        if self.res_size:
            first_id = self.id_cache[0].get(key)
            now_size = 0
            for one in self.id_cache:
                if one.get(key) == first_id:
                    now_size += 1
                else:
                    break
            if now_size >= self.res_size:
                ok = 2

        if ok:
            pop_id = self.id_cache[0].get(key)
            idx = 0
            self.id_set.remove(pop_id)
            for one in self.id_cache:
                if one.get(key) == pop_id:
                    idx += 1
                else:
                    break
            res = self.id_cache[:idx]
            self.inc += 1
            self.id_cache = self.id_cache[idx:]
            print('sync res size', len(res), 'type', ok, 'size', len(self.id_cache), 'pop_id', pop_id)
            if self.inc >= self.ready and len(res) > self.res_size:
                self.res_size = len(res)
        return res

class AioWs(Process):
    """aiohttp ws bind with process
    """
    
    def __init__(self, url, topic, mess_queue):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        self.url = url
        self.topic = topic

    def run(self):
        async def ws_recv(url, topic, mess_queue):
            session = aiohttp.ClientSession()
            async with session.ws_connect(url) as ws:

                msg = {
                    'source': 'pcview',
                    'topic': 'subscribe',
                    'data': topic,
                }
                data = msgpack.packb(msg)
                await ws.send_bytes(data)
                async for msg in ws:
                    data = msgpack.unpackb(msg.data)
                    data = data[b'data']
                    mess_queue.put(data)

                    if msg.type in (aiohttp.WSMsgType.CLOSED,
                                    aiohttp.WSMsgType.ERROR):
                        break
                    
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ws_recv(self.url, self.topic, self.mess_queue))

def read_data(data):
    try:
        data = msgpack.unpackb(data, use_list=False)
    except BaseException as e:
        pass

    if b'frame_id' in data:
        data = convert(data)
    else:
        frame_id = int.from_bytes(data[4:8], byteorder="little", signed=False)
        ts = int.from_bytes(data[16:24], byteorder="little", signed=False)
        data = data[24:]
        image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
        data = {
            'camera': {
                'image': image,
                'frame_id': frame_id,
                'create_ts': ts
            },
            'frame_id': frame_id
        }
    return data
    

def main():
    mess_queue = Queue()
    aiows = AioWs('ws://192.168.0.233:24011', 'pcview', mess_queue)
    aiows.start()
    print('aio start')
    sync = Sync(10)
    while True:
        while not mess_queue.empty():

            data = read_data(mess_queue.get())
            '''
            pops为同步一帧的数据
            '''
            pops = sync.append(data)

            print(pops)
            
        time.sleep(0.1)

if __name__ == '__main__':
    main()