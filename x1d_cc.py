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
from player import BaseDraw, FlowPlayer

if sys.platform == 'win32':
    from threading import Thread as Process
    print('win32 platform')
else:
    print('linux platform')

from player import FPSCnt
from sink import TcpSink
from recorder import Collector

def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

class PCView():
    
    def __init__(self, ip, file_cfg):
        self.msg_queue = Queue()
        self.ip = ip

        self.pc_draw = PCDraw(self.msg_queue, file_cfg)
        self.pc_draw.start()

    
    def run(self):
        tcp_sink = TcpSink(self.ip, 12032, self.msg_queue)
        tcp_sink.run()


class PCDraw(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue, file_cfg):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        self.save_path = file_cfg['path']

    def run(self):
        #collector = Collector(self.save_path, period=500, fps=20, w=1280, h=720)
        collector = Collector(self.save_path, period=500, fps=20, w=720, h=480)
        # collector = Collector(self.save_path)

        fps_cnt = FPSCnt(20, 0)
        cnt = 0

        player = FlowPlayer()
        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                if 'frame_id' not in mess:
                    continue
                if 'camera' not in mess:
                    continue
                collector.write(mess)

                fps_cnt.inc()

                image = mess['camera']['image']
                #'''
                player.draw(mess, image)
                '''
                fid = mess['frame_id']
                # draw now id
                speed, turnlamp = '-', '-'
                if 'speed' in mess:
                    speed = "%.1f" % (3.6*float(mess['speed']))
                if 'turnlamp' in mess:
                    turnlamp = mess['turnlamp']
                now = datetime.now()
                t1 = now.strftime('%Y-%m-%d')
                t2 = now.strftime('%H:%M:%S')
                para_list = [
                    'fps:' + str(fps_cnt.fps),
                    'speed:' + str(speed)+'km/h',
                    'turnlamp:' + str(turnlamp),
                    'fid:' + str(fid),
                    '' + str(t1),
                    '' + str(t2)
                ]
                BaseDraw.draw_single_info(image, (0, 0), 140, 'env', para_list)
                '''

                cv2.imshow('UI', image)
                cv2.waitKey(1)

                
            time.sleep(0.01)
        cv2.destroyAllWindows()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="保存地址", type=str)
    parser.add_argument("--ip", help="msg_fd地址", type=str)
    args = parser.parse_args()
    ip = '127.0.0.1'
    file_cfg = {
        'path': 'x1d_data',
    }
    if args.ip:
        ip = args.ip
    if args.path:
        file_cfg['path'] = args.path+'/'+get_data_str()
    file_cfg['path'] += '/'+get_data_str()
    pcview = PCView(ip, file_cfg)
    pcview.run()
