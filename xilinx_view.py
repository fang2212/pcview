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
import traceback

if sys.platform == 'win32':
    from threading import Thread as Process
    print('win32 platform')
else:
    print('linux platform')

from player import FPSCnt
from player.xilinx import FlowPlayer
from player.overlook import OverlookPlayer
from sink import TcpSink
from recorder import VideoRecorder, TextRecorder

def get_date_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

class PCView():
    
    def __init__(self, cfg):
        self.msg_queue = Queue()
        self.ip = cfg['ip']
        self.sync_size = cfg['sync']

        self.pc_draw = PCDraw(self.msg_queue, cfg)
        self.pc_draw.start()

    
    def run(self):
        # FlowSink.open_libflow_sink(ip, self.msg_queue)
        tcp_sink = TcpSink(self.ip, 12032, self.msg_queue, self.sync_size)
        tcp_sink.run()


class PCDraw(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue, file_cfg):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        self.save_log = file_cfg['log']
        self.save_video = file_cfg['video']
        self.save_path = os.path.join(file_cfg['path'], get_date_str())
        self.cfg = file_cfg

    def run(self):
        overlook = OverlookPlayer()
        player = FlowPlayer(self.cfg)
        if self.save_log:
            text_recorder = TextRecorder(self.save_path)
            text_recorder.set_writer(get_date_str())
        if self.save_video:
            video_recorder = VideoRecorder(self.save_path, fps=15)
            video_recorder.set_writer(get_date_str())

        fps_cnt = FPSCnt(100, 20)
        cnt = 0

        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                # print(mess)
                '''
                if mess == SinkError.Closed:
                    print('close')
                    if self.save_video:
                        video_recorder.release()
                    if self.save_log:
                        text_recorder.release()
                    cv2.destroyAllWindows()
                    return
                '''

                if 'frame_id' not in mess:
                    continue
                if 'camera' not in mess:
                    continue
                image = mess['camera']['image']

                cnt += 1
                fps_cnt.inc()

                frame_id = mess['frame_id']
                mess['env'] = {
                    'fps': fps_cnt.fps
                }

                if 'pedestrians' in mess or 'ldwparams' in mess or 'vehicle_warning' in mess or 'tsr_warning' in mess:
                    ol = None
                    try:
                        player.draw(mess, image)
                        ol = overlook.draw(mess)
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

                    ol = cv2.resize(ol, (500, 720))
                    img = cv2.hconcat((image, ol))
                    cv2.imshow('UI', img)
                    cv2.waitKey(1)

                if self.save_video:
                    video_recorder.write(image)
                if 'camera' in mess:
                    del mess['camera']['image']
                '''
                print('frame_id', frame_id)
                print(mess)
                '''
                if self.save_log:
                    text_recorder.write(json.dumps(mess)+'\n')
                
                if cnt % 2000 == 0:
                    if self.save_video:
                        video_recorder.release()
                        video_recorder.set_writer(get_date_str())
                    if self.save_log:
                        text_recorder.release()
                        text_recorder.set_writer(get_date_str())

            time.sleep(0.01)
        cv2.destroyAllWindows()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
    parser.add_argument("--path", help="保存地址", type=str)
    parser.add_argument("--ip", help="msg_fd地址", type=str)
    parser.add_argument("--sync", help="sync cache size", type=str)
    parser.add_argument("--lane_begin", help="车道线起点", type=str)
    parser.add_argument("--can_proto", help="can协议", type=str)
    parser.add_argument("--lane_pts", help="用算法输出点画车道线", type=str)
    args = parser.parse_args()
    file_cfg = {}
    cfg_file = 'config/xilinx.json'
    if os.path.exists(cfg_file):
        with open(cfg_file, 'r') as fp:
            cfg = json.load(fp)
            file_cfg.update(cfg)

    if sys.platform == 'win32':
        file_cfg['video'] = 0
    if args.ip:
        file_cfg['ip'] = args.ip
    if args.video:
        file_cfg['video'] = int(args.video)
    if args.ip:
        ip = args.ip
    if args.path:
        file_cfg['path'] = args.path
    if args.lane_pts:
        file_cfg['lane_pts'] = int(args.lane_pts)
    pcview = PCView(file_cfg)
    pcview.run()
