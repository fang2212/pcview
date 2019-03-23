#.!/usr/bin/python
# -*- coding:utf8 -*-

class Sync(object):
    '''
    '''
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