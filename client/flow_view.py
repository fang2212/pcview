#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import logging
import time
import msgpack
import json
import cv2
from datetime import datetime
from multiprocessing import Process, Queue, Value

from ui import DrawVehicle, DrawPed, CVColor
from msg_sink import FlowSink, SinkError
from recorder import VideoRecorder, TextRecorder
from player import FlowPlayer

def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

class PCView():
    
    def __init__(self, ip):
        self.msg_queue = Queue()

        self.pc_draw = PCDraw(self.msg_queue)
        self.pc_draw.start()

        FlowSink.open_libflow_sink(ip, self.msg_queue)


class PCDraw(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue

    def run(self):
        player = FlowPlayer()
        text_recorder = TextRecorder('log')
        text_recorder.set_writer(get_data_str())
        video_recorder = VideoRecorder('video')
        video_recorder.set_writer(get_data_str())

        cnt = 0
  
        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                if mess == SinkError.Closed:
                    print('close')
                    video_recorder.release()
                    text_recorder.release()
                    cv2.destroyAllWindows()
                    return

                if 'frame_id' not in mess:
                    continue
                if 'camera' not in mess:
                    continue
                # print(mess)

                cnt += 1

                frame_id = mess['frame_id']
                print(frame_id)
                image = mess['camera']['image']
                player.draw(mess, image)
                cv2.imshow('UI', image)
                cv2.waitKey(1)

                video_recorder.write(image)
                del mess['camera']['image']
                text_recorder.write(json.dumps(mess)+'\n')
                
                if cnt % 500 == 0:
                    video_recorder.release()
                    video_recorder.set_writer(get_data_str())
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
    pcview = PCView(ip)

    # python flow_view.py 192.168.10.118 static/rec_20180530_172935_04_41.mp4