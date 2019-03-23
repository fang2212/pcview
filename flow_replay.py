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

from player import FlowPlayer
from sink import FlowReader 
from recorder import VideoRecorder, TextRecorder

def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

def main():
    reader = FlowReader(r'E:\temp\20190322171339-Base02-CIZQ\pcview_data')
    player = FlowPlayer()
    while True:
        success, image, mess = reader.output()
        if not success:
            continue
        player.draw(mess, image)
        if 'frame_id' not in mess:
            print(image, mess)
        else:
            print(mess['frame_id'])
        cv2.imshow('hello', image)
        cv2.waitKey(100)

    
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
