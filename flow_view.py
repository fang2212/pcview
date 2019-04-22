#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import logging
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


def get_data_str():
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

        self.can_sink = CanSink(self.can_queue)
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
        self.save_log = file_cfg['log']
        self.save_video = file_cfg['video']
        self.save_path = file_cfg['path']
    
    def run(self):
        player = FlowPlayer()
        if self.save_log:
            text_recorder = TextRecorder(self.save_path)
            text_recorder.set_writer(get_data_str())
        if self.save_video:
            video_recorder = VideoRecorder(self.save_path, fps=15)
            video_recorder.set_writer(get_data_str())

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

                can_data = {}
                while not self.can_queue.empty():
                    can_cache = self.can_queue.get()
                    can_data.update(can_cache)
                mess['can'] = can_data

                try:
                    player.draw(mess, image)
                except Exception as err:
                    cv2.imwrite('error.jpg', image)
                    if 'camera' in mess:
                        mess['camera'].pop('image', None)
                    with open('error.json', 'w+') as fp:
                        print('error json', err)
                        fp.write(json.dumps(mess))
                    continue

                cv2.imshow('UI', image)
                cv2.waitKey(1)

                if self.save_video:
                    video_recorder.write(image)
                if 'camera' in mess:
                    # del mess['camera']['image']
                    mess['camera'].pop('image', None)
                '''
                print('frame_id', frame_id)
                print(mess)
                '''
                if self.save_log:
                    text_recorder.write(json.dumps(mess)+'\n')
                
                if cnt % 2000 == 0:
                    if self.save_video:
                        video_recorder.release()
                        video_recorder.set_writer(get_data_str())
                    if self.save_log:
                        text_recorder.release()
                        text_recorder.set_writer(get_data_str())

            time.sleep(0.01)
        cv2.destroyAllWindows()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
    parser.add_argument("--log", help="是否保存日志[0,1],默认保存", type=str)
    parser.add_argument("--path", help="保存地址", type=str)
    parser.add_argument("--ip", help="msg_fd地址", type=str)
    parser.add_argument("--sync", help="sync cache size", type=str)
    parser.add_argument("--lane_pts", help="", type=str)
    args = parser.parse_args()
    ip = '127.0.0.1'
    file_cfg = {
        'video': 1,
        'log': 1,
        'sync': 12,
        'path': 'pcview_data',
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
    pcview = PCView(ip, file_cfg)
    pcview.run()

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