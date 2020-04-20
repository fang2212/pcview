# !/usr/bin/python
# -*- coding:utf8 -*-

import socket
import time
import json
from threading import Thread
from queue import Queue

import numpy as np
import cv2


BUF_SIZE = 1280*720*20
class TcpSink(object):
    def __init__(self, ip, port, mess_queue):
        self.ip = ip
        self.port = port
        self.queue = mess_queue
        self.pre_id = None
        self.cache = []
        self.go = True
        self.msg_list = ['camera', 'lane', 'vehicle', 'tsr', 'ped']
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.connect((self.ip, self.port))

    def read_msg(self):
        buf = self.read(4)
        size = int.from_bytes(buf, byteorder="big", signed=False)
        buf = self.read(size)
        return buf

    def read(self, need_len):
        res = b''
        while need_len and self.go:
            if not self.cache:
                self.recv()
            len0 = len(self.cache[0])
            if len0 <= need_len:
                need_len -= len0
                res += self.cache[0]
                self.cache.pop(0)
            else:
                res += self.cache[0][0:need_len]
                self.cache[0] = self.cache[0][need_len:]
                need_len = 0
        return res
    
    def recv(self):
        tmp_buf = self.s.recv(BUF_SIZE)
        if not tmp_buf:
            self.go = False
            self.s.close()
            return
        self.cache.append(tmp_buf)

    def run(self):
        while self.go:
            res = {
                'frame_id': None,
                'img': None,
                'vehicle': {},
                'lane': {},
                'ped': {},
                'tsr': {},
            }
            ok = False
            for msg_type in self.msg_list:
                buf = self.read_msg()
                if len(buf) > 5:
                    if msg_type == 'camera':
                        frame_id, data = self.pkg_camera(buf)
                        res['img'] = data
                        ok = True
                    else:
                        frame_id, data = self.pkg_json(buf)
                        res[msg_type] = data
                    res['frame_id'] = frame_id
            # print('frame_id', res)
            if ok:
                self.queue.put(res)
                # print(res)

    def pkg_json(self, msg):
        res = json.loads(msg)
        frame_id = res['frame_id']
        #print('json', res)
        return frame_id, res

    def pkg_camera(self, msg):
        # frame_id = int.from_bytes(msg[16:20], byteorder="little", signed=False)
        # frame_id = int.from_bytes(msg[0:4], byteorder="little", signed=False)
        frame_id = 0
        # data = msg[4:]
        image = cv2.imdecode(np.fromstring(msg, np.uint8), cv2.IMREAD_COLOR)
        '''
        if self.pre_id and frame_id-self.pre_id != 1:
            print('jump: ', frame_id-self.pre_id)
        self.pre_id = frame_id
        '''
        return frame_id, image


class PCView(object):
    
    def __init__(self):
        self.res_queue = Queue() #处理结果，绘图数据队列

        # self.tcp_sink = TcpSink(ip='192.168.10.154', port=12032, mess_queue=self.res_queue) #从nanomsg接收图像
        self.tcp_sink = TcpSink(ip='127.0.0.1', port=12032, mess_queue=self.res_queue) #从nanomsg接收图像
        
        self.pc_draw = PCDraw(mess_queue=self.res_queue) #绘图进程

    def go(self):
        self.pc_draw.start()
        self.tcp_sink.run()

class CVColor(object):
    '''
    basic color RGB define
    '''
    Red = (0, 0, 255)
    Green = (0, 255, 0)
    Blue = (255, 0, 0)
    Cyan = (255, 255, 0)
    Magenta = (255, 0, 255)
    Yellow = (0, 255, 255)
    Black = (0, 0, 0)
    White = (255, 255, 255)
    Pink = (255, 0, 255)

class BaseDraw(object):
    """
    基本的opencv绘图函数
    """
    @classmethod
    def draw_rect(cls, img_content, point1, point2, color, thickness=2):
        cv2.rectangle(img_content, point1, point2, color, thickness)

    @classmethod
    def draw_line(cls, img_content, p1, p2,  color_type = CVColor.White, thickness=1, type=cv2.LINE_8):
        cv2.line(img_content, p1, p2, color_type, thickness, type, 0)

class PCDraw(Thread):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue):
        Thread.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        print('init draw')

    def draw_lane(self, img, lane_data):
        if lane_data:
            for lane in lane_data['lanelines']:
                ratios = lane['perspective_view_poly_coeff']
                a0, a1, a2, a3 = list(map(float, ratios))
                for y in range(450, 720, 20):
                    y1 = y
                    y2 = y1 + 20
                    x1 = (int)(a0 + a1 * y1 + a2 * y1 * y1 + a3 * y1 * y1 * y1)
                    x2 = (int)(a0 + a1 * y2 + a2 * y2 * y2 + a3 * y2 * y2 * y2)            
                    BaseDraw.draw_line(img, (x1, y1), (x2, y2), CVColor.Blue, 2)

    def draw_vehicle(self, img, vehicle_data):
        if vehicle_data:
            for vehicle in vehicle_data['dets']:
                position = vehicle['bounding_rect']
                x, y, width, height = position['x'], position['y'], position['width'], position['height']
                x1 = int(x)
                y1 = int(y)
                width = int(width)
                height = int(height)
                x2 = x1 + width
                y2 = y1 + height
                BaseDraw.draw_rect(img, (x1, y1), (x2, y2), CVColor.Green, 2)

    def draw_ped(self, img, ped_data):
        if ped_data:
            for pedestrain in ped_data['pedestrians']:
                position = pedestrain['regressed_box']
                position = position['x'], position['y'], position['width'], position['height']
                x1, y1, width, height = list(map(int, position))
                BaseDraw.draw_rect(img, (x1, y1), (x1+width, y1+height), CVColor.Red, 2)

    def draw_tsr(self, img, tsr_data):
        if tsr_data:
            for tsr in tsr_data['dets']:
                position = tsr['position']
                position = position['x'], position['y'], position['width'], position['height']
                x1, y1, width, height = list(map(int, position))
                BaseDraw.draw_rect(img, (x1, y1), (x1+width, y1+height), CVColor.Yellow, 2)

    def run(self):
        print('run abcdef')
        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                print('draw process', mess['frame_id'])
                img = mess.get('img')
                if 'vehicle' in mess:
                    self.draw_vehicle(img, mess.get('vehicle'))
                if 'lane' in mess:
                    self.draw_lane(img, mess.get('lane'))
                if 'ped' in mess:
                    self.draw_ped(img, mess.get('ped'))
                if 'tsr' in mess:
                    self.draw_tsr(img, mess.get('tsr'))
                cv2.imshow('UI', img)
                cv2.waitKey(1)
            time.sleep(0.02)
        cv2.destroyAllWindows()

if __name__ == '__main__':
    pcview = PCView()
    pcview.go()