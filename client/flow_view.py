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
from datetime import datetime
from multiprocessing import Process, Queue, Value

from ui import DrawVehicle, DrawPed, CVColor, FPSCnt
from msg_sink import FlowSink, SinkError
from recorder import VideoRecorder, TextRecorder
from player import FlowPlayer

def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

class PCView():
    
    def __init__(self, ip, file_cfg):
        self.msg_queue = Queue()

        self.pc_draw = PCDraw(self.msg_queue, file_cfg)
        self.pc_draw.start()

        FlowSink.open_libflow_sink(ip, self.msg_queue)


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
        player = FlowPlayer()
        if self.save_log:
            text_recorder = TextRecorder(self.save_path)
            text_recorder.set_writer(get_data_str())
        if self.save_video:
            video_recorder = VideoRecorder(self.save_path)
            video_recorder.set_writer(get_data_str())

        fps_cnt = FPSCnt(10, 0)
        cnt = 0

        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                if mess == SinkError.Closed:
                    print('close')
                    if self.save_video:
                        video_recorder.release()
                    if self.save_log:
                        text_recorder.release()
                    cv2.destroyAllWindows()
                    return

                if 'frame_id' not in mess:
                    continue
                if 'camera' not in mess:
                    continue
                # print(mess)

                cnt += 1
                fps_cnt.inc()

                frame_id = mess['frame_id']
                mess['env'] = {
                    'fps': fps_cnt.fps
                }
                # draw now id
                image = mess['camera']['image']
                player.draw(mess, image)
                cv2.imshow('UI', image)
                cv2.waitKey(1)

                if self.save_video:
                    video_recorder.write(image)
                del mess['camera']['image']
                print('frame_id', frame_id)
                print(mess)
                if self.save_log:
                    text_recorder.write(json.dumps(mess)+'\n')
                
                if cnt % 500 == 0:
                    if self.save_video:
                        video_recorder.release()
                        video_recorder.set_writer(get_data_str())
                    if self.save_log:
                        text_recorder.release()
                        text_recorder.set_writer(get_data_str())

            time.sleep(0.01)
        cv2.destroyAllWindows()
    
if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    else:
        ip = '127.0.0.1'

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="设备ip address，默认192.168.0.233", type=str)
    parser.add_argument("--video", help="是否保存视频[0,1]，默认保存", type=str)
    parser.add_argument("--log", help="是否保存日志[0,1],默认保存", type=str)
    parser.add_argument("--path", help="保存地址", type=str)
    args = parser.parse_args()
    ip = '127.0.0.1'
    if args.ip:
        ip = args.ip
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
