#!/usr/bin/python
# -*- coding:utf-8 -*-
# debug config fpga

fpga_cfg = {
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
        "log": False
    },
    "msg_types": [
        "lane",
        "vehicle"
    ],
    "show": {
        "overlook": False,
        "lane": True,
        "lane_type": False,
        "lane_speed_limit": 50,
        "vehicle": True,
        "ped": False,
        "tsr": False,
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
m3_cfg = {
    "ip": "192.168.1.201",
    # "port": 1200,
    "platform": "arm",
    "debug": True,
    "pic": {
        "use": True,
        "test_image": "/media/minieye/localdata1/TestImage",
        "path": "/media/minieye/localdata1/TestCase/STRESS01/image_list.txt"
    },
    "mobile": {
        "show": True,
        "path": "/media/minieye/localdata1/TestCase/STRESS01/mobile_log.json"
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
        "lane_speed_limit": 0,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "color": "color"
    },
    "fix": {
        "lane": 0,
        "vehicle": 0,
        "ped": 0,
        "tsr": 0
    },
    "testview": {
        "on": False,
        "mobile_path": "/media/minieye/4139A91A24AB9CBE/B9J5G7-201805301724/mobile"
    }
}

# debug config m3
fpga_hil_cfg = {
    "ip": "192.168.1.233",
    # "port": 1200,
    "platform": "fpga",
    "debug": True,
    "pic": {
        "use": True,
        "test_image": "/media/minieye/localdata1/TestImage",
        "path": "/media/minieye/localdata1/TestCase/STRESS01/image_list.txt"
    },
    "mobile": {
        "show": True,
        "path": "/media/minieye/localdata1/TestCase/STRESS01/mobile_log.json"
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
        "lane_speed_limit": 0,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "color": "color"
    },
    "fix": {
        "lane": 0,
        "vehicle": 0,
        "ped": 0,
        "tsr": 0
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

# config_dict = config_dict_fpga
# config_dict = config_dict_m3

def load(usage):
    if usage == 'fpga':
        return dic2obj(fpga_cfg)
    elif usage == 'm3':
        return dic2obj(m3_cfg)
    elif usage == 'fpga_hil':
        return dic2obj(fpga_hil_cfg)

config = load('fpga')
