#!/usr/bin/python
# -*- coding:utf-8 -*-

basic_cfg = {
    "ip": "192.168.0.233",
    "platform": "fpga",
    "debug": False,
    "pic": {
        "use_local": False,
        "test_image": "",
        "raw_type": "gray",
        "path": ""
    },
    "cache_size": 100,
    "mobile": {
        "show": False,
        "path": ""
    },
    "save": {
        "result_path": "",
        "path": "/home/minieye/pcviewer-data/",
        "video": True,
        "alert": False,  # 包括image和alert.log 主要用于演示平台
        "log": True
    },
    "msg_types": [
        "lane",
        "vehicle"
    ],
    "show": {
        "overlook": False,
        "lane": True,
        "lane_begin": 460,
        "lane_end": 720,
        "all_laneline": False,
        "lane_type": False,
        "lane_speed_limit": 50,
        "vehicle": True,
        "ped": False,
        "tsr": False,
        "color": "color"
    },
    "fix": {
        "lane": 4,
        "vehicle": 4,
        "ped": 2,
        "tsr": 2
    },
    "testview": {
        "on": False,
        "mobile_path": ""
    },
    "can": {
        "use": False
    }
}

debug_cfg = {
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": True,
        "alert": False,   # 包括image和alert.log 主要用于演示平台
        "log": True
    },
    "pic": {
        "use_local": False,
        "test_image": "/media/minieye/localdata1/TestImage",
        "raw_type": "color",
        "path": "/media/minieye/localdata1/TestCase/STRESS01/image_list.txt"
    },
    "msg_types": [
        "lane",
    ],
    "show": {
        "lane": True,
        "lane_speed_limit": 0,
        "all_laneline": False,
        "vehicle": False,
        "ped": False,
        "tsr": False,
        "color": "color"
    },
    "fix": {
        "lane": 2,
        "vehicle": 2,
        "ped": 2,
        "tsr": 2
    },
    "can": {
        "use": True
    }
}

test_cfg = {
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": True,
        "alert": False,   # 包括image和alert.log 主要用于演示平台
        "log": True
    },
    "pic": {
        "use_local": False,
        "test_image": "/media/minieye/localdata1/TestImage",
        "raw_type": "gray",
        "path": "/media/minieye/localdata1/TestCase/STRESS01/image_list.txt"
    },
    "msg_types": [
        "lane",
        "vehicle",
        "ped",
        "tsr"
    ],
    "show": {
        "lane": True,
        "lane_speed_limit": 0,
        "all_laneline": False,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "color": "color"
    },
    "fix": {
        "lane": 2,
        "vehicle": 2,
        "ped": 2,
        "tsr": 2
    }
}

show_cfg = {
    "debug": True,
    "save": {
        "path": "/home/minieye/pcviewer-data/",
        "video": True,
        "alert": False,   # 包括image和alert.log 主要用于演示平台
        "log": True
    },
    "pic": {
        "use_local": True,
        "test_image": "/media/minieye/localdata1/TestImage",
        "raw_type": "gray",
        "path": "/media/minieye/localdata1/TestCase/PCSHOW01/image_list.txt"
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
        "all_laneline": False,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "color": "color"
    },
    "fix": {
        "lane": 4,
        "vehicle": 4,
        "ped": 4,
        "tsr": 4
    }
}

pro_cfg = {
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
        "all_laneline": False,
        "vehicle": True,
        "ped": True,
        "tsr": True,
        "color": "color"
    },
    "fix": {
        "lane": 4,
        "vehicle": 4,
        "ped": 4,
        "tsr": 4
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
    cfg = None
    if usage == 'fpga':
        cfg = basic_cfg
    elif usage == 'pro':
        cfg = merge(basic_cfg, pro_cfg)
    elif usage == 'test':
        cfg = merge(basic_cfg, test_cfg)
    elif usage == 'show':
        cfg = merge(basic_cfg, show_cfg)
    elif usage == 'debug':
        cfg = merge(basic_cfg, debug_cfg)
    if cfg:
        config = toDict(cfg)
