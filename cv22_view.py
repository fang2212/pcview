#.!/usr/bin/python
# -*- coding:utf8 -*-

import asyncio
import msgpack
import aiohttp
import argparse
import numpy as np
import os
from datetime import datetime
import cv2

def get_data_str():
    FORMAT = '%Y%m%d%H%M%S'
    return datetime.now().strftime(FORMAT)

def draw_text(img_content, text, position, size, color, thickness, type=cv2.LINE_AA):
    """
    For anti-aliased text, add argument cv2.LINE_AA.
    sample drawText(img_content, text, (20, 30), 0.6, CVColor.Blue, 2)
    """
    cv2.putText(img_content, text, position,
                cv2.FONT_HERSHEY_SIMPLEX, size, color,
                thickness, type)

class Recorder(object):
    def __init__(self, path=''):
        self._path = path
        self._writer = None

        if not os.path.exists(self._path):
            os.makedirs(self._path)
    
    def set_writer(self):
        pass
    
    def write(self, data):
        self._writer.write(data)

    def release(self):
        pass

pack = os.path.join
    
class VideoRecorder(Recorder):
    def __init__(self, path, fps=10):
        Recorder.__init__(self, path)
        self.fps = fps
    
    def set_writer(self, file_name, w=1280, h=720):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self._writer = cv2.VideoWriter(os.path.join(self._path, file_name+'.avi'),
                                       fourcc, self.fps, (w, h), True)
    
    def release(self):
        self._writer.release()

class FPSCnt(object):

    def __init__(self, period, fps):
        self.period = period
        self.start_time = None
        self.cnt = 0
        self.fps = fps
    
    def inc(self, step=1):
        if self.cnt % self.period == 0:
            if not self.start_time:
                self.start_time = datetime.now()
            else:
                temp = self.start_time
                self.start_time = datetime.now()
                delta = (self.start_time - temp).total_seconds()
                print(self.period, delta)
                self.fps = str("%.2f" % (self.period / delta))
        self.cnt += 1

async def main(ip, height, width, fps):
    session = aiohttp.ClientSession()
    B_S = width*height
    G_S = width*height*2
    R_S = width*height*3

    URL = 'ws://'+ip+':24011'
    fps_cnt = FPSCnt(20, 20)
    cnt = 0

    if fps:
        video_recorder = VideoRecorder('cv22_data', fps)
        video_recorder.set_writer(get_data_str(), width, height)

    async with session.ws_connect(URL) as ws:

        msg = {
            'source': 'pcview',
            'topic': 'subscribe',
            'data': 'image',
        }
        data = msgpack.packb(msg)
        await ws.send_bytes(data)
        async for msg in ws:
            data = msgpack.unpackb(msg.data)
            data = data[b'data']

            '''
            data = data[24:]
            image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
            '''
            B = data[0:B_S] 
            G = data[B_S:G_S] 
            R = data[G_S:R_S]
            image_B = np.fromstring(B, dtype=np.uint8).reshape(height, width, 1)
            image_G = np.fromstring(G, dtype=np.uint8).reshape(height, width, 1)
            image_R = np.fromstring(R, dtype=np.uint8).reshape(height, width, 1)
            image = cv2.merge([image_B,image_G,image_R])

            if fps:
                video_recorder.write(image)
                if cnt % 2000 == 0:
                    video_recorder.release()
                    video_recorder.set_writer(get_data_str(), width, height)
            cnt += 1
            fps_cnt.inc()

            draw_text(image, 'fps:'+str(fps_cnt.fps), (20, 20),
                      0.6, (255, 0, 0), 1)

            cv2.imshow('rgbshow', image)
            cv2.waitKey(1)

            if msg.type in (aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR):
                break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--w", help="image width", type=str)
    parser.add_argument("--h", help="image height", type=str)
    parser.add_argument("--ip", help="device ip", type=str)
    parser.add_argument("--fps", help="save video fps", type=str)
    args = parser.parse_args()
    ip = '192.168.0.231'
    h = 540
    w = 960
    fps = 0
    if args.fps:
        fps = int(args.fps)
    if args.h:
        h = int(args.h)
    if args.w:
        w = int(args.w)
    if args.ip:
        ip = args.ip

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(ip, h, w, fps))