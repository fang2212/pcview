from multiprocessing import Queue, Process
import asyncio
import msgpack
import aiohttp
from recorder import TextRecorder, get_data_str
import json
import time
import numpy as np

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



class LibFlowSink(Process):
    """aiohttp ws bind with process
    """

    def __init__(self, url, topic, mess_queue):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        self.url = url
        self.topic = topic
        self.recorder = TextRecorder("./aeb_log")


    def run(self):
        self.recorder.set_writer(get_data_str())

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
                    data = msgpack.unpackb(data[b'data'])
                    if b'image' in data:
                        data[b'image'] = np.fromstring(data[b'image'], np.uint8).tolist()
                    data = convert(data)
                    s = ''
                    if 'image' in data:
                        s = 'image'
                    if 'fusion_tracks' in data:
                        s = 'fusion_tracks'
                    if 'camera_meas' in data or 'radar_meas' in data:
                        s = 'meas'
                    print('---'+s, data['img_frame_id'])
                    self.recorder.write(str(data) + "\n")
                    mess_queue.put(data)
                    if msg.type in (aiohttp.WSMsgType.CLOSED,
                                    aiohttp.WSMsgType.ERROR):
                        break

        loop = asyncio.get_event_loop()
        loop.run_until_complete(ws_recv(self.url, self.topic, self.mess_queue))


class Sync(object):

    def __init__(self, mess_queue, max_cathe_size=20):
        self.queue = mess_queue
        self.cathe = {}
        self.max_cathe_size = max_cathe_size

    def pop_simple(self):
        if not self.queue.empty():
            data = self.queue.get()
            if 'img_frame_id' in data:
                if data['img_frame_id'] not in self.cathe:
                    self.cathe[data['img_frame_id']] = []
                self.cathe[data['img_frame_id']].append(data)
            if 'fusion_tracks' not in data:
                return None
            if len(self.cathe) > 0:
                frame_id = data['img_frame_id']
                data_list = self.cathe[frame_id]
                res = {'camera': {}, 'mea': {}, 'fusion': {}}
                flag = 0
                for item in data_list:
                    if 'image' in item:
                        res['camera'] = item
                        flag = 1
                    if 'camera_meas' in item or 'radar_meas' in item:
                        res['mea'] = item
                    if 'fusion_tracks' in item:
                        res['fusion'] = item
                if len(self.cathe) > self.max_cathe_size:
                    mkey = min(self.cathe)
                    self.cathe.pop(mkey)
                if flag:
                    return res
            return None
