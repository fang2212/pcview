#!/usr/bin/python
# -*- coding -*-

import sys
import time
import cv2
import numpy as np
from etc.config import config
from multiprocessing import Queue
from .sink_mtk import MtkSink
from .sink_fpga import CameraSink,LaneSink,VehicleSink,PedSink,TsrSink

class Hub():
    def __init__(self):
        self.msg_queue = Queue()
        self.msg_list = {
            'lane': [],
            'vehicle': [],
            'ped': [],
            'tsr': [],
        }
        
        if not config.pic.ispic:
            image_fp = open(config.pic.path, 'r+')
            self.image_list = image_fp.readlines()
            image_fp.close()
    
    # 开始接收数据
    def start(self):
        pass

    def list_len(self):
        length = 0
        for key in self.msg_list:
            length += len(self.msg_list[key])
            return length
    def all_has(self):
        for key in self.msg_list:
            if not self.msg_list[key]:
                return False
        return True

    def push_msg(self):
        cnt = 3
        while cnt >= 0:
            if not self.msg_queue.empty():
                msg_type, msg_data = self.msg_queue.get()
                if msg_type == 'img':
                    frame_id = int.from_bytes(msg_data[4:8], byteorder="little", signed=False)
                    data = msg_data[16:]
                    self.img_list.append((frame_id, data))
                    break
                else:
                    self.msg_list[msg_type].append((msg_data['frame_id'], msg_data))
            cnt -= 1

    def get_res_pic(self, res):
        while len(self.img_list) <= 0:
            self.push_msg()
            time.sleep(0.02)
        frame_id, img_data = self.img_list.pop(0)
        img_gray = np.fromstring(img_data, dtype=np.uint8).reshape(720, 1280, 1)
        img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
 
        while not self.all_has() and self.list_len() < 10:
            self.push_msg()
            time.sleep(0.02)
        
        while len(self.msg_list['ped']) > 0 and self.msg_list['ped'][0][0] <= frame_id:
            ped_id, ped_data = self.msg_list['ped'].pop(0)
            if ped_id == frame_id:
                res['ped_data'] = ped_data
                break

        while len(self.msg_list['lane']) > 0 and self.msg_list['lane'][0][0] <= frame_id:
            lane_id, lane_data = self.msg_list['lane'].pop(0)
            if lane_id == frame_id:
                res['lane_data'] = lane_data
                break

        while len(self.msg_list['vehicle']) > 0 and self.msg_list['vehicle'][0][0] <= frame_id:
            vehicle_id, vehicle_data = self.msg_list['vehicle'].pop(0)
            if vehicle_id == frame_id:
                res['vehicle_data'] = vehicle_data
                break

        while len(self.msg_list['tsr']) > 0 and self.msg_list['tsr'][0][0] <= frame_id:
            tsr_id, tsr_data = self.msg_list['tsr'].pop(0)
            if tsr_id == frame_id:
                res['tsr_data'] = tsr_data
                break
        res['frame_id'] = frame_id
        res['img'] = img
        
        return res
    
    def get_res_nopic(self, res):
        while not self.all_has() and self.list_len() < 12:
            self.push_msg()
            time.sleep(0.02)
        
        lane_id, vehicle_id, pedes_id, tsr_id = sys.maxsize,sys.maxsize,sys.maxsize,sys.maxsize
        if len(self.msg_list['lane'])>0:
            lane_id, lane_data = self.msg_list['lane'][0]
        if len(self.msg_list['vehicle'])>0:
            vehicle_id, vehicle_data = self.msg_list['vehicle'][0]
        if len(self.msg_list['ped'])>0:
            pedes_id, pedes_data = self.msg_list['ped'][0]
        if len(self.msg_list['tsr'])>0:
            tsr_id, tsr_data = self.msg_list['tsr'][0]

        frame_id = min(min(min(lane_id, vehicle_id), pedes_id), tsr_id)

        if frame_id == sys.maxsize:
            res['frame_id'] = sys.maxsize
            return res

        index = ((frame_id//3)*4+frame_id%3) % len(self.image_list)
        image_path = self.image_list[index]
        image_path = image_path.strip()
        img = cv2.imread(image_path)
        res['frame_id'] = frame_id
        res['img'] = img
        if lane_id == frame_id:
            res['lane_data'] = lane_data
            self.msg_list['lane'].pop(0)
        if vehicle_id == frame_id:
            res['vehicle_data'] = vehicle_data
            self.msg_list['vehicle'].pop(0)
        if pedes_id == frame_id:
            res['ped_data'] = pedes_data
            self.msg_list['ped'].pop(0)
        if tsr_id == frame_id:
            res['tsr_data'] = tsr_data
            self.msg_list['tsr'].pop(0)
        return res

    def pop(self):
        res = {
            'frame_id': None,
            'img': None,
            'vehicle_data': {},
            'lane_data': {},
            'ped_data': {},
            'tsr_data': {},
        }
        while True:
            if config.pic.ispic: # 传图情况获取frame_id, img
                res = self.get_res_pic(res)
            else:
                res = self.get_res_nopic(res)
            # print('res:', res)
            if res['frame_id'] == sys.maxsize:
                continue
            return res

class MtkHub(Hub):
    def __init__(self):
        Hub.__init__(self)

    def start(self):
        sink = MtkSink(self.msg_queue)
        sink.start()

class FpgaHub(Hub):
    def __init__(self):
        Hub.__init__(self)

    def start(self):
        if config.pic.ispic:
            self.img_list =[]
            camera_sink = CameraSink(queue=self.msg_queue, port=1200)
            camera_sink.start()
        lane_sink = LaneSink(queue=self.msg_queue, port=1203)
        lane_sink.start()

        vehicle_sink = VehicleSink(queue=self.msg_queue, port=1204)
        vehicle_sink.start()

        ped_sink = PedSink(queue=self.msg_queue, port=1205)
        ped_sink.start()
        
        tsr_sink = TsrSink(queue=self.msg_queue, port=1206)
        tsr_sink.start()
