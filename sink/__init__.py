from .flow import TcpSink
from .replay import FlowReader
from .nano import NanoSink

def fix_frame(pre_, now_, now_id, fix_range):  #如果该帧数据为空，并且上一帧相隔不大，绘制上一帧的数据让图像连续
    if now_.get('frame_id') or (not fix_range):
        return now_, now_
    if pre_.get('frame_id'):
        if pre_.get('frame_id') + fix_range >= now_id:
            return pre_, pre_
    return {}, {}

def fix_all(pre_, now_, fix_range=4):  #如果该帧数据为空，并且上一帧相隔不大，绘制上一帧的数据让图像连续
    frame_id = now_['frame_id']
    for key in ['lane', 'ped', 'vehicle', 'tsr']:
        pre_[key], now_[key] = fix_frame(pre_[key], now_[key], frame_id, fix_range)