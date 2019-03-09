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
from sink import NanoSink
from recorder import VideoRecorder, TextRecorder

def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

class PCView():
    
    def __init__(self, ip, file_cfg):
        self.msg_queue = Queue()

        self.pc_draw = PCDraw(self.msg_queue, file_cfg)
        self.pc_draw.start()

    
    def run(self):
        # FlowSink.open_libflow_sink(ip, self.msg_queue)
        tcp_sink = NanoSink('127.0.0.1', 12032, self.msg_queue)
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
        self.save_path = file_cfg['path']

    def run(self):
        player = ClientPlayer()
        if self.save_video:
            video_recorder = VideoRecorder(self.save_path, 20)
            video_recorder.set_writer(get_data_str())

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
                if 'img' not in mess:
                    continue

                cnt += 1
                try:
                    image = player.draw(mess)
                except Exception as err:
                    cv2.imwrite('error/error.jpg', img)
                    continue

                cv2.imshow('UI', image)
                cv2.waitKey(1)

                if self.save_video:
                    video_recorder.write(image)
                '''
                print('frame_id', frame_id)
                print(mess)
                '''
                
                if cnt % 6000 == 0:
                    if self.save_video:
                        video_recorder.release()
                        video_recorder.set_writer(get_data_str())

            time.sleep(0.01)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
    parser.add_argument("--log", help="是否保存日志[0,1],默认保存", type=str)
    parser.add_argument("--path", help="保存地址", type=str)
    args = parser.parse_args()
    ip = '127.0.0.1'
    file_cfg = {
        'video': 1,
        'log': 1,
        'path': 'pcview_data',
    }
    if args.video:
        file_cfg['video'] = int(args.video)
    if args.log:
        file_cfg['log'] = int(args.log)
    if args.path:
        file_cfg['path'] = args.path
    pcview = PCView(ip, file_cfg)
    pcview.run()
