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

from player import FlowPlayer, BaseDraw
from sink import FlowReader 
from recorder import VideoRecorder, TextRecorder


def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)


def main():
    reader = FlowReader(r'E:\temp\lanebug0325')
    player = FlowPlayer()
    while True:
        success, image, mess = reader.output()
        if not success:
            continue
        player.draw(mess, image)
        frame_id = mess.get('frame_id')
        if frame_id >= 22720 and frame_id <= 22745:
            pass
        else:
            continue
        if 'lane' in mess:
            data = mess['lane']
            for lane in data:
                index = lane['label']
                begin = int(lane['end'][1])
                ratios = lane['perspective_view_poly_coeff']
                a0, a1, a2, a3 = list(map(float, ratios))
                y1 = begin
                x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
                BaseDraw.draw_text(image, str(index), (x1, y1), 1, (255, 0, 0), 2)

        if 'frame_id' not in mess:
            print(image, mess)
        else:
            print(mess['frame_id'])
        cv2.imshow('hello', image)
        key = cv2.waitKey(200)
        print(key)

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
    parser.add_argument("--log", help="是否保存日志[0,1],默认保存", type=str)
    parser.add_argument("--path", help="保存地址", type=str)
    parser.add_argument("--ip", help="msg_fd地址", type=str)
    parser.add_argument("--lane_pts", help="", type=str)
    args = parser.parse_args()

    '''
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
    '''
    main()
