#.!/usr/bin/python
# -*- coding:utf8 -*-

import time
import threading
import nanomsg
import msgpack
import json
from datetime import datetime
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Value
from .draw.base import BaseDraw
from .draw.base import CVColor
import os
import sys
                             
import numpy as np
import cv2
from .draw.ui_draw import Player
from ../etc/config import config

class FileHandle(Process):
    def __init__(self):
        Process.__init__(self)
        self.deamon = True
        self.log_queue = Queue()
        self.alert_queue = Queue()
        self.image_queue = Queue()
        self.video_queue = Queue()
        self._max_cnt = 7000
        path = config.save.path
 
        FORMAT = '%Y%m%d%H%M'
        date = datetime.now().strftime(FORMAT)
        self.path = os.path.join(path, date)
        os.makedirs(self.path)
 
        if config.save.log:
            self.log_fp = open(os.path.join(self.path, 'log.json'), 'w+')
        if config.save.alert:
            self.alert_fp = open(os.path.join(self.path, 'alert.json'), 'w+')
            self.image_path = os.path.join(self.path, 'image')
            os.makedirs(self.image_path)

        if config.save.video:
            self.video_writer = None
            self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.video_path = os.path.join(self.path, 'video')
            os.makedirs(self.video_path)

    def run(self):
        cnt = 0
        while True:
            # print('---fileHandle process id----', os.getpid())
            while config.save.log and not self.log_queue.empty():
                frame_id, data = self.log_queue.get() 
                self.log_fp.write(json.dumps(data) + '\n')
                self.log_fp.flush()
 
            if config.save.alert:
                while not self.alert_queue.empty():
                    frame_id, data = self.alert_queue.get()
                    self.alert_fp.write(json.dumps(data) + '\n')
                    self.alert_fp.flush()
 
                while not self.image_queue.empty():
                    image_index, data = self.image_queue.get() 
                    cv2.imwrite(os.path.join(self.image_path, str(image_index) + '.jpg'), data)
 
            while config.save.video and not self.video_queue.empty():
                frame_id, data = self.video_queue.get() 
                if cnt % self._max_cnt == 0:
                    if self.video_writer:
                        self.video_writer.release()
                    self.video_writer = cv2.VideoWriter(os.path.join(self.video_path, str(cnt)+'.avi'),
                            self.fourcc, 20.0, (1280, 720), True)
                self.video_writer.write(data)
                cnt += 1
            time.sleep(0.02)
 
    def insert_log(self, msg):
        self.log_queue.put(msg)

    def insert_alert(self, msg):
        self.alert_queue.put(msg)

    def insert_image(self, msg):
        self.image_queue.put(msg)

    def insert_video(self, msg):
        self.video_queue.put(msg)

class Sink(Process):
    def __init__(self, queue, ip, port=1200):
        Process.__init__(self)
        self.deamon = True
        self.port = port
        self.queue = queue
        self.q_max = 20
        self.cur_frame_id = -1

    def _init_socket(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (config.ip, self.port, ))

    def run(self):
        self._init_socket()
        while True:
            buf = nanomsg.wrapper.nn_recv(self._socket, 0)
            frame_id, data = self.pkg_handler(buf[1])

    def pkg_handler(self, msg_buf):
        pass

    def set_frame_id(self, frame_id):
        # This method must be called
        self.cur_frame_id = frame_id

class CameraSink(Sink):

    def __init__(self, queue, ip, port=1200):
        Sink.__init__(self, queue, ip, port)
        '''
        self.fp = open('/home/minieye/pc-viewer-data/c_id.txt', 'w+')
        self.cnt = 0
        '''

    def pkg_handler(self, msg):
        # print('c--process-id:', os.getpid())
        msg = memoryview(msg).tobytes()
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        data = msg[16:]
        # print('c id', frame_id)
        '''
        self.fp.write(str(frame_id)+'\n')
        self.cnt += 1
        if self.cnt % 10000 == 0:
            self.fp.flush()
        '''
        return frame_id, data

class LaneSink(Sink):

    def __init__(self, queue, ip, port=1203):
        Sink.__init__(self, queue, ip, port)
        '''
        self.fp = open('/home/minieye/pc-viewer-data/l_id.txt', 'w+')
        self.log_fp = open('/home/minieye/pc-viewer-data/lane.json', 'w+')
        self.cnt = 0
        '''

    def pkg_handler(self, msg):
        # print('l--process-id:', os.getpid())
        data = msgpack.loads(msg)
        self.set_frame_id(data[0])
        frame_id = data[0]
        res = dict()
        keys = [
            "frame_id", "deviate_state", "lanelines", "turn_radius",
            "speed_thresh", "turn_frequently", "left_wheel_dist",
            "right_wheel_dist", "warning_dist", "lateral_speed",
            "earliest_dist", "latest_dist", "deviate_trend",
            "success", "speed", "left_lamp", "right_lamp"]
        res = dict(zip(keys, data))
        line_keys = [
            "bird_view_poly_coeff", "perspective_view_poly_coeff",
            "confidence", "warning", "label", "color", "type", "width", "start", "end",
            "bird_view_pts"]
        lines = []
        for line in res["lanelines"]:
            ldict = dict(zip(line_keys, line))
            lines.append(ldict)
        res["lanelines"] = lines
        self.queue.put(('lane', res))
        # print('l id', frame_id)
        '''
        self.fp.write(str(frame_id)+'\n')
        self.log_fp.write(json.dumps(res)+'\n')
        self.cnt += 1
        if self.cnt % 10000 == 0:
            self.fp.flush()
            self.log_fp.flush()
        '''
        return frame_id, res

class VehicleSink(Sink):

    def __init__(self, queue, ip, port=1204):
        Sink.__init__(self, queue, ip, port)
        '''
        self.fp = open('/home/minieye/pc-viewer-data/v_id.txt', 'w+')
        self.log_fp = open('/home/minieye/pc-viewer-data/vehicle.json', 'w+')
        self.cnt = 0
        '''

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        self.set_frame_id(data[0])
        frame_id = data[0]
        res = dict()
        keys = [
            "frame_id", "dets", "focus_index", "light_mode", "weather", "wiper_on",
            "ttc", "forward_collision_warning", "headway_warning", "bumper_warning",
            "stop_and_go_warning", "warning_level", "warning_vehicle_index",
            "bumper_running", "bumper_state", "stop_and_go_state", "speed", "radius"]
        res = dict(zip(keys, data))
        det_keys = [
            "vertical_dist", "horizontal_dist", "ttc", "rel_ttc", "rel_speed",
            "speed_acc", "vehicle_width", "det_confidence", "rect", "bounding_rect",
            "index", "type", "warning_level", "count", "is_close", "on_route"]
        dets = []
        for det in res["dets"]:
            ddict = dict(zip(det_keys, det))
            dets.append(ddict)
        res["dets"] = dets
        self.queue.put(('vehicle', res))
        # print('v id', frame_id)
        '''
        self.fp.write(str(frame_id)+'\n')
        self.log_fp.write(json.dumps(res)+'\n')
        self.cnt += 1
        if self.cnt % 10000 == 0:
            self.fp.flush()
            self.log_fp.flush()
        '''
        return frame_id, res

class PedesSink(Sink):

    def __init__(self, queue, ip, port=1205):
        Sink.__init__(self, queue, ip, port)
        ''' 
        self.fp = open('/home/minieye/pc-viewer-data/p_id.txt', 'w+')
        self.log_fp = open('/home/minieye/pc-viewer-data/vehicle.json', 'w+')
        self.cnt = 0
        '''

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        # print('data:', data)
        self.set_frame_id(data[0])
        frame_id = data[0]
        res = dict()
        keys = ["frame_id", "pedestrains", "ped_on", "pcw_on"]
        res = dict(zip(keys, data))
        pedestrains_keys = [
            "detect_box", "regressed_box", "dist", "ttc", "is_danger",
            "is_key", "classify_type", "type_conf", "pcw_overlap",
            "work_overlap", "roi_num"
             ]
        pedestrains = []
        for pedestrain in res['pedestrains']:
            ddict = dict(zip(pedestrains_keys, pedestrain))
            pedestrains.append(ddict)
        res['pedestrains'] = pedestrains
        self.queue.put(('ped', res))
        '''
        self.fp.write(str(frame_id)+'\n')
        self.log_fp.write(json.dumps(res)+'\n')
        self.cnt += 1
        if self.cnt % 10000 == 0:
            self.fp.flush()
            self.log_fp.flush()
        '''
        return frame_id, res

class Hub(Process):
    
    def __init__(self):
        Process.__init__(self)
        self.msg_queue = Queue()
        self.msg_list = {
            'lane': [],
            'vehicle': [],
            'ped': [],
        }

        if config.pic.ispic:
            self.img_list =[]
            print('-------------------pic-------------------------------')
            self.camera_sink = CameraSink(queue=self.msg_queue, ip=ip, port=1200)
            self.camera_sink.start()
        else: 
            print('-------------------no_pic-------------------------------')
            image_fp = open(config.pic.path, 'r+')
            self.image_list = image_fp.readlines()
            image_fp.close()

        self.lane_sink = LaneSink(queue=self.msg_queue, ip=ip, port=1203)
        self.lane_sink.start()

        self.vehicle_sink = VehicleSink(queue=self.msg_queue, ip=ip, port=1204)
        self.vehicle_sink.start()
        
        self.pedes_sink = PedesSink(queue=self.msg_queue, ip=ip, port=1205)
        self.pedes_sink.start()

    def list_len(self):
        length = 0
        for key in self.msg_list:
            lenght += len(self.msg_list[key])
            return length
    def all_has(self):
        for key in self.msg_list:
            if not self.msg_list[key]:
                return False
        return True

    def pop(self):
        res = {
            'frame_id': None,
            'img': None,
            'vehicle_data': {},
            'lane_data': {},
            'pedes_data': {},
        }
        while True:
            if not config.pic.ispic:
                # print('-------------------no__pic-------------------------------')
                while not self.all_has() and self.list_len() < 10:
                    while not self.msg_queue.empty():
                        msg_type, msg_data = self.msg_queue.get()
                        self.msg_list[msg_type].append((msg_data['frame_id'], msg_data))
                    time.sleep(0.02)

                lane_id, vehicle_id, pedes_id = sys.maxsize,sys.maxsize,sys.maxsize

                if len(self.msg_list['lane'])>0:
                    lane_id, lane_data = self.msg_list['lane'][0]
                if len(self.msg_list['vehicle'])>0:
                    vehicle_id, vehicle_data = self.msg_list['vehicle'][0]
                if len(self.msg_list['ped'])>0:
                    pedes_id, pedes_data = self.msg_list['ped'][0]

                frame_id = min(min(lane_id, vehicle_id), pedes_id)
              
                if frame_id == sys.maxsize:
                    time.sleep(0.02)
                    continue
                
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
                    res['pedes_data'] = pedes_data
                    self.msg_list['ped'].pop(0)
            
                return res         
            
            else:
                while len(self.img_list) <= 0:
                    while not self.msg_queue.empty():
                        msg_type, msg_data = self.msg_queue.get()
                        if msg_type == 'img':
                            self.img_list.append((msg_data['frame_id'], msg_data))
                            break
                        else:
                            self.msg_list[msg_type].append((msg_data['frame_id'],
                                msg_data))
                    time.sleep(0.02)

                while not self.all_has() and self.list_len() < 10:
                    while not self.msg_queue.empty():
                        msg_type, msg_data = self.msg_queue.get()
                        self.msg_list[msg_type].append((msg_data['frame_id'], msg_data))
                    time.sleep(0.02)

                lane_id, vehicle_id, pedes_id = sys.maxsize,sys.maxsize,sys.maxsize

                if len(self.msg_list['lane'])>0:
                    lane_id, lane_data = self.msg_list['lane'][0]
                if len(self.msg_list['vehicle'])>0:
                    vehicle_id, vehicle_data = self.msg_list['vehicle'][0]
                if len(self.msg_list['ped'])>0:
                    pedes_id, pedes_data = self.msg_list['ped'][0]

                temp_id = min(min(lane_id, vehicle_id), pedes_id)
              
                if temp_id == sys.maxsize:
                    time.sleep(0.02)
                    continue
                
                frame_id, img_data = self.img_list.pop(0)
                img_gray = np.fromstring(img_data, dtype=np.uint8).reshape(720, 1280, 1)
                img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
                res['img'] = img

                res['frame_id'] = frame_id
                if lane_id == frame_id:
                    res['lane_data'] = lane_data
                    self.msg_list['lane'].pop(0)
                if vehicle_id == frame_id:
                    res['vehicle_data'] = vehicle_data
                    self.msg_list['vehicle'].pop(0)
                if pedes_id == frame_id:
                    res['pedes_data'] = pedes_data
                    self.msg_list['ped'].pop(0)
            
                return res         

class PCViewer():
    """pc-viewer功能类，用于接收每一帧数据，并绘制

    Attributes:
       ip: 数据源设备的ip地址
       save_origin_image: 是否保存原始图片
       save_result_image: 是否保存处理图片
       queue: 存储每一帧数据
       player: 图片播放器
    """
    def __init__(self):
        self.hub = None
        self.player = Player()
        self.exit = False

        self.pre_lane = {}
        self.pre_vehicle = {}
        self.lane_cnt = 0
        self.vehicle_cnt = 0

        if config.mobile.show:
            mobile_fp = open(config.mobile.path, 'r+')
            self.mobile_content = json.load(mobile_fp)
            print('moible_len:', len(self.mobile_content))
            mobile_fp.close()
        
        if config.save.log or config.save.alert or config.save.video:
            self.fileHandler = FileHandle()
            self.fileHandler.start()
    
    def start(self):
        self.hub = Hub()
        self.start_time = datetime.now()
        bool = 1
        frame_cnt = 0

        while not self.exit:
            d = self.hub.pop()
            if not d.get('frame_id'):
                continue
            frame_cnt += 1
            self.draw(d, frame_cnt)
            if frame_cnt >= 100:
                self.start_time = datetime.now()
                frame_cnt = 0

    def draw(self, mess, frame_cnt):
        vehicle_data = mess['vehicle_data']
        lane_data = mess['lane_data']
        pedes_data = mess['pedes_data']
        img = mess['img']
        frame_id = mess['frame_id']

        '''
        # 连续处理
        if not lane_data:
            if self.lane_cnt == 0:
                lane_data = self.pre_lane
                self.lane_cnt += 1
                self.pre_lane = {}
        else:
            self.pre_lane = lane_data
            self.lane_cnt = 0

        if not vehicle_data:
            if self.vehicle_cnt == 0:
                vehicle_data = self.pre_vehicle
                self.vehicle_cnt += 1
                self.pre_vehicle = {}
        else:
            self.pre_vehicle = vehicle_data
            self.vehicle_cnt = 0
        '''
        
        temp_mess = mess
        temp_mess.pop('img')
        if config.save.log:
            self.fileHandler.insert_log((frame_id, temp_mess))

        self.player.show_overlook_background(img)
        if config.show_mobile:
            bg_width = 120 * 5
        else:
            bg_width = 120 * 3
        self.player.show_parameters_background(img, (0, 0, bg_width, 170))

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        duration = duration if duration > 0 else 1
        fps = frame_cnt / duration

        alert = {}
        speed = 0
        light_mode = -1

        # vehicle
        v_type, index, ttc, fcw ,hwm, hw, vb = '-','-','-','-','-','-','-'
        warning_level, alert_ttc, hw_state, fcw_state, vb_state, sg_state = 0,0,0,0,0,0
        if vehicle_data:
            focus_index = vehicle_data['focus_index']
            speed = vehicle_data['speed'] * 3.6
            light_mode = vehicle_data['light_mode']
            for i, vehicle in enumerate(vehicle_data['dets']):
                focus_vehicle = (i == focus_index)
                position = vehicle['bounding_rect']
                
                color = CVColor.Red if focus_index == i else CVColor.Cyan
                self.player.show_vehicle(img, position, color, 2)
                
                self.player.show_vehicle_info(img, position,
                                        vehicle['vertical_dist'],vehicle['horizontal_dist'], 
                                        vehicle['vehicle_width'], str(vehicle['type']))
                self.player.show_overlook_vehicle(img, focus_vehicle,
                                            vehicle['vertical_dist'],
                                            vehicle['horizontal_dist'])
                
            if focus_index != -1:
                vehicle = vehicle_data['dets'][focus_index]
                v_type = vehicle['type']
                index = vehicle['index']
                ttc = '%.2f' % vehicle['rel_ttc']
                fcw = vehicle_data['forward_collision_warning']
                fcw_state = vehicle_data['forward_collision_warning']
                hw = vehicle_data['headway_warning']
                hw_state = vehicle_data['headway_warning']
                hwm = '%.2f' % vehicle_data['ttc']
                vb = vehicle_data['bumper_warning']
                vb_state = vehicle_data['bumper_state']
                sg_state = vehicle_data['stop_and_go_state']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                warning_level = vehicle_data['warning_level']
                if ttc == '1000.00':
                    ttc = '-'
        parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
        self.player.show_vehicle_parameters(img, parameters, (120, 0))
        alert['ttc'] = float(alert_ttc)
        alert['warning_level'] = int(warning_level)
        alert['hw_state'] = int(hw_state)
        alert['fcw_state'] = int(fcw_state)
        alert['vb_state'] = int(vb_state)
        alert['sg_state'] = int(sg_state)
                    
        # lane
        lw_dis, rw_dis, ldw, trend = '-', '-', '-', '-'
        lane_warning = 0
        if lane_data:
            speed = lane_data['speed']
            for lane in lane_data['lanelines']:
                if int(lane['label']) in [1, 2] and speed > 30:
                    Color = {
                        '0': CVColor.Red,
                        '1': CVColor.Green,
                        '2': CVColor.Cyan,
                        '3': CVColor.Magenta,
                        '4': CVColor.Yellow,
                        '5': CVColor.Black,
                        '6': CVColor.White,
                        '7': CVColor.Pink,
                    }
                    color = Color[str(lane['color'])]
                    width = lane['width']
                    l_type = lane['type']
                    conf = lane['confidence']
                    index = lane['label']
                    self.player.show_lane(img, lane['perspective_view_poly_coeff'], width, color)
                    self.player.show_overlook_lane(img, lane['bird_view_poly_coeff'], color)
                    self.player.show_lane_info(img, lane['perspective_view_poly_coeff'], index, width, l_type, conf, color)

            lw_dis = '%.2f' % (lane_data['left_wheel_dist'])
            rw_dis = '%.2f' % (lane_data['right_wheel_dist'])
            ldw = lane_data['deviate_state']
            lane_warning = lane_data['deviate_state']
            trend = lane_data['deviate_trend']
            if lw_dis == '111.00':
                lw_dis = '-'
            if rw_dis == '111.00':
                rw_dis = '-'

        # pedestrains
        if pedes_data:
            for pedestrain in pedes_data['pedestrains']:
                position = pedestrain['regressed_box']
                self.player.show_pedestrains(img, position, CVColor.Yellow, 2)

        parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
        if self.show_mobile_info:
            lane_y = 120 * 3
        else:
            lane_y = 120 * 2
        self.player.show_lane_parameters(img, parameters, (lane_y, 0))
        self.player.show_env(img, speed, light_mode, fps, (0, 0))
        alert['lane_warning'] = lane_warning
        alert['speed'] = float('%.2f' % speed)

        
        index = int(frame_id/3)*4+frame_id%3
        if self.show_mobile_info:
            mobile_ldw, mobile_hw, mobile_fcw, mobile_vb, mobile_hwm = '-', '-', '-', '-', '-'
            mobile_log = self.mobile_content[index]
            if mobile_log:
                mobile_hwm = mobile_log.get('headway_measurement') if mobile_log.get('headway_measurement') else 0
                mobile_hw = 1 if mobile_log.get('sound_type') == 3 else 0
                mobile_fcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('fcw_on') == 1 else 0
                mobile_vb = 1 if mobile_log.get('sound_type') == 5 else 0
                mobile_ldw = mobile_log['left_ldw'] * 2 + mobile_log['right_ldw'] if 'left_ldw' in mobile_log else 0

            mobile_parameters = [str(mobile_hwm), str(mobile_hw), str(mobile_fcw), str(mobile_vb), str(mobile_ldw)]
            self.player.show_mobile_parameters(img, mobile_parameters, (120*2, 0))
            

        if config.save.alert:
            self.fileHandler.insert_alert((frame_id, {index: alert}))
            self.fileHandler.insert_image((index, img))
        if config.save.video:
            self.fileHandler.insert_video((frame_id, img))
        cv2.imshow('UI', img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            self.exit = True
        elif key == 27:
            cv2.destroyAllWindows()
            self.exit = True

    def test(self):
        """用于测试，读取离线数据"""
        path = ""
        fp = open(os.path.join(path, 'log.json'), 'r')
        log_contents = fp.readlines()
        fp.close()
        
        frame_cnt = 0
        self.start_time = datetime.now()
        for data in log_contents:
            frame_cnt += 1
            if not self.exit:
                data = json.loads(data)
                img_path = os.path.join(path, str(data['frame_id']) + '.jpg')
                if not os.path.exists(img_path):
                    continue
                img = cv2.imread(img_path)
                data = {
                    'frame_id': data['frame_id'],
                    'img': img,
                    'lane_data': data['lane_data'],
                    'vehicle_data': data['vehicle_data']
                }
                self.draw(data, frame_cnt)
            else:
                break
