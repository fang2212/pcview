#!/usr/bin/python
# -*- coding:utf-8 -*-
import json
# debug config fpga


collector0 = {
    "ip": "192.168.3.233",
    # "ip": "192.168.98.227",
    "mac": '00:0c:18:ef:ff:ed',
    # 'mac': '00:0a:35:00:01:22',
    # "ip": "127.0.0.1",
    # "port": 1200,
    "platform": "fpga",
    "debug": True,
    "work_mode": 'collector',  # 'validator'
    "repeater": True,
    "pic": {
        "use": False,
        "path": "/media/minieye/localdata1/TestCase/ped/image_list0.txt"
    },
    "mobile": {
        "show": False,
        "path": "/home/minieye/testdisk1/TestCase/B9J5G7-20180109/case/fpga_case/case1/mobile/log.json"
    },
    "save": {
        "path": "./the_log.txt",
        "video": True,
        "alert": False,
        "log": False,
        "raw": True
    },
    "msg_types": [
        "can0",
        "can1",
        "gsensor"
        # "lane",
        # "vehicle",
        # "ped",
        # "tsr"
    ],
    "can_types": {
        "can0": ['esr'],
        "can1": ['x1']
    },
    "show": {
        "overlook": False,
        "lane": True,
        "lane_speed_limit": 40,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "q3": True,
        "radar": True,
        "color": "color"
    },
    "fix": {
        "lane": 1,
        "vehicle": 2,
        "ped": 2,
        "tsr": 2
    }
}


collector1 = {
    #"ip": "192.168.0.233",
    "ip": "192.168.98.227",
    # "ip": "127.0.0.1",
    # "port": 1200,
    'mac': '00:0a:35:00:01:22',
    "platform": "fpga",
    "debug": True,
    "work_mode": 'collector',  # 'validator'
    "repeater": True,
    "pic": {
        "use": False,
        "path": "/media/minieye/localdata1/TestCase/ped/image_list0.txt"
    },
    "mobile": {
        "show": False,
        "path": "/home/minieye/testdisk1/TestCase/B9J5G7-20180109/case/fpga_case/case1/mobile/log.json"
    },
    "save": {
        "path": "/media/nan/860evo/data/pcviewer",
        "video": False,
        "alert": False,
        "log": False,
        "raw": True
    },
    "msg_types": [
        "can0",
        "can1",
        # "gsensor"
        # "lane",
        # "vehicle",
        # "ped",
        # "tsr"
    ],
    "can_types": {
        "can0": ['x1'],
        "can1": ['esr']
    },
    "show": {
        "overlook": False,
        "lane": True,
        "lane_speed_limit": 40,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "q3": True,
        "radar": True,
        "color": "color"
    },
    "fix": {
        "lane": 1,
        "vehicle": 2,
        "ped": 2,
        "tsr": 2
    }
}

# debug config m3
config_dict_m3 = {
    "ip": "192.168.1.201",
    # "port": 1200,
    "platform": "arm",
    "debug": True,
    "pic": {
        "use": True,
        "path": "/media/minieye/localdata1/TestCase/ped/image_list0.txt"
    },
    "mobile": {
        "show": False,
        "path": "/home/minieye/testdisk1/TestCase/B9J5G7-20180109/case/fpga_case/case1/mobile/log.json"
    },
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": False,
        "alert": False,
        "log": True
    },
    "msg_types": [
        "lane",
        "vehicle",
        "ped",
        "tsr"
    ],
    "show": {
        "overlook": True,
        "lane": True,
        "lane_speed_limit": 50,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "color": "color"
    },
    "fix": {
        "lane": 1,
        "vehicle": 2,
        "ped": 2,
        "tsr": 2
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


config = dic2obj(collector0)
configs = [dic2obj(collector0),
           dic2obj(collector1)]

install = json.load(open('config/installation.json'))


def load_config(jsonspec):
    global config, configs
    spec = json.load(open(jsonspec))
    # config = dic2obj(spec[0])
    configs[0] = dic2obj(spec[0])
    configs[1] = dic2obj(spec[1])
    config = configs[0]


def load_installation(jsonspec):
    global install
    spec = json.load(open(jsonspec))
    for item in spec:
        install[item] = spec[item]
    # del install
    # install = dic2obj(spec)

