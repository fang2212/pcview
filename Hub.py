#!/usr/bin/python
# -*- coding -*-

import sys
from ../etc/config import config
from multiprocessing import Queue()

async def hello(uri, msg_queue):
    def pkg_vehicle(data):
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
        return res

    def pkg_lane(data):
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
        return res

    def pkg_ped(data):
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
        return res

    async with websockets.connect(uri) as websocket:
        msg = {
            'source': 'pcview-client',
            'topic': 'subscribe',
            'data': 'debug.hub.*',
        }
        data = msgpack.packb(msg)
        await websocket.send(data)

        while True:
            try:
                data = await websocket.recv()
                msg = msgpack.unpackb(data, use_list=False)
                if msg[b'topic'] == b'debug.hub.ped':
                    data = msgpack.unpackb(msg[b'data'], use_list=False)
                    # print('ped', pkg_ped(data))
                    msg_queue.put(('ped', pkg_ped(data)))
                if msg[b'topic'] == b'debug.hub.lane':
                    data = msgpack.unpackb(msg[b'data'], use_list=False)
                    # print('lane', pkg_lane(data))
                    msg_queue.put(('lane', pkg_lane(data)))
                if msg[b'topic'] == b'debug.hub.vehicle':
                    data = msgpack.unpackb(msg[b'data'], use_list=False)
                    # print('vehicle', pkg_vehicle(data))
                    msg_queue.put(('vehicle', pkg_vehicle(data)))

            except websockets.exceptions.ConnectionClosed as err:
                print('Connection was closed')
                break

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
        nanomsg.wrapper.nn_setsockopt(self._socket, nanomsg.SUB,
                nanomsg.SUB_SUBSCRIBE, "")
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

class Hub():

    def __init__(self):
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
        
        if config.fpga:
            self.lane_sink = LaneSink(queue=self.msg_queue, ip=ip, port=1203)
            self.lane_sink.start()

            self.vehicle_sink = VehicleSink(queue=self.msg_queue, ip=ip, port=1204)
            self.vehicle_sink.start()

            self.pedes_sink = PedesSink(queue=self.msg_queue, ip=ip, port=1205)
            self.pedes_sink.start()
        else: 
            msg_process = Process(target=self.msg_run,
                                  args=(self.msg_queue,))
            msg_process.daemon = True
            msg_process.start()

    @staticmethod
    def msg_run(msg_queue):
        asyncio.get_event_loop().run_until_complete(
                hello('ws://192.168.1.201:24012', msg_queue))

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
