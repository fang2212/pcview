#.!/usr/bin/python
# -*- coding:utf8 -*-

import os
import sys
import logging
import time
import nanomsg
import msgpack
import json
from datetime import datetime
from multiprocessing import Process, Queue, Value

import asyncio
import websockets
import numpy as np
import cv2

from .draw.base import BaseDraw, CVColor
from .draw.ui_draw import Player
from etc.config import config
from .FileHandler import FileHandler

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')  # logging.basicConfig函数对日志的输出格式及方式做相关配置
''' logging usage
logging.info('this is a loggging info message')
logging.debug('this is a loggging debug message')
logging.warning('this is loggging a warning message')
logging.error('this is an loggging error message')
logging.critical('this is a loggging critical message')
'''

def convert(data):
    '''
    msgpack dict type value convert
    delete b'
    '''
    if isinstance(data, bytes):      return data.decode('ascii')
    if isinstance(data, dict):       return dict(map(convert, data.items()))
    if isinstance(data, tuple):      return tuple(map(convert, data))
    if isinstance(data, list):       return list(map(convert, data))
    if isinstance(data, set):        return set(map(convert, data))
    return data

async def arm_flow(uri, msg_queue, msg_types):

    async with websockets.connect(uri) as websocket:
        msg = {
            'source': 'pcview-client',
            'topic': 'subscribe',
            'data': 'debug.hub.*',
        }
        data = msgpack.packb(msg)
        await websocket.send(data)
        # print('msg', msg_types)

        while True:
            try:
                data = await websocket.recv()
                # print('msg1')
                msg = msgpack.unpackb(data, use_list=False)
                for msg_type in msg_types:
                    topic = msg[b'topic'].decode('ascii')
                    if topic == 'debug.hub.'+msg_type:
                        data = msgpack.unpackb(msg[b'data'], use_list=False)
                        data = convert(data)
                        msg_queue.put((data['frame_id'], data, msg_type))

            except websockets.exceptions.ConnectionClosed as err:
                print('Connection was closed')
                break


def arm_handle(msg_types, msg_queue, ip):
    def msg_run(msg_queue, msg_types, ip):
        uri = 'ws://'+ip+':24012'
        logging.debug('uri {}'.format(uri))
        asyncio.get_event_loop().run_until_complete(
            arm_flow(uri, msg_queue, msg_types))
    msg_process = Process(target=msg_run,
                            args=(msg_queue, msg_types, ip, ))
    msg_process.daemon = True
    msg_process.start()
    return msg_process

class Sink(Process):
    def __init__(self, queue, ip, port, msg_type):
        Process.__init__(self)
        self.deamon = True
        self.ip = ip
        self.port = port
        self.queue = queue
        self.type = msg_type

    def _init_socket(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (self.ip, self.port, ))

    def run(self):
        self._init_socket()
        while True:
            buf = nanomsg.wrapper.nn_recv(self._socket, 0)
            frame_id, data = self.pkg_handler(buf[1])
            self.queue.put((frame_id, data, self.type))

    def pkg_handler(self, msg_buf):
        pass


class CameraSink(Sink):

    def __init__(self, queue, ip, port, msg_type):
        Sink.__init__(self, queue, ip, port, msg_type)

    def pkg_handler(self, msg):
        # print('c--process-id:', os.getpid())
        msg = memoryview(msg).tobytes()
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        data = msg[16:]
        logging.debug('cam id {}'.format(frame_id))
        return frame_id, data

class LaneSink(Sink):
    
    def __init__(self, queue, ip, port, msg_type):
        Sink.__init__(self, queue, ip, port, msg_type)

    def pkg_handler(self, msg): 
        # print('l--process-id:', os.getpid())
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        logging.debug('lan id {}'.format(frame_id))
        return frame_id, res

class VehicleSink(Sink):

    def __init__(self, queue, ip, port, msg_type):
        Sink.__init__(self, queue, ip, port, msg_type)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        logging.debug('veh id {}'.format(frame_id))
        return frame_id, res

class PedSink(Sink):

    def __init__(self, queue, ip, port, msg_type):
        Sink.__init__(self, queue, ip, port, msg_type)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        logging.debug('ped id {}'.format(frame_id))
        return frame_id, res

class TsrSink(Sink):

    def __init__(self, queue, ip, port, msg_type):
        Sink.__init__(self, queue, ip, port, msg_type)

    def pkg_handler(self, msg):
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        logging.debug('tsr id {}'.format(frame_id))
        return frame_id, res

def fpga_handle(msg_types, msg_queue, ip):
    sink = {}
    if 'lane' in msg_types:
        sink['lane'] = LaneSink(queue=msg_queue, ip=ip, port=1203, msg_type='lane')
        sink['lane'].start()

    if 'vehicle' in msg_types:
        sink['vehicle'] = VehicleSink(queue=msg_queue, ip=ip, port=1204, msg_type='vehicle')
        sink['vehicle'].start()
        
    if 'ped' in msg_types:
        sink['ped'] = PedSink(queue=msg_queue, ip=ip, port=1205, msg_type='ped')
        sink['ped'].start()
        
    if 'tsr' in msg_types:
        sink['tsr'] = TsrSink(queue=msg_queue, ip=ip, port=1206, msg_type='tsr')
        sink['tsr'].start()


class Hub(Process):
    
    def __init__(self):

        msg_types = config.msg_types
        image_list_path = config.pic.path 

        Process.__init__(self)
        # self.use_camera = True

        if config.pic.use:
            image_fp = open(image_list_path, 'r+')
            self.image_list = image_fp.readlines()
            image_fp.close()
        
        self.max_cache = len(msg_types)*10

        self.msg_queue = Queue()
        self.cam_queue = Queue()
        self.sink = {}
        self.cache = {}

        self.msg_cnt = {}

        for msg_type in msg_types:
            self.cache[msg_type] = []
            self.msg_cnt[msg_type] = {
                'rev': 0,
                'show': 0,
                'fix': 0,
            } 
        self.msg_cnt['frame'] = 0

        if not config.pic.use:
            self.camera_sink = CameraSink(queue=self.cam_queue, ip=config.ip, port=1200, msg_type='camera')
            self.camera_sink.start()
        
        if config.platform == 'fpga':
            fpga_handle(msg_types, self.msg_queue, config.ip)
        elif config.platform == 'arm':
            logging.debug('arm platform')
            arm_handle(msg_types, self.msg_queue, config.ip)

    def list_len(self):
        length = 0
        for key in self.cache:
            length += len(self.cache[key])
        return length 

    def all_has(self):
        for key in self.cache:
            if not self.cache[key]:
                return False
        return True 

    def all_over(self, frame_id):
        for key in self.cache:
            if not self.cache[key]:
                return False
            if self.cache[key][-1][0] < frame_id:
                return False
        return True 

    def msg_async(self):
        while not self.msg_queue.empty():
            frame_id, msg_data, msg_type = self.msg_queue.get()
            logging.debug('queue id {}, type {}'.format(frame_id, msg_type))
            self.cache[msg_type].append((frame_id, msg_data))
            self.msg_cnt[msg_type]['rev'] += 1
        time.sleep(0.02)

    def pop(self):
        res = {
            'frame_id': None,
            'img': None,
            'vehicle': {},
            'lane': {},
            'ped': {},
            'tsr':{},
            'extra': {}
        }

        frame_id = None

        if config.pic.use:
            while not self.all_has() and self.list_len() < self.max_cache:
                self.msg_async()
            frame_id = sys.maxsize
            for key in self.cache:
                if self.cache[key]:
                    temp_id = self.cache[key][0][0]
                    # logging.debug('temp id {}'.format(temp_id))
                    frame_id = min(temp_id, frame_id)
        
            logging.debug('frame_id {}'.format(frame_id))

            index = ((frame_id//3)*4+frame_id%3) % len(self.image_list)
            image_path = self.image_list[index]
            res['extra'] = {
                'image_path': image_path
            }
            image_path = image_path.strip()
            img = cv2.imread(image_path)
            if config.show.color == 'gray':
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            res['img'] = img
        else:
            while True:
                if not self.cam_queue.empty():
                    frame_id, image_data, msg_type = self.cam_queue.get()
                    image = np.fromstring(image_data, dtype=np.uint8).reshape(720, 1280, 1)
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                    res['img'] = image
                    break
                time.sleep(0.02)
            logging.debug('show cam id {}'.format(frame_id))
            while not self.all_over(frame_id) and self.list_len() < self.max_cache:
                self.msg_async()

        logging.debug('out')
        res['frame_id'] = frame_id
        logging.debug('end0 res')

        for key in self.cache:
            while self.cache[key] and self.cache[key][0][0]<=frame_id:
                if self.cache[key][0][0] == frame_id:
                    res[key] = self.cache[key][0][1]
                    self.msg_cnt[key]['show'] += 1
                    self.cache[key].pop(0)
                    break
                else:
                    self.cache[key].pop(0)
    
        self.msg_cnt['frame'] += 1
        # logging.debug('end res {}'.format(res))
        logging.debug('end res ped{}'.format(res['ped']))
        logging.debug('end res tsr{}'.format(res['tsr']))

        return res         


class PCViewer():
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, hub):
        self.hub = hub
        self.player = Player()
        self.exit = False
        
        self.now_id = 0
        self.pre_lane = {}
        self.pre_vehicle = {}
        self.pre_ped = {}
        self.pre_tsr = {}
        if config.mobile.show:
            mobile_fp = open(config.mobile.path, 'r+')
            self.mobile_content = json.load(mobile_fp)
            mobile_fp.close()
        
        if config.save.log or config.save.alert or config.save.video:
            self.fileHandler = FileHandler()
            self.fileHandler.start()
    
    def start(self):
        self.hub.start()
        self.start_time = datetime.now()
        frame_cnt = 0

        while not self.exit:
            d = self.hub.pop()
            if not d.get('frame_id'):
                continue
            frame_cnt += 1
            self.draw(d, frame_cnt)
            if frame_cnt >= 200:
                self.start_time = datetime.now()
                frame_cnt = 0

    def fix_frame(self, pre_, now_, fix_range):
        if now_.get('frame_id') or (not fix_range):
            return now_, now_
        if pre_.get('frame_id'):
            if pre_.get('frame_id') + fix_range >= self.now_id:
                return pre_, pre_
        return {}, {}

    def draw(self, mess, frame_cnt):
        img = mess['img']
        frame_id = mess['frame_id']
        self.now_id = frame_id
        vehicle_data = mess['vehicle']
        lane_data = mess['lane']
        ped_data = mess['ped']
        tsr_data = mess['tsr']

        self.player.show_overlook_background(img)
        if config.mobile.show:
            bg_width = 120 * 6
        else:
            bg_width = 120 * 4
        self.player.show_parameters_background(img, (0, 0, bg_width+20, 150))
        
        # fix frame
        self.pre_lane, lane_data = self.fix_frame(self.pre_lane, lane_data, config.fix.lane)
        self.pre_vehicle, vehicle_data = self.fix_frame(self.pre_vehicle, vehicle_data, config.fix.vehicle)
        self.pre_ped, ped_data = self.fix_frame(self.pre_ped, ped_data, config.fix.ped)
        self.pre_tsr, tsr_data = self.fix_frame(self.pre_tsr, tsr_data, config.fix.tsr)
        
        if config.show.vehicle:
            if vehicle_data:
                self.hub.msg_cnt['vehicle']['fix'] += 1
            self.draw_vehicle(img, vehicle_data)
        
        if config.show.lane:
            if lane_data:
                self.hub.msg_cnt['lane']['fix'] += 1
            self.draw_lane(img, lane_data)

        if config.show.ped:
            if ped_data:
                self.hub.msg_cnt['ped']['fix'] += 1
            self.draw_ped(img, ped_data)

        if config.show.tsr:
            if tsr_data:
                self.hub.msg_cnt['tsr']['fix'] += 1
            self.draw_tsr(img, tsr_data)
        
        logging.info('msg state {}'.format(self.hub.msg_cnt))

        # show env info
        light_mode = -1
        if vehicle_data:
            light_mode = vehicle_data['light_mode']
        speed = vehicle_data.get('speed') if vehicle_data.get('speed') else 0
        speed = lane_data.get('speed')*3.6 if lane_data.get('speed') else speed

        fps = self.cal_fps(frame_cnt)
        self.player.show_env(img, speed, light_mode, fps, (0, 0))
        
        # save info
        if config.save.alert:
            alert = self.get_alert(vehicle, lane_data, ped_data)
            self.fileHandler.insert_alert((frame_id, {index: alert}))
            self.fileHandler.insert_image((index, img))

        if config.save.video:
            self.fileHandler.insert_video((frame_id, img))
        
        if config.save.log:
            temp_mess = mess
            temp_mess.pop('img')
            self.fileHandler.insert_log((frame_id, temp_mess))
        
        cv2.imshow('UI', img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            self.exit = True
        elif key == 27:
            cv2.destroyAllWindows()
            self.exit = True

    def get_alert(self, vehicle_data, lane_data, ped_data):
        alert = {}
        warning_level, alert_ttc, hw_state, fcw_state, vb_state, sg_state = 0,0,0,0,0,0
        if vehicle_data:
            speed = vehicle_data['speed']
            focus_index = vehicle_data['focus_index']
            if focus_index != -1:
                fcw_state = vehicle_data['forward_collision_warning']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                vb_state = vehicle_data['bumper_state']
                sg_state = vehicle_data['stop_and_go_state']
                alert_ttc = '%.2f' % vehicle_data['ttc']
                warning_level = vehicle_data['warning_level']
                hw_state = vehicle_data['headway_warning']
        alert['ttc'] = float(alert_ttc)
        alert['warning_level'] = int(warning_level)
        alert['hw_state'] = int(hw_state)
        alert['fcw_state'] = int(fcw_state)
        alert['vb_state'] = int(vb_state)
        alert['sg_state'] = int(sg_state)

        lane_warning = 0
        if lane_data: 
            lane_warning = lane_data['deviate_state']
            speed = lane_data['speed']*3.6
        alert['lane_warning'] = lane_warning
        alert['speed'] = float('%.2f' % speed)
       
        return alert

    # vehicle
    def draw_vehicle(self, img, vehicle_data):
        v_type, index, ttc, fcw ,hwm, hw, vb = '-','-','-','-','-','-','-'
        if vehicle_data:
            focus_index = vehicle_data['focus_index']
            speed = vehicle_data['speed'] * 3.6
            for i, vehicle in enumerate(vehicle_data['dets']):
                focus_vehicle = (i == focus_index)
                position = vehicle['bounding_rect']
                position = position['x'], position['y'], position['width'], position['height']
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
                hw = vehicle_data['headway_warning']
                hwm = '%.2f' % vehicle_data['ttc']
                vb = vehicle_data['bumper_warning']
                if ttc == '1000.00':
                    ttc = '-'
        parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
        self.player.show_vehicle_parameters(img, parameters, (120, 0))
                    
    # lane
    def draw_lane(self, img, lane_data):
        lw_dis, rw_dis, ldw, trend = '-', '-', '-', '-'
        if lane_data:
            speed = lane_data['speed'] * 3.6
            for lane in lane_data['lanelines']:
                if int(lane['label']) in [1, 2]:# and speed >= config.show.lane_speed_limit:
                    color = CVColor.Cyan
                    width = lane['width']
                    l_type = lane['type']
                    conf = lane['confidence']
                    index = lane['label']
                    self.player.show_lane(img, lane['perspective_view_poly_coeff'], 
                                          0.2, color)
                    self.player.show_overlook_lane(img, lane['bird_view_poly_coeff'], color)
                    self.player.show_lane_info(img, lane['perspective_view_poly_coeff'],
                                               index, width, l_type, conf, color)

            lw_dis = '%.2f' % (lane_data['left_wheel_dist'])
            rw_dis = '%.2f' % (lane_data['right_wheel_dist'])
            ldw = lane_data['deviate_state']
            trend = lane_data['deviate_trend']
            if lw_dis == '111.00':
                lw_dis = '-'
            if rw_dis == '111.00':
                rw_dis = '-'
            
        parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
        if config.mobile.show:
            lane_y = 120 * 3
        else:
            lane_y = 120 * 2
        self.player.show_lane_parameters(img, parameters, (lane_y, 0))

    # ped
    def draw_ped(self, img, ped_data):
        if ped_data:
            for pedestrain in ped_data['pedestrians']:
                position = pedestrain['regressed_box']
                position = position['x'], position['y'], position['width'], position['height']
                # print('position:', position)
                color = CVColor.Yellow
                if pedestrain['is_key']:
                    color = CVColor.Pink
                if pedestrain['is_danger']:
                    color = CVColor.Pink
                self.player.show_peds(img, position, color, 2)
                if position[0] > 0:
                    self.player.show_peds_info(img, position, pedestrain['dist'])
    
    def draw_tsr(self, img, tsr_data):
        focus_index, speed_limit, tsr_warning_level, tsr_warning_state = -1, 0, 0, 0
        if tsr_data:
            logging.info('tsr data {}'.format(tsr_data))
            focus_index = tsr_data['focus_index']
            speed_limit = tsr_data['speed_limit']
            tsr_warning_level = tsr_data['tsr_warning_level']
            tsr_warning_state = tsr_data['tsr_warning_state']
            for i, tsr in enumerate(tsr_data['dets']):
                position = tsr['position']
                logging.info('tsrrrr {}'.format(position))
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red
                self.player.show_tsr(img, position, color, 2)
                if tsr['max_speed'] != 0:
                    self.player.show_tsr_info(img, position, tsr['max_speed'])                
                
        parameters = [str(focus_index), str(speed_limit), str(tsr_warning_level), str(tsr_warning_state)]
        self.player.show_tsr_parameters(img, parameters, (369, 0))
    
    def cal_fps(self, frame_cnt):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        duration = duration if duration > 0 else 1
        fps = frame_cnt / duration
        return fps

    def draw_mobile(self, img, frame_id):
        index = int(frame_id/3)*4+frame_id%3
        if config.mobile.show:
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
