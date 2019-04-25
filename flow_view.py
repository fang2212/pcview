#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import logging
import traceback
import time
import msgpack
import json
import cv2
import argparse
import numpy as np
from datetime import datetime
from multiprocessing import Process, Queue, Value

if sys.platform == 'win32':
    from threading import Thread as Process
    print('win32 platform')
else:
    print('linux platform')

from player import FPSCnt, FlowPlayer
from sink import TcpSink
from recorder import VideoRecorder, TextRecorder
from sink.canSink import CanSink 

def get_date_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

class PCView():
    
    def __init__(self, ip, cfg):
        self.msg_queue = Queue()
        self.can_queue = Queue()
        self.ip = ip
        self.sync_size = cfg['sync']

        self.pc_draw = PCDraw(self.msg_queue, self.can_queue, cfg)
        self.pc_draw.start()

        if cfg['can_proto']:
            self.can_sink = CanSink(cfg['can_proto'], self.can_queue)
            self.can_sink.start()

    
    def run(self):
        # FlowSink.open_libflow_sink(ip, self.msg_queue)
        tcp_sink = TcpSink(self.ip, 12032, self.msg_queue, self.sync_size)
        tcp_sink.run()


class PCDraw(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue, can_queue, file_cfg):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        self.can_queue = can_queue
        self.file_cfg = file_cfg
        self.save_path = os.path.join(file_cfg['path'], get_date_str())
        
    
    def run(self):
        player = FlowPlayer(self.file_cfg)
        if self.file_cfg['log']:
            text_recorder = TextRecorder(self.save_path)
            text_recorder.set_writer(get_date_str())
        if self.file_cfg['video']:
            video_recorder = VideoRecorder(self.save_path, fps=15)
            video_recorder.set_writer(get_date_str())

        fps_cnt = FPSCnt(20, 20)
        cnt = 0

        can_cache = []
        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()

                if 'frame_id' not in mess:
                    continue
                if 'camera' not in mess:
                    image = np.zeros((720, 1280, 3), np.uint8)
                    temp = mess.get('camera_time')
                    mess['camera'] = {
                        'create_ts': temp
                    }
                else:
                    image = mess['camera']['image']

                cnt += 1
                fps_cnt.inc()

                frame_id = mess['frame_id']
                mess['env'] = {
                    'fps': fps_cnt.fps
                }

                if self.file_cfg['can_proto']:
                    can_data = {}
                    while not self.can_queue.empty():
                        can_cache = self.can_queue.get()
                        can_data.update(can_cache)
                    mess['can'] = can_data

                if 'pedestrians' in mess or 'ldwparams' in mess or 'vehicle_warning' in mess or 'tsr_warning' in mess:
                    try:
                            player.draw(mess, image)
                    except Exception as err:
                        if not os.path.exists(self.save_path):
                            os.makedirs(self.save_path)
                        cv2.imwrite(os.path.join(self.save_path, 'error.jpg'), image)
                        if 'camera' in mess:
                            mess['camera'].pop('image', None)
                        with open(os.path.join(self.save_path, 'error.json'), 'w+') as fp:
                            print('error json', err)
                            fp.write(json.dumps(mess)+'\n')
                            fp.write(traceback.format_exc())
                        continue
                    cv2.imshow('UI', image)
                    cv2.waitKey(1)

                if self.file_cfg['video']:
                    video_recorder.write(image)
                if 'camera' in mess:
                    # del mess['camera']['image']
                    mess['camera'].pop('image', None)
                '''
                print('frame_id', frame_id)
                print(mess)
                '''
                if self.file_cfg['log']:
                    text_recorder.write(json.dumps(mess)+'\n')
                
                if cnt % 2000 == 0:
                    if self.file_cfg['video']:
                        video_recorder.release()
                        video_recorder.set_writer(get_date_str())
                    if self.file_cfg['log']:
                        text_recorder.release()
                        text_recorder.set_writer(get_date_str())

            time.sleep(0.01)
        cv2.destroyAllWindows()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
    parser.add_argument("--log", help="是否保存日志[0,1],默认保存", type=str)
    parser.add_argument("--path", help="保存地址", type=str)
    parser.add_argument("--ip", help="msg_fd地址", type=str)
    parser.add_argument("--sync", help="sync cache size", type=str)
    parser.add_argument("--lane_begin", help="车道线起点", type=str)
    parser.add_argument("--can_proto", help="can协议", type=str)
    args = parser.parse_args()
    ip = '127.0.0.1'
    file_cfg = {
        'video': 1,
        'log': 1,
        'sync': 12,
        'path': 'pcview_data',
        'lane_begin': 0,
        'can_proto': '',
    }
    if sys.platform == 'win32':
        file_cfg['video'] = 0
    if args.video:
        file_cfg['video'] = int(args.video)
    if args.ip:
        ip = args.ip
    if args.log:
        file_cfg['log'] = int(args.log)
    if args.path:
        file_cfg['path'] = args.path
    if args.lane_begin:
        file_cfg['lane_begin'] = int(args.lane_begin)
    if args.can_proto:
        file_cfg['can_proto'] = args.can_proto
        if file_cfg['can_proto'] == 'no-can':
            file_cfg['can_proto'] = ''
    try:
        pcview = PCView(ip, file_cfg)
        pcview.run()
    except Exception as e:
        exc = traceback.format_exc()
        with open('error.log', 'w') as f:
            f.write(exc)

'''
{
    "camera_time": 1455208613969069,
    "vehicle_start_time": 1455208613969069,
    "vehicle_finish_time": 1455208613969069,
    "lane_start_time": 1455208613969069,
    "lane_finish_time": 1455208613969069,
    "tsr_start_time": 1455208613969069,
    "tsr_finish_time": 1455208613969069,
}
'''