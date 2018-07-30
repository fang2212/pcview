#!/usr/bin/python
# -*- coding:utf-8 -*-
config_dict = {
    "ip": "192.168.1.233",
    "port": 1200,
    "debug": True,
    "pic": {
        "ispic": True,
        "path": "/home/minieye/TestCase/B9J5G7-201803271443/case/fpga_case/default_case/image_list.txt"
    },

    "mobile": {
        "show": False,
        "path": "/home/minieye/testdisk1/TestCase/B9J5G7-20180109/case/fpga_case/case1/mobile/log.json"
    },

    "save": {
        "path": "/home/tester/pcviewer-data/",
        "video": False,
        "alert": False,
        "log": False
    },
    
    "show": {
        "lane": True,
        "lane_speed_limit": 50,
        "vehicle": True,
        "ped": True
    }
}

def dic2obj(d):
    top = type('new', (object,), d)
    seqs = tuple, list, set, frozenset
    for i, j in d.items():
        if isinstance(j, dict):
            setattr(top, i, dic2obj(j))
        elif isinstance(j, seqs):
            setattr(top, i, type(j)(dic2obj(sj) if isinstance(sj, dict) else sj for sj in j))
        else:
            setattr(top, i, j)
    return top

config = dic2obj(config_dict)
