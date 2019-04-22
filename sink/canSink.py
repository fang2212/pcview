import sys
from multiprocessing import Process, Queue, Value
if sys.platform == 'win32':
    from threading import Thread as Process

from sensor.liuqi import parse_liuqi
from easy_can.base import CanBase

class CachePool():
    def __init__(self, cache_num=2):
        self.cache_num = cache_num
        self.caches = {}
        self.miss = {}

    def update(self, key, data):
        self.caches[key] = data
        self.miss[key] = 0

    def get(self):
        res = {}
        for key in self.caches:
            if self.miss[key] <= self.cache_num:
                res[key] = self.caches[key]
            self.miss[key] += 1
        return res
        

class CanSink(Process):
    def __init__(self, can_queue, bitrate=500000):
        Process.__init__(self)
        self.can0 = CanBase(bitrate=bitrate)  
        self.can_queue = can_queue  
        self.cache = CachePool(2)

    def run(self):
        while True:
            tmp = self.can0.recv()
            #print(tmp)
            ts = tmp['recv_ts']
            can_id = int(tmp['can_id'], 16)
            data = bytes(tmp['data'])
            r = parse_liuqi(can_id, data)
            if r:
                self.cache.update(can_id, r)
            if self.can_queue.empty():
                cache_data = self.cache.get()
                res = {}
                for value in cache_data.values():
                    res.update(value)
                self.can_queue.put(res)