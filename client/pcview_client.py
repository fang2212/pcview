#!/usr/bin/python
# -*- coding:utf8 -*-


import threading
import nanomsg
import msgpack
import json
from datetime import datetime
from multiprocessing import Process
from multiprocessing import Queue
from .draw.base import BaseDraw
from .draw.base import CVColor
import os

class Sink(threading.Thread):

    def __init__(self, ip, port=1200):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self._init_socket()
        self.cur_frame_id = -1
        self._data_queue = []
        self._cv = threading.Condition()

    def _init_socket(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (self.ip, self.port, ))

    def run(self):
        while True:
            buf = nanomsg.wrapper.nn_recv(self._socket, 0)
            frame_id, data = self.pkg_handler(buf[1])
            #if len(self._data_queue) > 0 and frame_id < self._data_queue[-1][0]:
            #    continue
            self._data_queue.append((frame_id, data, ))
            with self._cv:
                self._cv.notify()

    def pkg_handler(self, msg_buf):
        pass

    def set_frame_id(self, frame_id):
        # This method must be called
        self.cur_frame_id = frame_id

    def deq(self, block=False):
        if block:
            with self._cv:
                while len(self._data_queue) <= 0:
                    self._cv.wait()
                frame_id, data = self._data_queue.pop(0)
                return frame_id, data
        if len(self._data_queue) <= 0:
            return -1, None
        frame_id, data = self._data_queue.pop(0)
        return frame_id, data


class CameraSink(Sink):

    def __init__(self, ip, port=1200):
        Sink.__init__(self, ip, port)

    def pkg_handler(self, msg):
        msg = memoryview(msg).tobytes()
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        data = msg[16:]
        return frame_id, data


class LaneSink(Sink):

    def __init__(self, ip, port=1203):
        Sink.__init__(self, ip, port)

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
        return frame_id, res


class VehicleSink(Sink):

    def __init__(self, ip, port=1204):
        Sink.__init__(self, ip, port)

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
        return frame_id, res


class Hub(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._sinks = []
        self.elms = []
        self._flag_start = False
        self._cur_frame_id = []
        self._num_sink = -1
        self._init_frame_done = False
        self._cv = threading.Condition()

    def add_sink(self, sink):
        if not self._flag_start:
            self._sinks.append(sink)

    def _add_sink_done(self):
        self._flag_start = True
        self._cur_frame_id = [-1] * len(self._sinks)
        self._num_sink = len(self._sinks)

    def check_ready(self):
        if len(self.elms) <= 0:
            return False
        for fid in self._cur_frame_id:
            if fid == -1 or fid < self.elms[0][0]:
                return False
        return True

    def start_main_loop(self):
        self._add_sink_done()
        self.start()

    def run(self):
        while True:
            self.init_frame()
            self.run_frame()

    def init_frame(self):
        if self._init_frame_done:
            return
        self._init_frame_done = True

        for i, fid in enumerate(self._cur_frame_id):
            frame_id, data = -1, None
            if fid == -1:
                frame_id, data = self._sinks[i].deq(block=True)

            self._cur_frame_id[i] = frame_id

            ind = -1
            for j, elm in enumerate(self.elms):
                if frame_id <= elm[0]:
                    ind = j
                    break

            if ind == -1:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                self.elms.append(elm)
                continue

            if frame_id == self.elms[j][0]:
                self.elms[j][i + 1] = data
            else:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                self.elms.insert(j, elm)

    def run_frame(self):
        for i, sink in enumerate(self._sinks):
            frame_id, data = sink.deq()
            if frame_id < 0:
                return
            self._cur_frame_id[i] = frame_id

            ind = -1
            for j, elm in enumerate(self.elms):
                if frame_id <= elm[0]:
                    ind = j
                    break

            if ind == -1:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                if len(self.elms) > 20:
                    self.elms.pop(0)
                if len(elm[1])>0:
                    # print('----len:', len(elm[1])) 
                    self.elms.append(elm)
                continue

            if frame_id == self.elms[j][0]:
                self.elms[j][i + 1] = data
            else:
                elm = [frame_id] + [[]] * 3
                elm[i + 1] = data
                self.elms.insert(j, elm)

        if self.check_ready():
            with self._cv:
                self._cv.notify()

    def deq(self):
        # Should be a blocking method
        if len(self.elms) <= 0 or not self.check_ready():
            with self._cv:
                self._cv.wait()
        # print('elms size', len(self.elms))
        elm = self.elms.pop(0)
        while len(elm[1])<=0: # 取出image_data不为空的elm
            elm = self.elms.pop(0)
        return {"frame_id": elm[0], "data": elm[1:]}


class WorkHub(Hub):
    def __init__(self, ip):
        Hub.__init__(self)
        camera_sink = CameraSink(ip, 1200)
        lane_sink = LaneSink(ip, 1203)
        vehicle_sink = VehicleSink(ip, 1204)
        self.add_sink(camera_sink)
        self.add_sink(lane_sink)
        self.add_sink(vehicle_sink)
        camera_sink.start()
        lane_sink.start()
        vehicle_sink.start()
        self.start_main_loop()

import numpy as np
import cv2
from .draw.ui_draw import Player
class PCViewer():
    """pc-viewer功能类，用于接收每一帧数据，并绘制

    Attributes:
       ip: 数据源设备的ip地址
       save_origin_image: 是否保存原始图片
       save_result_image: 是否保存处理图片
       queue: 存储每一帧数据
       player: 图片播放器
    """
    def __init__(self, save_path, ip = "192.168.1.251", save_origin_image = 0, save_result_image = 0):
        self.hub = None
        self.queue = Queue(5)
        self.save_origin_image = save_origin_image
        self.save_result_image = save_result_image
        self.player = Player()
        self.ip = ip

        FORMAT = '%Y%m%d%H%M'
        date = datetime.now().strftime(FORMAT)
        self.date_dir = os.path.join(save_path, date)
        if not os.path.exists(self.date_dir):
            os.makedirs(self.date_dir)
        self.log_fp = open(os.path.join(self.date_dir, 'log.json'), 'w+')

    def __del__(self):
        self.log_fp.seek(0, 0)
        self.log_fp.write('[')
        self.log_fp.seek(0, 2)
        self.log_fp.write(']')
        self.log_fp.close()

    def start(self):
        """不断接收帧数据，并将数据放进queue中。"""
        self.hub = WorkHub(self.ip)
        draw_process = Process(target=self.draw)
        draw_process.daemon = True
        draw_process.start()
        while True:
            d = self.hub.deq()
            image_data = d["data"][0]
            lane_data = d["data"][1]
            vehicle_data = d["data"][2]
            if len(image_data) <= 0:
                continue
            #if len(vehicle_data) <= 0:
            #    continue

            image = np.fromstring(image_data, dtype=np.uint8).reshape(720, 1280, 1)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            # print('size:', self.queue.qsize())
            #if self.queue.qsize() > 15:
            #    self.queue.get()
            self.queue.put({
            'frame_id': d['frame_id'],
            'img': image,
            'lane_data': lane_data,
            'vehicle_data': vehicle_data})

    def draw(self):
        """从queue取出帧数据，并绘制。"""
        if self.save_origin_image:
            origin_path = os.path.join(self.date_dir,'origin')
            if not os.path.exists(origin_path):
                os.makedirs(origin_path)
        if self.save_result_image:
            result_path = os.path.join(self.date_dir,'result')
            if not os.path.exists(result_path):
                os.makedirs(result_path)

        def write_log_to_file():
            global timer
            timer = threading.Timer(5, write_log_to_file)
            timer.start()

        timer = threading.Timer(5, write_log_to_file)
        timer.start()
        start_time = datetime.now()
        frame_cnt = 0
        while True:
            mess = None
            while not self.queue.empty():
                mess = self.queue.get()
            if not mess:
                continue
            
            frame_cnt += 1
            end_time = datetime.now()
            duration = (end_time - start_time).seconds
            duration = duration if duration > 0 else 1
            fps = frame_cnt / duration
            
            log = {'frame_id': mess['frame_id'],
                   'lane_data': mess['lane_data'],
                   'vehicle_data': mess['vehicle_data']
                  }
            log_str = ',' + json.dumps(log)
            self.log_fp.write(log_str)

            img = mess['img']
            
            if self.save_origin_image:
                # print("---qszie:", self.queue.qsize())
                if self.queue.qsize()<3:
                    cv2.imwrite(os.path.join(origin_path, str(mess['frame_id']) + '.jpg'), img)

            vehicle_data = mess['vehicle_data']
            lane_data = mess['lane_data']
            self.player.show_overlook_background(img)
            self.player.show_parameters_background(img)
            speed = 0
            light_mode = -1

            # vehicle
            type, index, ttc, fcw ,hwm, hw, vb = '','','','','','',''
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
                    type = str(vehicle['type'])
                    index = str(vehicle['index'])
                    ttc = str('%.2f' % vehicle['rel_ttc'])
                    fcw = str(vehicle_data['forward_collision_warning'])
                    hwm = str(vehicle_data['headway_warning'])
                    hw = str('%.2f' % vehicle_data['ttc'])
                    vb = str(vehicle_data['bumper_warning'])
            parameters = [type, index, ttc, fcw, hwm, hw, vb]
            self.player.show_vehicle_parameters(img, parameters)
                        
            # lane
            lw_dis, rw_dis, ldw, trend = '', '', '', ''
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
                        type = lane['type']
                        conf = lane['confidence']
                        index = lane['label']
                        self.player.show_lane(img, lane['perspective_view_poly_coeff'], width, color)
                        self.player.show_overlook_lane(img, lane['bird_view_poly_coeff'], color)
                        self.player.show_lane_info(img, lane['perspective_view_poly_coeff'], index, width, type, conf, color)

                lw_dis = str('%.2f' % (lane_data['left_wheel_dist']))
                rw_dis = str('%.2f' % (lane_data['right_wheel_dist']))
                ldw = str(lane_data['deviate_state'])
                trend = str(lane_data['deviate_trend'])
            parameters = [lw_dis, rw_dis, ldw, trend]
            self.player.show_lane_parameters(img, parameters)
            
            self.player.show_env(img, speed, light_mode, fps)
            if self.save_result_image:
                if self.queue.qsize()<3:
                    cv2.imwrite(os.path.join(result_path, str(mess['frame_id']) + '.jpg'), img)
            
            cv2.imshow('2333', img)
                
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q'):
                cv2.destroyAllWindows()
        

    def test(self):
        """用于测试，读取离线数据"""
        fp = open('/home/tester/Documents/pc-viewer-data/201805212004/log.json', 'r')
        log_contents = json.load(fp)
        fp.close()
        
        draw_process = Process(target=self.draw)
        draw_process.daemon = True
        draw_process.start()
        
        for data in log_contents:
            img = cv2.imread('/home/tester/minieye/pc-viewer/pc-viewer-data/socket/out/'+str(data['frame_id']) + '.jpg')
            while self.queue.qsize() > 5:
                self.queue.get()
            self.queue.put({
                'frame_id': data['frame_id'],
                'img': img,
                'lane_data': data['lane_data'],
                'vehicle_data': data['vehicle_data']})            


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="ip address",
                        type=str)
    parser.add_argument("--origin", help="save origin images",
                        type=str)
    parser.add_argument("--result", help="save result images",
                        type=str)
    parser.add_argument("--path", help="the save path of images",
                        type=str)
    args = parser.parse_args()
    PCViewer(args.ip, args.origin, args.result, args.path).draw()
