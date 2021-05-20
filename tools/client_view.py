#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
# import logging
import time
import json
import cv2
import argparse
from datetime import datetime
from multiprocessing import Process, Queue, Value

if sys.platform == 'win32':
    from threading import Thread as Process
    print('win32 platform')
else:
    print('linux platform')

from player import FPSCnt, ClientPlayer
from sink import NanoSink, fix_all
from recorder import VideoRecorder, TextRecorder, get_data_str
from config import recorder_cfg, player_cfg, merge



class PCDraw(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue, cfg, video_recorder=None):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        self.video_recorder = video_recorder
        self.cfg = cfg
        self.pre_ = {
            'vehicle': {},
            'lane': {},
            'ped': {},
            'tsr': {}
        }

    def run(self):
        player = ClientPlayer(self.cfg)
        video_recorder = self.video_recorder
        cnt = 0
        if video_recorder:
            video_recorder.set_writer(get_data_str())

        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                # print(mess)

                if 'frame_id' not in mess:
                    continue
                if 'img' not in mess:
                    continue
                fix_all(self.pre_, mess, 5)

                cnt += 1
                try:
                    image = player.draw(mess)
                except Exception as err:
                    cv2.imwrite('error/error.jpg', img)
                    continue

                cv2.imshow('UI', image)
                cv2.waitKey(1)

                if self.video_recorder:
                    video_recorder.write(image)
                '''
                print('frame_id', frame_id)
                print(mess)
                '''
                
                if cnt % 6000 == 0:
                    if self.video_recorder:
                        video_recorder.release()
                        video_recorder.set_writer(get_data_str())

            time.sleep(0.01)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    try:
        if os.path.exists('client_cfg.json'):
            with open('client_cfg.json', 'r+') as fp:
                local_cfg = json.loads(fp.read())
                # print(local_cfg)
                recorder_cfg = merge(recorder_cfg, local_cfg.get('recorder'))
                player_cfg = merge(player_cfg, local_cfg.get('player'))
    except Exception as error:
        print(error)

    # print(recorder_cfg)
    # print(player_cfg)
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
    parser.add_argument("--log", help="是否保存日志[0,1],默认保存", type=str)
    parser.add_argument("--path", help="保存地址", type=str)
    args = parser.parse_args()
    ip = '127.0.0.1'
    if args.video:
        recorder_cfg['video'] = int(args.video)
    if args.log:
        recorder_cfg['log'] = int(args.log)
    if args.path:
        recorder_cfg['path'] = args.path

    if recorder_cfg.get('video'):
        video_recorder = VideoRecorder(recorder_cfg['path'], 30)
    else:
        video_recorder = None
    msg_queue = Queue()
    pc_draw = PCDraw(msg_queue, player_cfg, video_recorder)
    pc_draw.start()
    tcp_sink = NanoSink('127.0.0.1', 12032, msg_queue)
    tcp_sink.run()