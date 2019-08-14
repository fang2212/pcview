#!/usr/bin/env python
# _*_ coding:utf-8 _*_
#
# @Version : 1.0
# @Time    : 2018/07/15
# @Author  : simon.xu
# @File    : config.py
# @Desc    :


import json
import os
import shutil

collector0 = {
    "ip": "192.168.0.233",
    # "ip": "192.168.98.227",
    "mac": '00:0c:18:ef:ff:ed',
    # 'mac': '00:0a:35:00:01:22',
    # "ip": "127.0.0.1",
    # "port": 1200,
    "platform": "fpga",
    "debug": True,
    "work_mode": 'collector',  # 'validator'
    "repeater": True,
    "save": {
        "path": "/media/nan/860evo/data/pcviewer",
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
        "can0": ['ifv300'],
        "can1": []
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
    'mac': '00:0c:18:ef:ff:e0',
    "platform": "fpga",
    "debug": True,
    "work_mode": 'collector',  # 'validator'
    "repeater": True,
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

collector2 = {
    "ip": "192.168.98.227",
    # "ip": "127.0.0.1",
    # "port": 1200,
    'mac': '00:0c:18:ef:ff:ec',
    "platform": "fpga",
    "debug": True,
    "work_mode": 'collector',  # 'validator'
    "repeater": True,
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
        "can0": ['rtk'],
        "can1": []
    }
}

collector3 = {
    "ip": "192.168.98.227",
    # "ip": "127.0.0.1",
    # "port": 1200,
    'mac': '00:0c:18:ef:ff:e1',
    "platform": "fpga",
    "debug": True,
    "work_mode": 'collector',  # 'validator'
    "repeater": True,
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
        "can0": ['rtk'],
        "can1": []
    }
}

collector4 = {
    # "ip": "192.168.98.227",
    # "ip": "127.0.0.1",
    # "port": 1200,
    'mac': 'b8:27:eb:21:ba:29',
    "platform": "fpga",
    "debug": True,
    "work_mode": 'collector',  # 'validator'
    "repeater": True,
    "msg_types": [
        "can0",
        # "gsensor"
        # "lane",
        # "vehicle",
        # "ped",
        # "tsr"
    ],
    "can_types": {
        "can0": ['rtk'],
        "can1": []
    }
}

cfg_superb = {
    'version': 0.1,
    'collectors': [0, 1, 2, 3, 4],
    'installation': {
        "video": {
            "lon_offset": -1.67,
            "fv": 1458.0,
            "cv": 360.0,
            "roll": 1.0,
            "fu": 1458.0,
            "cu": 640.0,
            "height": 1.18,
            "lat_offset": 0.15,
            "yaw": 2.25,
            "pitch": -0.4
        },
        "ifv300": {
            "lon_offset": -1.64,
            "roll": 0.0,
            "height": 1.18,
            "lat_offset": 0.0,
            "yaw": 0.0,
            "pitch": 0.0
        },
        "x1": {
            "lon_offset": -1.64,
            "roll": 0.0,
            "height": 1.18,
            "lat_offset": 0.0,
            "yaw": 0.0,
            "pitch": 0.0
        },
        "esr": {
            "lon_offset": 0.0,
            "roll": 0.0,
            "height": 0.45,
            "lat_offset": 0.22,
            "yaw": -1.8,
            "pitch": 0.0
        },
        "rtk": {
            "lon_offset": -0.21,
            "roll": 0.0,
            "height": 0.86,
            "lat_offset": 0.0,
            "yaw": 0.0,
            "pitch": -2.0
        },
        "lmr": {
            "lon_offset": 0.0,
            "roll": 0.0,
            "height": 0.45,
            "lat_offset": -0.3,
            "yaw": -1.0,
            "pitch": 0.0
        }
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


def load_config(jsonspec):
    global config, configs
    spec = json.load(open(jsonspec))
    # config = dic2obj(spec[0])
    for idx, coll in enumerate(spec):
        try:
            configs[idx] = coll
        except Exception as e:
            configs.append(coll)
    # configs[0] = spec[0]
    # configs[1] = spec[1]
    config = dic2obj(configs[0])
    print(bcl.WARN + 'configs:' + bcl.ENDC)
    for c in configs:
        print(c)


def load_cfg(jsonspec):
    print(bcl.WARN+'using config:' + bcl.ENDC, jsonspec)
    global configs, install
    spec = json.load(open(jsonspec))
    for idx in spec['collectors']:
        clct = json.load(open('config/collectors/{}.json'.format(idx)))
        configs.append(clct)

    for item in spec['installation']:
        # print(item)
        install[item] = spec['installation'][item]
    # config = dic2obj(configs[0])


def load_installation(jsonspec):
    global install
    spec = json.load(open(jsonspec))
    for item in spec:
        install[item] = spec[item]
    # del install
    # install = dic2obj(spec)
    print(bcl.WARN + 'installation:' + bcl.ENDC)
    print(install)


class bcl:
    HDR = '\033[95m'
    OKBL = '\033[94m'
    OKGR = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


configs = []
install = {}

__test = []

if __name__ == "__main__":
    config = dic2obj(collector0)
    configs = [collector0,
               collector1,
               collector2,
               collector3,
               collector4]

    json.dump({'installation': json.load(open('installation.json')), 'collectors': configs},
              open('skoda_spb.json', 'w+'), indent=True)
    json.dump(collector0, open('collectors/0.json', 'w+'), indent=True)
    json.dump(collector1, open('collectors/1.json', 'w+'), indent=True)
    json.dump(collector2, open('collectors/2.json', 'w+'), indent=True)
    json.dump(collector3, open('collectors/3.json', 'w+'), indent=True)
    json.dump(collector4, open('collectors/4.json', 'w+'), indent=True)
    json.dump(cfg_superb, open('cfg_superb.json', 'w+'), indent=True)
    json.dump(configs, open('config.json', 'w+'), indent=True)


else:
    # install = json.load(open('etc/installation.json'))
    # configs = json.load(open('config/skoda_spb.json'))['collectors']
    install = json.load(open('config/cfg_superb.json'))['installation']
    # config = dic2obj(configs[0])

    if not os.path.exists('config/local.json'):
        shutil.copy('config/local_sample.json', 'config/local.json')
    local_cfg = dic2obj(json.load(open('config/local.json')))

