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

import numpy as np
import cv2
from .draw.ui_draw import Player

class FileHandle(Process):
    def __init__(self, path):
        Process.__init__(self)
        self.deamon = True
        #threading.Thread.__init__(self)
        self.queue = Queue()
        self.path = path
        self._max_cnt = 6000
        FORMAT = '%Y%m%d%H%M'
        date = datetime.now().strftime(FORMAT)
        self.path = os.path.join(path, date)

    def run(self):
        cnt = 0
        while True:
            while not self.queue.empty():
                frame_id, data = self.queue.get() 
                #cv2.imwrite('out/'+ str(frame_id) + '.jpg', image)
                self.handler(data,frame_id, cnt)
                cnt += 1
            time.sleep(0.02)

    def insert(self, msg):
        self.queue.put(msg)

    def handler(self, data, frame_id, cnt):
        pass

class LogHandle(FileHandle):

    def __init__(self, path, type):
        FileHandle.__init__(self, path)
        self.type = type
        self.log_fp = None
        self.file_path = os.path.join(self.path, self.type)
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

    def handler(self, data, frame_id, cnt):
        if cnt % self._max_cnt == 0:
            if self.log_fp:
                self.log_fp.close()
            self.log_fp = open(os.path.join(self.file_path, str(cnt)+'.json'), 'w+')
        self.log_fp.write(json.dumps(data) + '\n')
        self.log_fp.flush()

class VideoHandle(FileHandle):
    def __init__(self, path, type):
        FileHandle.__init__(self, path)
        self.video_writer = None
        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.type = type
        self.video_path = os.path.join(self.path, 'video', self.type)
        if not os.path.exists(self.video_path):
            os.makedirs(self.video_path)

    def handler(self, data,frame_id, cnt):
        if cnt % self._max_cnt == 0:
            if self.video_writer:
                self.video_writer.release()
            self.video_writer = cv2.VideoWriter(os.path.join(self.video_path, str(cnt)+'.avi'), self.fourcc, 20.0, (1280, 720), True)
        self.video_writer.write(data)

class Sink(Process):
    def __init__(self, queue, ip, port=1200):
        Process.__init__(self)
        self.deamon = True
        self.ip = ip
        self.port = port
        self.queue = queue
        self.q_max = 20
        self.cur_frame_id = -1

    def _init_socket(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (self.ip, self.port, ))

    def run(self):
        self._init_socket()
        while True:
            # print('sink main run')
            buf = nanomsg.wrapper.nn_recv(self._socket, 0)
            frame_id, data = self.pkg_handler(buf[1])
            #if len(self._data_queue) > 0 and frame_id < self._data_queue[-1][0]:
            #    continue
            self.queue.put((frame_id, data))
            # print('queuesize', self.queue.qsize())
            if self.queue.qsize() > self.q_max:
                self.queue.get()

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

class Hub(Process):
    
    def __init__(self, ip='192.168.0.233'):
        Process.__init__(self)
        self.camera_queue = Queue()
        self.camera_sink = CameraSink(queue=self.camera_queue, ip=ip, port=1200)
        self.camera_sink.start()

        self.lane_queue = Queue()
        self.lane_sink = LaneSink(queue=self.lane_queue, ip=ip, port=1203)
        self.lane_sink.start()

        self.vehicle_queue = Queue()
        self.vehicle_sink = VehicleSink(queue=self.vehicle_queue, ip=ip, port=1204)
        self.vehicle_sink.start()

        self.camera_list = []
        self.lane_list = []
        self.vehicle_list = []

    def __del__(self):
        self.camera_sink.exit = True
        self.lane_sink.exit = True
        self.vehicle_sink.exit = True
    
    @staticmethod
    def pending(queue, list):
        while not len(list):
            if not queue.empty():
                list.append(queue.get())
            time.sleep(0.02)

    @staticmethod
    def waiting(queue, list, frame_id):
        while True:
            if not queue.empty():
                id, data = queue.get()
                if id >= frame_id:
                    list.append((id, data))
                    break
            time.sleep(0.01)
            
    def pop(self):

        ''''
        inc = 5
        while inc:
            if not self.camera_queue.empty():
                self.camera_list.append(self.camera_queue.get())
            if not self.lane_queue.empty():
                self.lane_list.append(self.lane_queue.get())
            if not self.vehicle_queue.empty():
                self.vehicle_list.append(self.vehicle_queue.get())
            inc -= 1
        '''
        self.pending(self.camera_queue, self.camera_list)
        # self.pending(self.vehicle_queue, self.vehicle_list)
        # self.pending(self.lane_queue, self.lane_list)
        frame_id, image_data = self.camera_list.pop(0)
        self.waiting(self.vehicle_queue, self.vehicle_list, frame_id)
        self.waiting(self.lane_queue, self.lane_list, frame_id)

        '''
        self.camera_list.sort(key=lambda log:log[0])
        self.vehicle_list.sort(key=lambda log:log[0])
        self.lane_list.sort(key=lambda log:log[0])
        '''

        res = {
            'frame_id': None,
            'img': None,
            'vehicle_data': {},
            'lane_data': {},
        }

        image = np.fromstring(image_data, dtype=np.uint8).reshape(720, 1280, 1)
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        res['frame_id'] = frame_id
        res['img'] = image

        # print(frame_id, end='')
        while len(self.vehicle_list) and self.vehicle_list[0][0]<=frame_id:
            temp = self.vehicle_list.pop(0)
            if temp[0] == frame_id:
                res['vehicle_data'] = temp[1]
                # print(' vehicle', end='')
        
        while len(self.lane_list) and self.lane_list[0][0]<=frame_id:
            temp = self.lane_list.pop(0)
            if temp[0] == frame_id:
                res['lane_data'] = temp[1]
                # print(' lane', end='')
        # print()
        if not res['lane_data'] and not res['vehicle_data']:
            res['frame_id'] = None
        # print('data show', res['vehicle_data'], res['lane_data'])
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
    def __init__(self, path, ip = "192.168.0.233", save_video=1, save_demo=1):
        self.hub = None
        self.save_video = save_video
        self.save_demo = save_demo
        self.player = Player()
        self.ip = ip
        self.path = path
        self.exit = False
        self.logHandle = LogHandle(self.path, 'log')
        self.logHandle.start()
        if self.save_demo:
            self.demoHandle = LogHandle(self.path, 'demo')
            self.demoHandle.start()

        if self.save_video:
            self.originVideo = VideoHandle(self.path, 'origin')
            self.originVideo.start()

            self.resultVideo = VideoHandle(self.path, 'result')
            self.resultVideo.start()
    
    def start(self):
        self.hub = Hub(self.ip)
        
        bool = 1
        while not self.exit:
            d = self.hub.pop()
            # bool = 1 - bool
            if not d.get('frame_id'):
                continue
            # if bool:
            #    continue
            self.draw(d)

    def draw(self, mess):
        vehicle_data = mess['vehicle_data']
        lane_data = mess['lane_data']
        img = mess['img']
        frame_id = mess['frame_id']
        
        temp_mess = mess
        temp_mess.pop('img')
        self.logHandle.insert((frame_id, temp_mess))
        if self.save_video:
            temp_img = img.copy()
            self.originVideo.insert((frame_id, temp_img))
    
        # print('vehicle', vehicle_data)
        # print('lane', lane_data)

        self.player.show_overlook_background(img)
        self.player.show_parameters_background(img)

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
                hwm = vehicle_data['headway_warning']
                hw_state = vehicle_data['headway_warning']
                hw = '%.2f' % vehicle_data['ttc']
                vb = vehicle_data['bumper_warning']
                vb_state = vehicle_data['bumper_state']
                sg_state = vehicle_data['stop_and_go_state']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                warning_level = vehicle_data['warning_level']
                if ttc == '1000.00':
                    ttc = '-'
        parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
        self.player.show_vehicle_parameters(img, parameters)
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
                if True:
                # if int(lane['label']) in [1, 2] and speed > 30:
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
        parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
        self.player.show_lane_parameters(img, parameters)
        self.player.show_env(img, speed, light_mode, 0)
        alert['lane_warning'] = lane_warning
        alert['speed'] = float('%.2f' % speed)
        
        if self.save_video:
            self.resultVideo.insert((frame_id, img))
        if self.save_demo:
            self.demoHandle.insert((frame_id, alert))
        cv2.imshow('UI', img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            self.exit = True
        elif key == 27:
            cv2.destroyAllWindows()
            self.exit = True

    def test(self, path):
        """用于测试，读取离线数据"""
        fp = open(os.path.join(path, 'log.json'), 'r')
        log_contents = json.load(fp)
        fp.close()
        
        for data in log_contents:
            if not self.exit:
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
                self.draw(data)
            else:
                break
