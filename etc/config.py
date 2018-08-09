#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
config_dict = {
    "ip": "192.168.1.233",
    # "port": 1200,
    "platform": "fpga",
    "debug": True,
    "pic": {
        "use": False,
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
    "msg_types": [
        "lane",
        "vehicle",
        "ped",
        "tsr"
    ],
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
'''
# debug config fpga
config_dict = {
    "ip": "192.168.0.233",
    # "port": 1200,
    "platform": "fpga",
    "debug": True,
    "pic": {
        "use": False,
        "path": "/media/minieye/localdata1/TestCase/ped/image_list0.txt"
    },
    "mobile": {
        "show": False,
        "path": "/home/minieye/testdisk1/TestCase/B9J5G7-20180109/case/fpga_case/case1/mobile/log.json"
    },
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": False,
        "alert": False,  # 包括image和alert.log 主要用于演示平台
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
        "lane_speed_limit": 40,
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
    },
    "testview": {
        "on": False,
        "mobile_path": "/media/minieye/4139A91A24AB9CBE/B9J5G7-201805301724/mobile"
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
        "alert": False,   # 包括image和alert.log 主要用于演示平台
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
    },
    "testview": {
        "on": False,
        "mobile_path": "/media/minieye/4139A91A24AB9CBE/B9J5G7-201805301724/mobile"
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
