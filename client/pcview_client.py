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
    from easy_can.base import CanBase, liuqi_p
class CanSink(Process):
    def __init__(self, can_queue):
        Process.__init__(self)
        self.can0 = CanBase()  
        self.can_queue = can_queue  

    def run(self):
        while True:
            for tmp in self.can0.recv():
                #print(tmp)
                tmp = self.can0.parse(tmp, liuqi_p)
                if tmp and tmp.get('can_id') in liuqi_p.keys():
                    self.can_queue.put(tmp)
            time.sleep(0.01) #serialcan 接收不会暂停，主动休眠 10ms

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

    if 'cali' in msg_types:
        sink['cali'] = AlgorithmSink(queue=msg_queue, ip=ip, port=1209, msg_type='cali')
        sink['cali'].start()

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
        self.show_frameid = 0

        self.msg_queue = Queue()    #从nanomsg接收消息
        self.cam_queue = Queue()    #从nanomsg接收图像
        self.res_queue = Queue()    #处理结果，绘图数据队列
        self.file_queue = Queue()   #结果保存到文件日志
        self.can_queue = Queue()    #接收can数据

        self.sink = {}
        self.cache = {}    #算法数据缓存，不同算法数据从不同进程读取，通过cache同步
        
        self.msg_cnt = {}
        self.pre = {}       #上一帧非空的数据

        if config.can.use:
            self.can_cache = {}
            for can_id in liuqi_p.keys():
                self.can_cache[can_id] = []

        if not config.pic.use_local:
            self.cache['cam'] = []  #初始化cache
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
                self.can_sink = CanSink(self.can_queue, self.file_queue) #接收can数据进程
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

    def over_frameid(self): #判断是否接收到完整数据或者缓存超过指定大小
        min_frameid_list = []
        max_frameid_list = []
        for key in self.cache:
            min_frameid = self.cache[key][0][0] if self.cache[key] else sys.maxsize
            min_frameid_list.append(min_frameid)
            max_frameid = self.cache[key][-1][0] if self.cache[key] else 0
            max_frameid_list.append(max_frameid)
        if self.cache['cam']:
            min_min = min(min_frameid_list)
            min_max = min(max_frameid_list)
            max_max = max(max_frameid_list)
            #print(min_min, min_max, max_max, len(self.cache['cam']), self.cache['cam'][0][0])
            if min_max >= self.cache['cam'][0][0] or max_max - min_min >= self.max_cache:
                return True
        return False

    def frame_async(self):  #同步图片及算法数据
        q_size = self.cam_queue.qsize()
        while q_size>0:     #中途push到queue的数据等下一次循环再取，避免数据发送太快导致卡在这里
            q_size -= 1
        #while not self.cam_queue.empty():
            ts, frame_id, image, msg_type = self.cam_queue.get()
            if config.save.log:
                temp = json.dumps({'cam': {
                    'frame_id': frame_id,
                    'recv_ts': ts
                }})
                self.file_queue.put(('log', temp))
            self.cache['cam'].append((frame_id, image, ts))
        time.sleep(0.01)    #延时放在中间，使这一次循环得到的算法帧尽量不要落后于图片
        q_size = self.msg_queue.qsize()
        while q_size>0:
            q_size -= 1
        #while not self.msg_queue.empty():
            ts, frame_id, msg_data, msg_type = self.msg_queue.get()
            msg_data['recv_ts'] = ts
            if config.save.log:
                temp = json.dumps({msg_type: msg_data})
                self.file_queue.put(('log', temp))
            logging.debug('queue id {}, type {}'.format(frame_id, msg_type))
            self.cache[msg_type].append((frame_id, msg_data, ts))

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

    def pop(self, loop_time=None): #生成绘图数据
        res = {
            'frame_id': None,
            'img': None,
            'vehicle': {},
            'lane': {},
            'ped': {},
            'tsr':{},
            'cali':{},
            'can': {},
            'extra': {}
        }

        frame_id = None

        if config.pic.use_local:    #用本地图片
            while (not self.all_has()) and (self.list_len() < self.max_cache):
                self.msg_async()
            frame_id = sys.maxsize

            for key in self.cache:
                if self.cache[key]:
                    temp_id = self.cache[key][0][0]
                    frame_id = min(temp_id, frame_id)
        
            logging.debug('frame_id {}'.format(frame_id))

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
            if config.show.color == 'gray':
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            res['img'] = img
        else:
            '''
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
            '''
            loop = 0
            while not self.over_frameid():
                loop += 1
                if loop_time and loop > loop_time:
                    return None
                self.frame_async()
            frame_id, image, ts = self.cache['cam'].pop(0)
            res['img'] = image
            res['recv_ts'] = ts
            
        res['frame_id'] = frame_id
        
        for key in self.cache:
            while self.cache[key] and self.cache[key][0][0]<=frame_id: #从cache取出当前帧的算法数据，并把落后的帧抛弃掉
                if self.cache[key][0][0] == frame_id:
                    res[key] = self.cache[key][0][1]
                    res['recv_ts'] = min(res['recv_ts'], self.cache[key][0][2]) #时间戳取最早的
                    self.msg_cnt[key]['show'] += 1
                    self.cache[key].pop(0)
                    break
                else:
                    self.cache[key].pop(0)
        self.msg_cnt['frame'] += 1
        
        if config.can.use:
            qsize = self.can_queue.qsize()
            while qsize > 0:
                qsize -= 1
                frdata = self.can_queue.get()
                can_id = frdata['can_id']
                if can_id in liuqi_p.keys():
                    self.can_cache[can_id].append(frdata)
                    if len(self.can_cache[can_id]) > 100:
                        self.can_cache[can_id].pop(0)

            res_can = {}
            for can_id in liuqi_p.keys():
                frdata = self.find_closest_can(self.can_cache[can_id], res['recv_ts']-20) #时间戳往前推20ms
                if frdata:
                    res_can.update(frdata['info'])
                    if config.save.can:
                        temp = json.dumps(frdata)
                        self.file_queue.put('can', temp)
            res['can'] = res_can

        logging.debug('end res ped{}'.format(res['ped']))
        logging.debug('end res tsr{}'.format(res['tsr']))
        self.update_extra(res)
        return res   

    def find_closest_can(self, frdata_list, timestamp):
        ptr = len(frdata_list)
        while ptr > 0:
            ptr -= 1
            if frdata_list[ptr]['recv_ts'] < timestamp:
                return frdata_list[ptr]
        return None
        

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
                img = Player().draw(mess)
                if config.save.video:
                    frame_id = mess['frame_id']
                    self.file_queue.put(('video', (frame_id, img)))
                cv2.imshow('UI', img)
                cv2.waitKey(1)
            time.sleep(0.01)