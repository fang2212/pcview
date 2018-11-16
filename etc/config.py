#!/usr/bin/python
# -*- coding:utf-8 -*-
import os 
home_path = os.path.expanduser('~')                 #home目录路径
media_path = home_path.replace('home', 'media')     #外接硬盘路径

cfg_dict = {
    "fpga":{           #基本配置项
        "inhert": None,         #从哪组配置参数继承
        "ip": "192.168.0.233",  #默认设备ip,通过--ip参数覆盖
        "platform": "fpga",     #设备平台类型
        "pic": {            #图片配置
            "use_local": False, #使用本地图片
            "test_image": "",   #本地图片文件夹路径
            "raw_type": "color", #图片类型 [color, gray]
            "path": "",         #图片列表
        },  
        "can": {            #can配置    
            "use": True,        #启用can
            "bitrate": 500000,  #波特率 500000 or 250000
        },
        "mobile": {         #mobile
            "show": False,      #显示mobile 数据
            "path": ""          #mobile数据文件路径
        },
        "save": {           #保存内容配置
            "result_path": "",  #指定保存路径
            "path": home_path + "/pcviewer-data/",  #保存跟目录，在它下面以日期为文件夹名新建文件夹保存
            "video": True,      #保存结果视频
            "log": True,        #保存log日志
            "can": True,        #保存can数据
        },
        "show": {           #显示内容配置
            "parameters": True, #左上角参数，True内部版本，全部显示， False客户版本,只显示frameid和时间
            "overlook": False,  #右上角俯视缩略图
            "debug": False,     #显示图片路径
            "lane": True,       #车道线算法结果
            "vehicle": True,    #车辆算法结果
            "ped": False,       #行人算法结果
            "tsr": False,       #交通牌算法结果
            "cali": False,      #
        },
        "lane":{            #车道线配置
            "lane_begin": 460,  #车起始位置
            "lane_end": 720,    #结束位置
            "all_laneline": False,  #绘制所有车道线
            "lane_speed_limit": 50, #速度限制，小于该值不画车道线
        },
        "cache_size": 10,   #nanomsg接收数据缓冲限制
        "msg_types": [      #nanomsg接收数据类型
            "lane",
            "vehicle"
        ],
        "fix": {            #补帧范围
            "lane": 4,
            "vehicle": 4,
            "ped": 2,
            "tsr": 2,
            "cali": 0
        },
    },
    "debug":{
        "inhert": "fpga",
        "can": {
            "use": False
        },
        "msg_types": [
            "lane",
        ],
        "show": {
            "lane": True,
            "vehicle": False,
        },
        "lane":{
            "lane_speed_limit": 0,
            "all_laneline": False,
        },
        "fix": {
            "lane": 2,
            "vehicle": 2,
        },
    },
    "test":{
        "inhert": "fpga",
        "msg_types": [
            "lane",
            "vehicle",
            "ped",
            "tsr"
        ],
        "show": {
            "lane": True,       
            "vehicle": True,
            "ped": True,
            "tsr": True,
        },
        "lane":{
            "lane_speed_limit": 0,
            "all_laneline": False,
        },
        "fix": {
            "lane": 2,
            "vehicle": 2,
            "ped": 2,
            "tsr": 2
        }
    },
    "show":{
        "inhert": "fpga",
        "pic": {
            "use_local": True,
            "test_image": media_path + "/localdata1/TestImage",
            "raw_type": "color",
            "path": media_path + "/localdata1/TestCase/PCSHOW01/image_list.txt"
        },
        "msg_types": [
            "lane",
            "vehicle",
            "ped",
            "tsr"
        ],
        "show": {
            "overlook": True,
            "debug": True,
            "lane": True,
            "vehicle": True,
            "ped": True,
            "tsr": True,
        },
        "lane":{
            "lane_speed_limit": 0,
            "all_laneline": False,
        },
        "fix": {
            "lane": 4,
            "vehicle": 4,
            "ped": 4,
            "tsr": 4
        }
    },
    "pro":{
        "inhert": 'test',
        "show": {
            "overlook": True,
        },
        "fix": {
            "lane": 4,
            "vehicle": 4,
            "ped": 4,
            "tsr": 4
        }
    },
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

def merge_cfg(usage):
    cfg = cfg_dict[usage]
    if cfg['inhert']:
        inhert = merge_cfg(cfg['inhert'])
        return merge(inhert, cfg)
    else:
        return cfg

def load(usage):
    global config
    cfg = merge_cfg(usage)
    config = toDict(cfg)
