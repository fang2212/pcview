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

    def append(self, one):
        key = self.key
        self.id_set.add(one.get(key))
        self.id_cache.append(one)
        self.id_cache.sort(key=lambda o: o.get(key))
        # print('len', len(self.id_cache))
        # print('gap', len(self.id_set))
        res = []
        if len(self.id_set) > self.id_size:
            pop_id = self.id_cache[0].get(key)
            idx = 0
            self.id_set.remove(pop_id)
            for one in self.id_cache:
                if one.get(key) == pop_id:
                    idx += 1
                else:
                    break
            res = self.id_cache[:idx]
            print('sync res size', len(res))
            self.id_cache = self.id_cache[idx:]
        return res