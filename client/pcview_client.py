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
import numpy as np
import cv2

from .draw.base import BaseDraw, CVColor
#from .draw.ui_draw import Player
from .draw import Player
from etc.config import config

from .file_handler import FileHandler
pack = os.path.join
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')  # logging.basicConfig函数对日志的输出格式及方式做相关配置

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

class Sink(Process):
    def __init__(self, queue, ip, port, msg_type):
        Process.__init__(self)
        self.deamon = True
        self.ip = ip
        self.port = port
        self.queue = queue
        self.msg_type = msg_type

    def _init_socket(self):
        self._socket = nanomsg.wrapper.nn_socket(nanomsg.AF_SP, nanomsg.SUB)
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB, nanomsg.SUB_SUBSCRIBE, "")
        nanomsg.wrapper.nn_connect(self._socket, "tcp://%s:%s" % (self.ip, self.port, ))

    def run(self):
        self._init_socket()
        while True:
            buf = nanomsg.wrapper.nn_recv(self._socket, 0)
            frame_id, data = self.pkg_handler(buf[1])
            self.queue.put((int(time.time()*1000), frame_id, data, self.msg_type))

    def pkg_handler(self, msg_buf):
        pass


if config.can.use:
    from CANAlyst.can_server import TRunner
class CanSink(Process):
    def __init__(self, can_queue):
        Process.__init__(self)
        self.deamon = True
        self.can_runner = TRunner('X1S', 500000, can_queue)

    def run(self):
        self.can_runner.run_test()

class CameraSink(Sink):
    '''
    YUYV = 0
    RGB = 1
    GREY = 2
    '''
    def __init__(self, queue, ip, port, msg_type):
        Sink.__init__(self, queue, ip, port, msg_type)
        self.raw_type = config.pic.raw_type

    def pkg_handler(self, msg):
        # print('c--process-id:', os.getpid())
        msg = memoryview(msg).tobytes()
        frame_id = int.from_bytes(msg[4:8], byteorder="little", signed=False)
        # color_type = int.from_bytes(msg[1:2], byteorder="little", signed=False)
        # color_type = int.from_bytes(msg[2:4], byteorder="little", signed=False)
        # print(msg[0:16])
        if config.pic.raw_type == 'gray':
            data = msg[16:]
            image = np.fromstring(data, dtype=np.uint8).reshape(720, 1280, 1)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if config.pic.raw_type == 'color':
            data = msg[24:]
            image = cv2.imdecode(np.fromstring(data, np.uint8), cv2.IMREAD_COLOR)
        logging.debug('cam id {}'.format(frame_id))
        return frame_id, image

class AlgorithmSink(Sink):
    
    def __init__(self, queue, ip, port, msg_type):
        Sink.__init__(self, queue, ip, port, msg_type)

    def pkg_handler(self, msg): 
        # print('l--process-id:', os.getpid())
        data = msgpack.loads(msg)
        res = convert(data)
        frame_id = res['frame_id']
        return frame_id, res

def fpga_handle(msg_types, msg_queue, ip):
    sink = {}
    if 'lane' in msg_types:
        sink['lane'] = AlgorithmSink(queue=msg_queue, ip=ip, port=1203, msg_type='lane')
        sink['lane'].start()

    if 'vehicle' in msg_types:
        sink['vehicle'] = AlgorithmSink(queue=msg_queue, ip=ip, port=1204, msg_type='vehicle')
        sink['vehicle'].start()
        
    if 'ped' in msg_types:
        sink['ped'] = AlgorithmSink(queue=msg_queue, ip=ip, port=1205, msg_type='ped')
        sink['ped'].start()
        
    if 'tsr' in msg_types:
        sink['tsr'] = AlgorithmSink(queue=msg_queue, ip=ip, port=1206, msg_type='tsr')
        sink['tsr'].start()
    return sink


class PCView():
    
    def __init__(self):

        msg_types = config.msg_types
        image_list_path = config.pic.path 

        if config.pic.use_local:
            image_fp = open(image_list_path, 'r+')
            self.image_list = image_fp.readlines()
            image_fp.close()
            for index, item in enumerate(self.image_list):
                self.image_list[index] = item.strip()
        
        # self.max_cache = len(msg_types)*20
        self.max_cache = config.cache_size

        self.msg_queue = Queue()    #从nanomsg接收消息
        self.cam_queue = Queue()    #从nanomsg接收图像
        self.res_queue = Queue()    #处理结果，绘图数据队列
        self.file_queue = Queue()   #结果保存到文件日志
        self.can_queue = Queue()    #接收can数据

        self.sink = {}
        self.cache = {}    #算法数据缓存，不同算法数据从不同进程读取，通过cache同步
        self.msg_cnt = {}
        self.pre = {}       #上一帧非空的数据

        for msg_type in msg_types:
            self.cache[msg_type] = []
            self.pre[msg_type] = {}
            self.msg_cnt[msg_type] = {
                'rev': 0,
                'show': 0,
                'fix': 0,
            } 
        self.msg_cnt['frame'] = 0
        self.fps_cnt = {
            'start_time': None,
            'inc': 0,
            'value': 20
        }

        if not config.pic.use_local:
            self.camera_sink = CameraSink(queue=self.cam_queue, ip=config.ip, port=1200, msg_type='camera') #从nanomsg接收图像
            self.camera_sink.start()

        
        if config.platform == 'fpga':
            self.sink = fpga_handle(msg_types, self.msg_queue, config.ip) #启动接收nanomsg进程

        self.mobile_content = None
        if config.mobile.show:  #显示mobile数据
            mobile_fp = open(config.mobile.path, 'r+')
            self.mobile_content = json.load(mobile_fp)
            mobile_fp.close()
            self.gen_mobile_dict()

        self.file_handler = None
        if config.save.log or config.save.alert or config.save.video:
            self.file_handler = FileHandler(self.file_queue)    #保存log和video进程
            self.file_handler.start()

        if config.can.use:
            try:
                self.can_sink = CanSink(self.can_queue) #接收can数据进程
                self.can_sink.start()
            except Exception as E:
                print(E)

        self.pc_draw = PCDraw(self.res_queue, self.file_queue) #绘图进程
        self.pc_draw.start()

    def gen_mobile_dict(self):  #读取mobile数据
        temp_dict = {}
        for mobile_log in self.mobile_content:
            temp_dict[mobile_log['image_mark']] = mobile_log
        self.mobile_content = temp_dict

    def list_len(self): #cache缓存数据量
        length = 0
        for key in self.cache:
            length += len(self.cache[key])
        return length 

    def all_has(self):  #每种类型的数据都有
        for key in self.cache:
            if not self.cache[key]:
                return False
        return True 

    def all_over(self, frame_id):  #每种类型的数据都有，并且 达到或者超前 图像帧
        for key in self.cache:
            if not self.cache[key]:
                return False
            if self.cache[key][-1][0] < frame_id:
                return False
        return True 

    def msg_async(self):    #把算法数据从 msg_queue 同步到cache
        while not self.msg_queue.empty():
            ts, frame_id, msg_data, msg_type = self.msg_queue.get()
            msg_data['recv_ts'] = ts
            if config.save.log:
                temp = json.dumps({msg_type: msg_data})
                self.file_queue.put(('log', temp))
            logging.debug('queue id {}, type {}'.format(frame_id, msg_type))
            self.cache[msg_type].append((frame_id, msg_data))
            self.msg_cnt[msg_type]['rev'] += 1
        time.sleep(0.01)

    def go(self): #往绘图数据队列填数据
        while True:
            self.res_queue.put(self.pop())
            time.sleep(0.01)

    def fix_frame(self, pre_, now_, msg_type, now_id):  #如果该帧数据为空，并且上一帧相隔不大，绘制上一帧的数据让图像连续
        fix_range = config.fix[msg_type]
        if now_.get('frame_id') or (not fix_range):
            return now_, now_
        if pre_.get('frame_id'):
            if pre_.get('frame_id') + fix_range >= now_id:
                self.msg_cnt[msg_type]['fix'] += 1
                return pre_, pre_
        return {}, {}

    def update_extra(self, res):    #添加额外数据：计算帧率， mobile数据， 根据上一帧填充空的数据
        self.fps_cnt['inc'] += 1
        fps_period  = 100
        if not self.fps_cnt['start_time']:
            self.fps_cnt['start_time'] = datetime.now()
        if self.fps_cnt['inc'] % fps_period == 0:
            self.fps_cnt['inc'] = 0
            temp = self.fps_cnt['start_time']
            self.fps_cnt['start_time'] = datetime.now()
            delta = (self.fps_cnt['start_time'] - temp).total_seconds()
            self.fps_cnt['value'] = int(fps_period / delta)
        res['extra']['fps'] = self.fps_cnt['value']

        image_mark = res['extra'].get('image_mark')
        if config.mobile.show and image_mark:
            mobile_log = self.mobile_content.get(image_mark)
            res['extra']['mobile_log'] = mobile_log

        # fix frame
        frame_id = res['frame_id']
        img = res['img']
        for msg_type in config.msg_types:
            self.pre[msg_type], res[msg_type] = self.fix_frame(self.pre[msg_type],
                                                               res[msg_type],
                                                               msg_type,
                                                               frame_id)

        logging.info('msg state {}'.format(self.msg_cnt))

    def pop(self): #生成绘图数据
        res = {
            'frame_id': None,
            'img': None,
            'vehicle': {},
            'lane': {},
            'ped': {},
            'tsr':{},
            'can': {},
            'extra': {}
        }

        frame_id = None

        if config.pic.use_local:    #用本地图片
            # print('len', self.list_len())
            while (not self.all_has()) and (self.list_len() < self.max_cache):
                self.msg_async()
            frame_id = sys.maxsize

            for key in self.cache:
                if self.cache[key]:
                    temp_id = self.cache[key][0][0]
                    # logging.debug('temp id {}'.format(temp_id))
                    frame_id = min(temp_id, frame_id)
        
            logging.debug('frame_id {}'.format(frame_id))
            # print("use frame_id", frame_id)

            index = ((frame_id//3)*4+frame_id%3) % len(self.image_list)
            image_path = pack(config.pic.test_image, self.image_list[index].strip())
            items = self.image_list[index].split('/')
            res['extra'] = {
                'image_path': image_path,
                'image_mark': items[0]+'/'+items[-1],
                'image_index': (frame_id//3)*4+frame_id%3
            }
            image_path = image_path.strip()
            img = cv2.imread(image_path)
            # print('image_path', image_path)
            if config.show.color == 'gray':
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            res['img'] = img
        else:
            while True: #等待接收图片
                if not self.cam_queue.empty():
                    ts, frame_id, image, msg_type = self.cam_queue.get()
                    res['img'] = image
                    if config.save.log:
                        temp = json.dumps({'cam': {
                            'frame_id': frame_id,
                            'recv_ts': ts
                        }})
                        self.file_queue.put(('log', temp))
                    break
                time.sleep(0.01)
            logging.debug('show cam id {}'.format(frame_id))
            while not self.all_over(frame_id) and self.list_len() < self.max_cache: #等待接收算法数据
                self.msg_async()

        res['frame_id'] = frame_id

        for key in self.cache:
            while self.cache[key] and self.cache[key][0][0]<=frame_id: #从cache取出当前帧的算法数据，并把落后的帧抛弃掉
                if self.cache[key][0][0] == frame_id:
                    res[key] = self.cache[key][0][1]
                    self.msg_cnt[key]['show'] += 1
                    self.cache[key].pop(0)
                    break
                else:
                    self.cache[key].pop(0)
    
        self.msg_cnt['frame'] += 1
        
        if config.can.use:
            inc = 100
            while not self.can_queue.empty() and inc:   #读取can数据，取最后一个，最多取第100个
                data = self.can_queue.get()
                if config.save.log:
                    temp = json.dumps({'can': data})
                    self.file_queue.put(('log', temp))
                res['can'] = data
                inc -= 1

        logging.debug('end res ped{}'.format(res['ped']))
        logging.debug('end res tsr{}'.format(res['tsr']))
        self.update_extra(res)
        return res         

class ParaList(object):
    def __init__(self, para_type):
        self.type = para_type
        self.para_list = []
    def insert(self, para, value):
        self.para_list.append(str(para) + ': ' + str(value))
    def output(self):
        return self.para_list

class PCDraw(Process):
    """pc-viewer功能类，用于接收每一帧数据，并绘制
    """
    
    def __init__(self, mess_queue, file_queue):
        Process.__init__(self)
        self.daemon = True
        self.mess_queue = mess_queue
        self.player = Player()
        self.file_queue = file_queue

    def run(self):
        while True:
            while not self.mess_queue.empty():
                mess = self.mess_queue.get()
                img = Player(mess).draw()
                if config.save.video:
                    frame_id = mess['frame_id']
                    self.file_queue.put(('video', (frame_id, img)))
                cv2.imshow('UI', img)
                cv2.waitKey(1)
            time.sleep(0.01)

    def run1(self):
        while True: 
            while not self.mess_queue.empty():
                # print('e qsize', self.mess_queue.qsize())
                d = self.mess_queue.get()
                # print('mess_queue', d )
                self.draw(d)
            time.sleep(0.01)

    def draw(self, mess):
        img = mess['img']
        frame_id = mess['frame_id']
        vehicle_data = mess['vehicle']
        lane_data = mess['lane']
        ped_data = mess['ped']
        tsr_data = mess['tsr']
        can_data = mess.get('can')
        extra = mess['extra']
        mobile_log = extra.get('mobile_log')

        if config.show.overlook:
            self.player.show_overlook_background(img)

        if config.mobile.show:
            bg_width = 120 * 6
        elif len(config.msg_types) == 1: 
            bg_width = 120 * len(config.msg_types) + 300
        else:
            bg_width = 120 * len(config.msg_types) + 50
        if config.show_parameters:
            self.player.show_parameters_background(img, (0, 0, bg_width+20, 150))
        
        if config.show.vehicle:
            self.draw_vehicle(img, vehicle_data)
        
        if config.show.lane:
            self.draw_lane(img, lane_data)

        if config.show.ped:
            self.draw_ped(img, ped_data)

        if config.show.tsr:
            self.draw_tsr(img, tsr_data)

        if config.mobile.show:
            self.draw_mobile(img, mobile_log)
        
        # show env info
        light_mode = '-'
        if vehicle_data:
            light_mode = vehicle_data['light_mode']
        speed = vehicle_data.get('speed')*3.6 if vehicle_data.get('speed') else 0
        if not speed:
            speed = lane_data.get('speed') if lane_data.get('speed') else speed
        fps = extra.get('fps')
        if not fps:
            fps = 0
        if config.show_parameters:
            para_list = ParaList('env')
            para_list.insert('speed', int(speed))
            para_list.insert('light', light_mode)
            para_list.insert('fps', fps)
            para_list.insert('fid', frame_id)
            # self.player.show_env(img, speed, light_mode, fps, (0, 0))
            self.player.show_normal_parameters(img, para_list, (2, 0))

        if config.can.use and can_data:
            self.player.show_byd_can(img, can_data, lane_data)

        if config.debug:
            cv2.putText(img, str(extra.get('image_path')), (20, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        if config.save.video:
            self.file_queue.put(('video', (frame_id, img)))

        cv2.imshow('UI', img)
        cv2.waitKey(1)
        return

    # vehicle
    def draw_vehicle(self, img, vehicle_data):
        v_type, index, ttc, fcw ,hwm, hw, vb = '-','-','-','-','-','-','-'
        if vehicle_data:
            focus_index = vehicle_data['focus_index']
            for i, vehicle in enumerate(vehicle_data['dets']):
                focus_vehicle = (i == focus_index)
                position = vehicle['bounding_rect']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red if focus_index == i else CVColor.Cyan
                self.player.show_vehicle(img, position, color, 2)
                
                self.player.show_vehicle_info(img, position,
                                        vehicle['vertical_dist'],vehicle['horizontal_dist'], 
                                        vehicle['vehicle_width'], str(vehicle['type']))
                if config.show.overlook:
                    self.player.show_overlook_vehicle(img, focus_vehicle,
                                                vehicle['vertical_dist'],
                                                vehicle['horizontal_dist'])
                
            if focus_index != -1:
                vehicle = vehicle_data['dets'][focus_index]
                # v_type = vehicle['type']
                # index = vehicle['index']
                ttc = '%.2f' % vehicle['rel_ttc']
                fcw = vehicle_data['forward_collision_warning']
                hw = vehicle_data['headway_warning']
                hwm = '%.2f' % vehicle_data['ttc']
                vb = vehicle_data['bumper_warning']
                if ttc == '1000.00':
                    ttc = '-'
        
        if config.show_parameters:
            para_list = ParaList('vehicle')
            #para_list.insert('ttc', ttc)
            para_list.insert('fcw', fcw)
            para_list.insert('hwm', hwm)
            para_list.insert('hw', hw)
            para_list.insert('vb', vb)
            self.player.show_normal_parameters(img, para_list, (100, 0))
        '''
        parameters = [str(v_type), str(index), str(ttc), str(fcw), str(hwm), str(hw), str(vb)]
        self.player.show_vehicle_parameters(img, parameters, (100, 0))
        '''
 
    # lane
    def draw_lane(self, img, lane_data):
        lw_dis, rw_dis, ldw, trend = '-', '-', '-', '-'
        if lane_data:
            speed = lane_data['speed']
            deviate_state = lane_data['deviate_state']
            for lane in lane_data['lanelines']:
                if ((int(lane['label']) in [1, 2]) or config.show.all_laneline)and speed >= config.show.lane_speed_limit:
                    # color = CVColor.Cyan
                    color = CVColor.Blue
                    width = lane['width']
                    l_type = lane['type']
                    conf = lane['confidence']
                    index = lane['label']
                    if config.show.lane_begin == -1:
                        begin = int(lane['end'][1])
                    else:
                        begin = config.show.lane_begin
                    if config.show.lane_end == -1:
                        end = int(lane['start'][1])
                    else:
                        end = config.show.lane_end
                    #print('label', index, deviate_state)
                    if int(index) == int(deviate_state):
                        color = CVColor.Red
                    #self.player.show_lane(img, lane['perspective_view_poly_coeff'], 
                    #                      0.2, color, config.show.lane_begin, config.show.lane_end)
                    self.player.show_lane(img, lane['perspective_view_poly_coeff'], 
                                          0.2, color, begin, end) 
                    if config.show.overlook:
                        self.player.show_overlook_lane(img, lane['bird_view_poly_coeff'], color)
                    #self.player.show_lane_info(img, lane['perspective_view_poly_coeff'],
                    #                           index, width, l_type, conf, color)

            lw_dis = '%.2f' % (lane_data['left_wheel_dist'])
            rw_dis = '%.2f' % (lane_data['right_wheel_dist'])
            ldw = lane_data['deviate_state']
            trend = lane_data['deviate_trend']
            if lw_dis == '111.00':
                lw_dis = '-'
            if rw_dis == '111.00':
                rw_dis = '-'

        if config.show_parameters:
            para_list = ParaList('lane')
            para_list.insert('lw_dis', lw_dis)
            para_list.insert('rw_dis', rw_dis)
            para_list.insert('ldw', ldw)
            #para_list.insert('trend', trend)
            self.player.show_normal_parameters(img, para_list, (192, 0))
        '''
        parameters = [str(lw_dis), str(rw_dis), str(ldw), str(trend)]
        self.player.show_lane_parameters(img, parameters, (200, 0))
        '''

    # ped
    def draw_ped(self, img, ped_data):
        pcw_on, ped_on = '-', '-'
        if ped_data:
            if ped_data.get('pcw_on'):
                pcw_on = 1
            if ped_data.get('ped_on'):
                ped_on = 1
            for pedestrain in ped_data['pedestrians']:
                position = pedestrain['regressed_box']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Yellow
                if pedestrain['is_key']:
                    color = CVColor.Pink
                if pedestrain['is_danger']:
                    color = CVColor.Pink
                self.player.show_peds(img, position, color, 2)
                if position[0] > 0:
                    self.player.show_peds_info(img, position, pedestrain['dist'])
        if config.show_parameters:
            para_list = ParaList('ped')
            para_list.insert('pcw_on', pcw_on)
            #para_list.insert('ped_on', ped_on)
            self.player.show_normal_parameters(img, para_list, (430, 0))
    
    def draw_tsr(self, img, tsr_data):
        focus_index, speed_limit, tsr_warning_level, tsr_warning_state = -1, 0, 0, 0
        if tsr_data:
            focus_index = tsr_data['focus_index']
            speed_limit = tsr_data['speed_limit']
            tsr_warning_level = tsr_data['tsr_warning_level']
            tsr_warning_state = tsr_data['tsr_warning_state']
            for i, tsr in enumerate(tsr_data['dets']):
                position = tsr['position']
                position = position['x'], position['y'], position['width'], position['height']
                color = CVColor.Red
                self.player.show_tsr(img, position, color, 2)
                if tsr['max_speed'] != 0:
                    self.player.show_tsr_info(img, position, tsr['max_speed'])                

        if config.show_parameters:
            para_list = ParaList('tsr')
            para_list.insert('speed_limit', speed_limit)
            self.player.show_normal_parameters(img, para_list, (305, 0))
        # parameters = [str(focus_index), str(speed_limit), str(tsr_warning_level), str(tsr_warning_state)]
        # self.player.show_tsr_parameters(img, parameters, (300, 0))
    

    def draw_mobile(self, img, mobile_log):
        # mobile_log = None
        if mobile_log:
            mobile_ldw, mobile_hw, mobile_fcw, mobile_vb, mobile_hwm = '-', '-', '-', '-', '-'
            mobile_hwm = mobile_log.get('headway_measurement') if mobile_log.get('headway_measurement') else 0
            mobile_hw = 1 if mobile_log.get('sound_type') == 3 else 0
            mobile_fcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('fcw_on') == 1 else 0
            mobile_pcw = 1 if mobile_log.get('sound_type') == 6 and mobile_log.get('peds_fcw') == 1 else 0
            mobile_vb = 1 if mobile_log.get('sound_type') == 5 else 0
            mobile_ldw = mobile_log['left_ldw'] * 2 + mobile_log['right_ldw'] if 'left_ldw' in mobile_log else 0
            if config.show_parameters:
                para_list = ParaList('mobile')
                para_list.insert('hwm', mobile_hwm)
                para_list.insert('hw', mobile_hw)
                para_list.insert('fcw', mobile_fcw)
                para_list.insert('vb', mobile_vb)
                para_list.insert('ldw', mobile_ldw)
                para_list.insert('pcw', mobile_pcw)
                self.player.show_normal_parameters(img, para_list, (300, 0))
            '''
            mobile_parameters = [str(mobile_hwm), str(mobile_hw), str(mobile_fcw), str(mobile_vb), str(mobile_ldw), str(mobile_pcw)]
            self.player.show_mobile_parameters(img, mobile_parameters, (600, 0))
            '''
