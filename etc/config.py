#!/usr/bin/python
# -*- coding:utf-8 -*-
config_dict = {
    "ip": "192.168.1.233",
    "port": 1200,
    "debug": True,
    "pic": {
        "ispic": True,
        "path": "/media/tester/testdisk1/TestCase/B9J5G7-201805301724/case/fpga_case/case1/image_list.txt"
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
        "ped": True,
        "tsr": True
    },

    "fix": {
        "lane": 3,
        "vehicle": 5,
        "ped": 5,
        "tsr": 5
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
