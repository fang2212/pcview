#!/usr/bin/python
# -*- coding:utf-8 -*-

basic_cfg = {
    "ip": "192.168.0.233",
    "platform": "fpga",
    "debug": False,
    "pic": {
        "use_local": False,
        "test_image": "",
        "raw_type": "",
        "path": ""
    },
    "mobile": {
        "show": False,
        "path": ""
    },
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": True,
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
        "mobile_path": ""
    }
}

fpga_cfg = {
    "pic": {
        "raw_type": "gray"
    }
}

x1s_cfg = {
    "pic": {
        "raw_type": "color"
    }
}

pm_cfg = {
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": True,
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
    }
}

fpga_hil_cfg = {
    "ip": "192.168.1.233",
    "platform": "fpga",
    "pic": {
        "use_local": True,
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
        "lane": 1,
        "vehicle": 1,
        "ped": 1,
        "tsr": 1
    }
}


m3_hil_cfg = {
    "ip": "192.168.1.201",
    "platform": "arm",
    "pic": {
        "use_local": True,
        "test_image": "/media/minieye/localdata1/TestImage",
        "path": "/media/minieye/localdata1/TestCase/STRESS01/image_list.txt"
    },
    "mobile": {
        "show": True,
        "path": "/media/minieye/localdata1/TestCase/STRESS01/mobile_log.json"
    },
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": True,
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
        "lane": 1,
        "vehicle": 1,
        "ped": 1,
        "tsr": 1
    }
}

class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D

config = None

def load(usage):
    global config
    if usage == 'fpga':
        cfg = merge(basic_cfg, fpga_cfg)
    elif usage == 'x1s':
        cfg = merge(basic_cfg, x1s_cfg)
    elif usage == 'm3_hil':
        cfg = merge(basic_cfg, m3_hil_cfg)
    elif usage == 'fpga_hil':
        cfg = merge(basic_cfg, fpga_hil_cfg)
    elif usage == 'pm':
        cfg = merge(basic_cfg, pm_cfg)
    config = toDict(cfg)
