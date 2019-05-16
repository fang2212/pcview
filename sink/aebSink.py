from multiprocessing import Queue, Process
import asyncio
import msgpack
import aiohttp
from recorder import TextRecorder, get_data_str
import json


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
                    data = convert(msgpack.unpackb(data[b'data']))
                    self.recorder.write(str(data) + "\n")
                    mess_queue.put(data)
                    if msg.type in (aiohttp.WSMsgType.CLOSED,
                                    aiohttp.WSMsgType.ERROR):
                        break

        loop = asyncio.get_event_loop()
        loop.run_until_complete(ws_recv(self.url, self.topic, self.mess_queue))


class Sync(object):

    def __init__(self, mess_queue, max_cathe_size=5):
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

        if len(self.cathe) < self.max_cathe_size:
            return None
        else:
            while len(self.cathe):
                mkey = min(self.cathe)
                data_list = self.cathe[mkey]
                data = {'camera': {}, 'mea': {}, 'fusion': {}}
                flag = 0
                for item in data_list:
                    if 'image' in item:
                        data['camera'] = item
                        flag = 1
                    if 'camera_meas' in item or 'radar_meas' in item:
                        data['mea'] = item
                    if 'fusion_tracks' in item:
                        data['fusion'] = item
                self.cathe.pop(mkey)
                if flag:
                    return data
            return None
