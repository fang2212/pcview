import json

player_cfg = {           #绘图基本配置项
    "lane": {            #车道线配置
        "show_obj": True,
        "lane_begin": -1,  #车起始位置
        "lane_end": -1,    #结束位置
        "all_laneline": False,  #绘制所有车道线
        "speed_limit": 50, #速度限制，小于该值不画车道线
        "show_warning": False,
        "show_info": True
    },
    "vehicle": {        
        "show_obj": True,
        "rect_type": 'obj',
        "thickness": 1,
        "len_ratio": 50,
        "show_warning": False,
        "show_info": True
    },
    "ped": {        
        "show_obj": True,
        "thickness": 1,
        "show_warning": False,
        "show_info": True
    },
    "tsr": {        
        "show_obj": True,
        "thickness": 1,
        "show_warning": False,
        "show_info": True
    },
    "env": {        
        "show": True
    }
}

recorder_cfg = {
    "path": "pcview_data",
    "log": False,
    "video": False
}

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

def read_json(path):
    with open(path, 'r+') as fp:
        res = json.loads(fp.read())
        return res